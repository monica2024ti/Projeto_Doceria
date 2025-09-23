import streamlit as st
from datetime import date
import pandas as pd

import db
from auth import verify_password


def set_page_config():
	st.set_page_config(
		page_title="Encomendas de Bolos",
		page_icon="🎂",
		layout="wide",
		initial_sidebar_state="expanded",
	)


def inject_css():
	try:
		with open("assets/styles.css", "r", encoding="utf-8") as f:
			st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
	except FileNotFoundError:
		pass


def ensure_session_state():
	if "auth" not in st.session_state:
		st.session_state.auth = {
			"is_authenticated": False,
			"user_id": None,
			"username": None,
			"is_superuser": False,
			"bakery_name": None,
		}


def login_form():
	st.markdown("## Entrar")
	with st.form("login_form", clear_on_submit=False):
		username = st.text_input("Usuário", key="login_user")
		password = st.text_input("Senha", type="password", key="login_pass")
		submitted = st.form_submit_button("Entrar")
		if submitted:
			user = db.get_user_by_username(username)
			if user and verify_password(password, user["password_hash"]):
				st.session_state.auth = {
					"is_authenticated": True,
					"user_id": user["id"],
					"username": user["username"],
					"is_superuser": bool(user["is_superuser"]),
					"bakery_name": user["bakery_name"],
				}
				st.success("Login realizado!")
				st.rerun()
			else:
				st.error("Usuário ou senha inválidos.")


def logout_button():
	if st.sidebar.button("Sair", use_container_width=True):
		st.session_state.auth = {
			"is_authenticated": False,
			"user_id": None,
			"username": None,
			"is_superuser": False,
			"bakery_name": None,
		}
		st.rerun()


def render_header():
	a = st.session_state.auth
	left, right = st.columns([0.7, 0.3])
	with left:
		st.markdown("### 🎂 Sistema de Encomendas de Bolos")
		if a["bakery_name"]:
			st.caption(f"Doceria: {a['bakery_name']}")
	with right:
		st.write("")
		st.write("")
		st.metric("Usuário", a["username"])  # simples indicativo


def dashboard():
	a = st.session_state.auth
	counts = db.stats_counts(a["user_id"]) if a["user_id"] else {"Pendente": 0, "Pago (Em preparação)": 0, "Entregue": 0}
	st.markdown("## Visão Geral")

	c1, c2, c3 = st.columns(3)
	with c1:
		st.metric("Pendente", counts.get("Pendente", 0))
	with c2:
		st.metric("Pago (Em preparação)", counts.get("Pago (Em preparação)", 0))
	with c3:
		st.metric("Entregue", counts.get("Entregue", 0))

	st.markdown("---")

	# Destaques com ações rápidas
	st.markdown("### Destaques de Hoje e Próximos Dias")
	orders = db.list_orders(a["user_id"]) if a["user_id"] else []

	pendentes = [o for o in orders if o["status"] == "Pendente"]
	preparando = [o for o in orders if o["status"].startswith("Pago")]

	col1, col2 = st.columns(2)
	with col1:
		st.markdown("#### Pendentes")
		if pendentes:
			for o in pendentes:
				row = st.columns([0.28, 0.18, 0.18, 0.18, 0.18])
				with row[0]:
					st.write(f"{o['client_name']} — {o['flavor']}")
				with row[1]:
					st.caption(f"Tamanho: {o['size'] or '-'}")
				with row[2]:
					st.caption(f"Entrega: {o['due_date']}")
				with row[3]:
					st.caption(f"Preço: R$ {o['price'] if o['price'] is not None else '-'}")
				with row[4]:
					if st.button("Marcar: Em preparação", key=f"mark_prep_{o['id']}"):
						db.update_order_status(a["user_id"], o["id"], "Pago (Em preparação)")
						st.success("Atualizado para Em preparação.")
						st.rerun()
				st.divider()
		else:
			st.info("Sem pedidos pendentes.")

	with col2:
		st.markdown("#### Em preparação (Pago)")
		if preparando:
			for o in preparando:
				row = st.columns([0.28, 0.18, 0.18, 0.18, 0.18])
				with row[0]:
					st.write(f"{o['client_name']} — {o['flavor']}")
				with row[1]:
					st.caption(f"Tamanho: {o['size'] or '-'}")
				with row[2]:
					st.caption(f"Entrega: {o['due_date']}")
				with row[3]:
					st.caption(f"Preço: R$ {o['price'] if o['price'] is not None else '-'}")
				with row[4]:
					if st.button("Marcar: Entregue", key=f"mark_done_{o['id']}"):
						db.update_order_status(a["user_id"], o["id"], "Entregue")
						st.success("Atualizado para Entregue.")
						st.rerun()
				st.divider()
		else:
			st.info("Sem pedidos em preparação.")


def sidebar_nav():
	a = st.session_state.auth
	st.sidebar.markdown("## Navegação")
	st.sidebar.page_link("app.py", label="Home", icon="🏠")
	st.sidebar.page_link("pages/1_Clientes.py", label="Clientes", icon="👥")
	st.sidebar.page_link("pages/2_Encomendas.py", label="Encomendas", icon="🧾")
	if a["is_superuser"]:
		st.sidebar.page_link("pages/3_Admin.py", label="Admin", icon="⚙️")
	logout_button()


def main():
	set_page_config()
	inject_css()
	ensure_session_state()

	db.init_db()

	a = st.session_state.auth

	if not a["is_authenticated"]:
		st.markdown("## Bem-vindo(a) 👋")
		st.write("Organize seus pedidos de bolos com praticidade.")
		login_form()
		return

	# Logado
	sidebar_nav()
	render_header()
	dashboard()


if __name__ == "__main__":
	main()

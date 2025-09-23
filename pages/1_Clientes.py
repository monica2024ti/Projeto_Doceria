import streamlit as st
import db


def ensure_auth():
	if "auth" not in st.session_state or not st.session_state.auth.get("is_authenticated"):
		st.warning("Faça login para acessar esta página.")
		st.stop()


def main():
	st.set_page_config(page_title="Clientes | Encomendas de Bolos", page_icon="👥", layout="wide")
	ensure_auth()
	a = st.session_state.auth

	st.markdown("## Clientes")

	with st.expander("Adicionar cliente", expanded=True):
		with st.form("add_client_form"):
			name = st.text_input("Nome do cliente")
			phone = st.text_input("Telefone")
			notes = st.text_area("Observações")
			sub = st.form_submit_button("Salvar")
			if sub:
				if not name.strip():
					st.error("Nome é obrigatório.")
				else:
					db.create_client(a["user_id"], name.strip(), phone.strip() if phone else None, notes.strip() if notes else None)
					st.success("Cliente cadastrado!")
					st.rerun()

	st.markdown("---")

	clients = db.list_clients(a["user_id"]) or []
	if not clients:
		st.info("Nenhum cliente cadastrado.")
		return

	for c in clients:
		with st.expander(f"👤 {c['name']}"):
			col1, col2 = st.columns([0.5, 0.5])
			with col1:
				st.markdown("**Telefone**")
				st.write(c["phone"] or "-")
			with col2:
				st.markdown("**Observações**")
				st.write(c["notes"] or "-")

			st.markdown("---")
			st.markdown("**Encomendas deste cliente**")
			orders = db.list_orders_by_client(a["user_id"], c["id"]) or []
			if not orders:
				st.caption("Sem encomendas.")
			else:
				for o in orders:
					cols = st.columns([0.25, 0.25, 0.2, 0.15, 0.15])
					with cols[0]:
						st.write(f"Sabor: {o['flavor']}")
					with cols[1]:
						st.caption(f"Tamanho: {o['size'] or '-'}")
					with cols[2]:
						st.caption(f"Entrega: {o['due_date']}")
					with cols[3]:
						st.caption(f"Preço: R$ {o['price'] if o['price'] is not None else '-'}")
					with cols[4]:
						st.caption(f"Status: {o['status']}")

			st.markdown("---")
			if st.button("Remover cliente", key=f"del_{c['id']}"):
				db.delete_client(a["user_id"], c["id"])
				st.success("Cliente removido.")
				st.rerun()


if __name__ == "__main__":
	main()

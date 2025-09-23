import os
import sqlite3
from typing import List, Optional, Dict
from datetime import datetime

DB_DIR = os.path.join("data")
DB_PATH = os.path.join(DB_DIR, "app.db")


def get_connection() -> sqlite3.Connection:
	os.makedirs(DB_DIR, exist_ok=True)
	conn = sqlite3.connect(DB_PATH, check_same_thread=False)
	conn.row_factory = sqlite3.Row
	return conn


def init_db() -> None:
	conn = get_connection()
	cur = conn.cursor()

	# Users (docerias e superusuários)
	cur.execute(
		"""
		CREATE TABLE IF NOT EXISTS users (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			username TEXT UNIQUE NOT NULL,
			password_hash TEXT NOT NULL,
			bakery_name TEXT,
			email TEXT,
			is_superuser INTEGER NOT NULL DEFAULT 0,
			created_at TEXT NOT NULL
		)
		"""
	)

	# Clients por usuário/doceria
	cur.execute(
		"""
		CREATE TABLE IF NOT EXISTS clients (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			user_id INTEGER NOT NULL,
			name TEXT NOT NULL,
			phone TEXT,
			notes TEXT,
			created_at TEXT NOT NULL,
			FOREIGN KEY (user_id) REFERENCES users (id)
		)
		"""
	)

	# Orders (encomendas)
	cur.execute(
		"""
		CREATE TABLE IF NOT EXISTS orders (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			user_id INTEGER NOT NULL,
			client_id INTEGER NOT NULL,
			flavor TEXT NOT NULL,
			size TEXT,
			price REAL,
			due_date TEXT NOT NULL,
			status TEXT NOT NULL,
			notes TEXT,
			created_at TEXT NOT NULL,
			paid_at TEXT,
			delivered_at TEXT,
			FOREIGN KEY (user_id) REFERENCES users (id),
			FOREIGN KEY (client_id) REFERENCES clients (id)
		)
		"""
	)

	conn.commit()

	# Seed de superusuário padrão se nenhum usuário existir
	cur.execute("SELECT COUNT(1) AS c FROM users")
	count = cur.fetchone()["c"]
	if count == 0:
		from auth import hash_password  # lazy import para evitar ciclo
		cur.execute(
			"""
			INSERT INTO users (username, password_hash, bakery_name, email, is_superuser, created_at)
			VALUES (?, ?, ?, ?, ?, ?)
			""",
			(
				"admin",
				hash_password("admin123"),
				"Admin",
				"admin@example.com",
				1,
				datetime.utcnow().isoformat(),
			),
		)
		conn.commit()

	cur.close()
	conn.close()


# USERS

def create_user(username: str, password_hash: str, bakery_name: Optional[str], email: Optional[str], is_superuser: bool) -> int:
	conn = get_connection()
	cur = conn.cursor()
	cur.execute(
		"""
		INSERT INTO users (username, password_hash, bakery_name, email, is_superuser, created_at)
		VALUES (?, ?, ?, ?, ?, ?)
		""",
		(username, password_hash, bakery_name, email, 1 if is_superuser else 0, datetime.utcnow().isoformat()),
	)
	conn.commit()
	user_id = cur.lastrowid
	cur.close()
	conn.close()
	return user_id


def get_user_by_username(username: str) -> Optional[sqlite3.Row]:
	conn = get_connection()
	cur = conn.cursor()
	cur.execute("SELECT * FROM users WHERE username = ?", (username,))
	row = cur.fetchone()
	cur.close()
	conn.close()
	return row


def get_user_by_id(user_id: int) -> Optional[sqlite3.Row]:
	conn = get_connection()
	cur = conn.cursor()
	cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
	row = cur.fetchone()
	cur.close()
	conn.close()
	return row


def list_users() -> List[sqlite3.Row]:
	conn = get_connection()
	cur = conn.cursor()
	cur.execute("SELECT * FROM users ORDER BY created_at DESC")
	rows = cur.fetchall()
	cur.close()
	conn.close()
	return rows


def update_user_password(user_id: int, new_password_hash: str) -> None:
	conn = get_connection()
	cur = conn.cursor()
	cur.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_password_hash, user_id))
	conn.commit()
	cur.close()
	conn.close()


# CLIENTS

def create_client(user_id: int, name: str, phone: Optional[str], notes: Optional[str]) -> int:
	conn = get_connection()
	cur = conn.cursor()
	cur.execute(
		"""
		INSERT INTO clients (user_id, name, phone, notes, created_at)
		VALUES (?, ?, ?, ?, ?)
		""",
		(user_id, name, phone, notes, datetime.utcnow().isoformat()),
	)
	conn.commit()
	client_id = cur.lastrowid
	cur.close()
	conn.close()
	return client_id


def list_clients(user_id: int) -> List[sqlite3.Row]:
	conn = get_connection()
	cur = conn.cursor()
	cur.execute("SELECT * FROM clients WHERE user_id = ? ORDER BY name", (user_id,))
	rows = cur.fetchall()
	cur.close()
	conn.close()
	return rows


def delete_client(user_id: int, client_id: int) -> None:
	conn = get_connection()
	cur = conn.cursor()
	# Também apagamos encomendas do cliente
	cur.execute("DELETE FROM orders WHERE user_id = ? AND client_id = ?", (user_id, client_id))
	cur.execute("DELETE FROM clients WHERE user_id = ? AND id = ?", (user_id, client_id))
	conn.commit()
	cur.close()
	conn.close()


# ORDERS

def create_order(
	user_id: int,
	client_id: int,
	flavor: str,
	size: Optional[str],
	price: Optional[float],
	due_date_iso: str,
	status: str,
	notes: Optional[str],
) -> int:
	conn = get_connection()
	cur = conn.cursor()
	cur.execute(
		"""
		INSERT INTO orders (user_id, client_id, flavor, size, price, due_date, status, notes, created_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
		""",
		(
			user_id,
			client_id,
			flavor,
			size,
			price,
			due_date_iso,
			status,
			notes,
			datetime.utcnow().isoformat(),
		),
	)
	conn.commit()
	order_id = cur.lastrowid
	cur.close()
	conn.close()
	return order_id


def list_orders(user_id: int) -> List[sqlite3.Row]:
	conn = get_connection()
	cur = conn.cursor()
	cur.execute(
		"""
		SELECT o.*, c.name AS client_name
		FROM orders o
		JOIN clients c ON c.id = o.client_id
		WHERE o.user_id = ?
		ORDER BY o.due_date ASC, o.created_at DESC
		""",
		(user_id,),
	)
	rows = cur.fetchall()
	cur.close()
	conn.close()
	return rows


def list_orders_by_client(user_id: int, client_id: int) -> List[sqlite3.Row]:
	conn = get_connection()
	cur = conn.cursor()
	cur.execute(
		"""
		SELECT o.*, c.name AS client_name
		FROM orders o
		JOIN clients c ON c.id = o.client_id
		WHERE o.user_id = ? AND o.client_id = ?
		ORDER BY o.due_date ASC, o.created_at DESC
		""",
		(user_id, client_id),
	)
	rows = cur.fetchall()
	cur.close()
	conn.close()
	return rows


def update_order_status(user_id: int, order_id: int, status: str) -> None:
	conn = get_connection()
	cur = conn.cursor()
	timestamp_field = None
	if status.startswith("Pago"):
		timestamp_field = "paid_at"
	elif status == "Entregue":
		timestamp_field = "delivered_at"

	if timestamp_field:
		cur.execute(
			f"UPDATE orders SET status = ?, {timestamp_field} = ? WHERE user_id = ? AND id = ?",
			(status, datetime.utcnow().isoformat(), user_id, order_id),
		)
	else:
		cur.execute(
			"UPDATE orders SET status = ? WHERE user_id = ? AND id = ?",
			(status, user_id, order_id),
		)
	conn.commit()
	cur.close()
	conn.close()


def delete_order(user_id: int, order_id: int) -> None:
	conn = get_connection()
	cur = conn.cursor()
	cur.execute("DELETE FROM orders WHERE user_id = ? AND id = ?", (user_id, order_id))
	conn.commit()
	cur.close()
	conn.close()


def stats_counts(user_id: int) -> Dict[str, int]:
	conn = get_connection()
	cur = conn.cursor()
	statuses = ["Pendente", "Pago (Em preparação)", "Entregue"]
	result: Dict[str, int] = {s: 0 for s in statuses}
	for s in statuses:
		cur.execute("SELECT COUNT(1) AS c FROM orders WHERE user_id = ? AND status = ?", (user_id, s))
		result[s] = cur.fetchone()["c"]
	cur.close()
	conn.close()
	return result

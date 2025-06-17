import sqlite3
import os

def add_user_to_db(user_id, first_name, last_name, chat_id, username):
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'telgrambotusers.db')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
    existing_user = cursor.fetchone()

    if existing_user:
        pass
    else:
        cursor.execute('''
        INSERT INTO users (first_name, last_name, chat_id, username)
        VALUES (?, ?, ?, ?)
        ''', (first_name, last_name, chat_id, username))
        print(f"User {user_id} added to database.")

    conn.commit()
    conn.close()


def create_db():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'telgrambotusers.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        first_name TEXT,
        last_name TEXT,
        chat_id INTEGER,
        username TEXT
    )
    ''')

    conn.commit()
    conn.close()

create_db()

import sqlite3

DB_PATH = "bridge.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER NOT NULL UNIQUE
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS bridges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                telegram_chat_id INTEGER NOT NULL UNIQUE,
                max_chat_id INTEGER NOT NULL UNIQUE,
                enabled INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        conn.commit()


def get_or_create_user(telegram_user_id):
    with get_connection() as conn:
        result = conn.execute("""
            SELECT id
            FROM users
            WHERE telegram_user_id = ?
        """, (telegram_user_id,)).fetchone()

        if result:
            return result[0]

        cursor = conn.execute("""
            INSERT INTO users (telegram_user_id)
            VALUES (?)
        """, (telegram_user_id,))

        conn.commit()

        return cursor.lastrowid


def add_bridge(telegram_user_id, telegram_chat_id, max_chat_id):
    user_id = get_or_create_user(telegram_user_id)

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO bridges (
                user_id,
                telegram_chat_id,
                max_chat_id
            )
            VALUES (?, ?, ?)
        """, (
            user_id,
            telegram_chat_id,
            max_chat_id
        ))

        conn.commit()


def remove_bridge(telegram_chat_id, max_chat_id):
    with get_connection() as conn:
        conn.execute("""
            DELETE FROM bridges
            WHERE telegram_chat_id = ?
            AND max_chat_id = ?
        """, (
            telegram_chat_id,
            max_chat_id
        ))

        conn.commit()


def get_max_chat_id(telegram_chat_id):
    with get_connection() as conn:
        result = conn.execute("""
            SELECT max_chat_id
            FROM bridges
            WHERE telegram_chat_id = ?
            AND enabled = 1
        """, (telegram_chat_id,)).fetchone()

        if result:
            return result[0]

        return None


def get_telegram_chat_id(max_chat_id):
    with get_connection() as conn:
        result = conn.execute("""
            SELECT telegram_chat_id
            FROM bridges
            WHERE max_chat_id = ?
            AND enabled = 1
        """, (max_chat_id,)).fetchone()

        if result:
            return result[0]

        return None


def get_user_bridges(telegram_user_id):
    with get_connection() as conn:
        result = conn.execute("""
            SELECT
                telegram_chat_id,
                max_chat_id,
                enabled
            FROM bridges
            WHERE user_id = (
                SELECT id
                FROM users
                WHERE telegram_user_id = ?
            )
        """, (telegram_user_id,)).fetchall()

        return result


if __name__ == "__main__":
    init_db()
    print("База данных инициализирована")

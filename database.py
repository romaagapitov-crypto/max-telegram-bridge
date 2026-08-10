import sqlite3

DB_PATH = "bridge.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bridges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_chat_id INTEGER NOT NULL UNIQUE,
                max_chat_id INTEGER NOT NULL UNIQUE,
                enabled INTEGER NOT NULL DEFAULT 1
            )
        """)

        conn.commit()


def add_bridge(telegram_chat_id, max_chat_id):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO bridges (
                telegram_chat_id,
                max_chat_id
            )
            VALUES (?, ?)
        """, (
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



if __name__ == "__main__":
    init_db()

    print(
        "MAX для Telegram:",
        get_max_chat_id(-5471339047)
    )

    print(
        "Telegram для MAX:",
        get_telegram_chat_id(-77682869790919)
    )
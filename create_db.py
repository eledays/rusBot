import sqlite3


def create(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            author_id INTEGER NOT NULL,
            human_verified BOOLEAN DEFAULT FALSE,
            admin_verified BOOLEAN DEFAULT FALSE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pieces (
            id INTEGER PRIMARY KEY,
            topic_id INTEGER NOT NULL,
            data TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            piece_id INTEGER NOT NULL,
            send_at DATETIME
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS statictics (
            user_id INTEGER NOT NULL,
            piece_id INTEGER NOT NULL,
            color TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER,
            do_not_disturb_start TIME,
            do_not_disturb_end TIME
        )
    ''')
    conn.commit()


if __name__ == '__main__':
    conn = sqlite3.connect('db.sqlite3')
    create(conn)
    conn.close()
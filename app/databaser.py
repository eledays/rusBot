import sqlite3


class Databaser:

    def __init__(self, filename='app.db'):
        self.conn = sqlite3.connect(filename, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def create(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                author_id INTEGER NOT NULL,
                human_verified BOOLEAN DEFAULT FALSE,
                admin_verified BOOLEAN DEFAULT FALSE
            )
        ''')

    def add(self, name, author_id, human_verified=False, admin_verified=False):
        self.cursor.execute('''
            INSERT INTO topics (name, author_id, human_verified, admin_verified)
            VALUES (?, ?, ?, ?)
        ''', (name, author_id, human_verified, admin_verified))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_all(self):
        self.cursor.execute('''
            SELECT * FROM topics
        ''')
        return self.cursor.fetchall()
    
    def get_name_by_id(self, id):
        self.cursor.execute('''
            SELECT name FROM topics WHERE id = ?
        ''', (id,))
        return self.cursor.fetchone()['name']
    
    def delete(self, id):
        self.cursor.execute('''
            DELETE FROM topics WHERE id = ?
        ''', (id,))
        self.conn.commit()
        
        
        
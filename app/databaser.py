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
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS pieces (
                id INTEGER PRIMARY KEY,
                topic_id INTEGER NOT NULL,
                data TEXT NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                piece_id INTEGER NOT NULL,
                send_at DATETIME
            )
        ''')
        self.conn.commit()

    def add_topic(self, name, author_id, human_verified=False, admin_verified=False):
        self.cursor.execute('''
            INSERT INTO topics (name, author_id, human_verified, admin_verified)
            VALUES (?, ?, ?, ?)
        ''', (name, author_id, human_verified, admin_verified))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_topics(self):
        self.cursor.execute('''
            SELECT * FROM topics
        ''')
        return self.cursor.fetchall()
    
    def get_topic(self, topic_id):
        self.cursor.execute('''
            SELECT * FROM topics WHERE id = ?
        ''', (topic_id,))
        return self.cursor.fetchone()
    
    def get_topic_name_by_id(self, id):
        self.cursor.execute('''
            SELECT name FROM topics WHERE id = ?
        ''', (id,))
        return self.cursor.fetchone()['name']
    
    def delete_topic(self, id):
        self.cursor.execute('''
            DELETE FROM topics WHERE id = ?
        ''', (id,))
        self.conn.commit()
    
    def add_piece(self, topic_id, data):
        self.cursor.execute('''
            INSERT INTO pieces (topic_id, data)
            VALUES (?, ?)
        ''', (topic_id, data))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def add_pieces(self, topic_id, pieces):
        self.cursor.executemany('''
            INSERT INTO pieces (topic_id, data)
            VALUES (?, ?)
        ''', [(topic_id, e) for e in pieces])
        self.conn.commit()
    
    def get_pieces(self, topic_id):
        self.cursor.execute('''
            SELECT * FROM pieces WHERE topic_id = ?
        ''', (topic_id,))
        return self.cursor.fetchall()
    
    def get_piece_to_send(self, user_id):
        self.cursor.execute('''
            SELECT * FROM schedule WHERE user_id = ? AND send_at <= DATETIME('now') ORDER BY send_at ASC LIMIT 1
        ''', (user_id,))
        scheduled = self.cursor.fetchone()

        if scheduled:
            self.cursor.execute('''
                DELETE FROM schedule WHERE id = ?
            ''', (scheduled['id'],))
            self.conn.commit()
            return scheduled
        else:
            self.cursor.execute('''
                SELECT * FROM schedule WHERE user_id = ? AND send_at IS NULL LIMIT 1
            ''', (user_id,))
            piece = self.cursor.fetchone()
            if piece:
                self.cursor.execute('''
                    DELETE FROM schedule WHERE id =?
                ''', (piece['user_id'],))
                self.conn.commit()
                return piece

    def get_users(self):
        self.cursor.execute('''
            SELECT DISTINCT user_id FROM schedule
        ''')
        return self.cursor.fetchall()

    def __del__(self):
        self.conn.close()
        
        
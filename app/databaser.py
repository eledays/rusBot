import sqlite3
from datetime import datetime


class Databaser:

    def __init__(self, filename='app.db'):
        self.conn = sqlite3.connect(filename, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

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

    def update_pieces(self, topic_id, pieces):
        self.cursor.execute('''
            DELETE FROM pieces WHERE topic_id = ?
        ''', (topic_id,))
        self.add_pieces(topic_id, pieces)
        self.conn.commit()

    def get_piece(self, piece_id):
        self.cursor.execute('''
            SELECT * FROM pieces WHERE id = ?
        ''', (piece_id,))
        return self.cursor.fetchone()
    
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
                UPDATE schedule SET send_at = NULL WHERE id = ?
            ''', (scheduled['id'],))
            self.conn.commit()
            piece_id = scheduled['piece_id']
            piece = self.get_piece(piece_id)
            return scheduled['user_id'], piece['data'], piece_id

        # Порция без даты  
        self.cursor.execute('''
            SELECT * FROM schedule WHERE user_id = ? AND send_at IS NULL LIMIT 1
        ''', (user_id,))
        scheduled = self.cursor.fetchone()

        if scheduled:
            piece_id = scheduled['piece_id']
            piece = self.get_piece(piece_id)
            return scheduled['user_id'], piece['data'], piece_id
        
        # Порция с датой из будущего
        self.cursor.execute('''
            SELECT * FROM schedule WHERE user_id = ? ORDER BY send_at ASC LIMIT 1
        ''', (user_id,))
        scheduled = self.cursor.fetchone()
        if scheduled:
            self.cursor.execute('''
                UPDATE schedule SET send_at = NULL WHERE id = ?
            ''', (scheduled['id'],))
            self.conn.commit()
            piece_id = scheduled['piece_id']
            piece = self.get_piece(piece_id)

            return scheduled['user_id'], piece['data'], piece_id
            
    def postpone_piece(self, piece_id, user_id, days):
        query = f'''
            UPDATE schedule SET send_at = DATETIME('now', '+{days} day') WHERE piece_id = {piece_id} AND user_id = {user_id}
        '''
        self.cursor.execute(query)
        self.conn.commit()

    def get_users(self):
        self.cursor.execute('''
            SELECT DISTINCT user_id FROM schedule
        ''')
        return self.cursor.fetchall()
    
    def has_user_pieces(self, user_id):
        self.cursor.execute('''
            SELECT * FROM schedule WHERE user_id = ?
        ''', (user_id,))
        return bool(self.cursor.fetchone())
    
    def add_topic_to_user(self, user_id, topic_id):
        self.cursor.execute('''
            INSERT INTO schedule (user_id, piece_id, send_at)
            SELECT ?, p.id, NULL 
            FROM pieces p
            WHERE p.topic_id = ? 
            AND NOT EXISTS (
                SELECT 1 FROM schedule s
                WHERE s.user_id = ? AND s.piece_id = p.id
            )
        ''', (user_id, topic_id, user_id))
        self.conn.commit()

    def piece_reation(self, user_id, piece_id, color):
        self.cursor.execute('''
            INSERT INTO statictics (user_id, piece_id, color)
            VALUES (?, ?, ?)
        ''', (user_id, piece_id, color))
        self.conn.commit()

    def get_user_pieces(self, user_id):
        self.cursor.execute('''
            SELECT * FROM schedule WHERE user_id = ?
        ''', (user_id,))
        return self.cursor.fetchall()

    def set_do_not_disturb(self, user_id, start_time, end_time):
        try:
            datetime.strptime(start_time, '%H:%M').time()
            datetime.strptime(end_time, '%H:%M').time()
        except:
            return

        self.cursor.execute('''
            DELETE FROM user_settings WHERE user_id = ?
        ''', (user_id,))
        self.conn.commit()
        
        self.cursor.execute('''
            INSERT INTO user_settings (user_id, do_not_disturb_start, do_not_disturb_end)
            VALUES (?, ?, ?)
        ''', (user_id, start_time, end_time))
        self.conn.commit()

    def get_do_not_disturb(self, user_id):
        self.cursor.execute('''
            SELECT do_not_disturb_start, do_not_disturb_end FROM user_settings WHERE user_id = ?
        ''', (user_id,))
        dnd = self.cursor.fetchone()

        if dnd is None:
            return

        start_time, end_time = dnd
        start_time = datetime.strptime(start_time, '%H:%M').time()
        end_time = datetime.strptime(end_time, '%H:%M').time()

        return start_time, end_time
    
    def can_send(self, user_id):
        do_not_disturb = self.get_do_not_disturb(user_id)
        if do_not_disturb:
            start_time, end_time = do_not_disturb
            return not (start_time <= datetime.now().time() <= end_time)
        return True

    def __del__(self):
        self.conn.close()


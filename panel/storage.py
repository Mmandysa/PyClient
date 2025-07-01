import os
import sqlite3
class SecureStorage:
    def __init__(self):
        self.db_path = "db"
        self._init_db()
    
    def _init_db(self):
        try:
            # SQLite 会自动创建文件，不要手动 open
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute(
                '''
                    create table if not exists friends (
                        user_id integer primary key,
                        public_key text not null,
                        session_key text
                    )
                    
                    create table if not exists my_userid (
                        user_id integer primary key
                    )
                '''
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error initializing database: {e}")
        
    def save_key(self, user_id, public_key, session_key=None):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                select 1 from friends where user_id = ?
            ''',(user_id,))
            
            result = cursor.fetchone()
            
            if result:
                cursor.execute('''
                    update friends set public_key = ?, session_key = ? where user_id = ?
                ''', (public_key, session_key, user_id))
                conn.commit()
                conn.close()
            else:    
                cursor.execute('''
                    insert into friends (user_id, public_key, session_key) values (?, ?, ?)
                ''', (user_id, public_key, session_key))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error saving key: {e}")
        
    def get_public_key(self, user_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                select public_key from friends where user_id = ?
            ''', (user_id,))
            result = cursor.fetchone()
            public_key = result[0]
            conn.close()
            
        except Exception as e:
            print(f"Error getting public key: {e}")
            public_key = None
        
        return public_key

    def get_session_key(self, user_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                select session_key from friends where user_id = ?
            ''', (user_id,))
            result = cursor.fetchone()
            session_key = result[0]
            conn.close()
            
        except Exception as e:
            print(f"Error getting public key: {e}")
            session_key = None
        
        return session_key

    def remove_session_key(self, user_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                update friends set session_key = null where user_id = ?
            ''', (user_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error removing session key: {e}")   
    
    
    def save_my_user_id(self, user_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                insert into my_userid (user_id) values (?)
            ''', (user_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error saving my user id: {e}")
            
    def get_my_user_id(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                select user_id from my_userid
            ''')
            result = cursor.fetchone()
            my_user_id = result[0]
            conn.close()
        except Exception as e:
            print(f"Error getting my user id: {e}")
            my_user_id = None
        return my_user_id
    
    def _remove_db(self):
        if __name__ == "__main__":
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
    
if __name__ == "__main__":
    """ storage = SecureStorage()
    storage.save_key(1, "public_key", "session_key")
    print(storage.get_public_key(1))
    print(type(storage.get_public_key(1)))
    print(storage.get_session_key(1))
    print(type(storage.get_session_key(1)))
    storage._remove_db() """
    
    """ storage1 = SecureStorage()
    storage2 = SecureStorage()
    
    storage1.save_key(1, "public_key1", "session_key1")
    storage2.save_key(2, "public_key2", "session_key2")
    
    print(storage1.get_public_key(2))
    print(storage2.get_public_key(1)) """
    
    
        
        
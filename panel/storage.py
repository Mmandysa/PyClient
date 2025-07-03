import os
import sqlite3
from panel.Singleton import Singleton
from datetime import datetime
from time import time
from panel.connect import *
import logging

class SecureStorage(Singleton):
    def __init__(self):
        self.db_path = "db"
        self._init_db()
    
    def _init_db(self):
        try:
            # SQLite 会自动创建文件，不要手动 open
            conn = sqlite3.connect(self.db_path) # 注意只能由一个进程连接数据库 
            cursor = conn.cursor()
            cursor.execute(
                '''
                    create table if not exists friends (
                        user_id integer primary key,
                        public_key text not null,
                        session_key text
                    )
                    
                '''
            )
            
            cursor.execute(
                '''
                    create table if not exists messages (
                        user_id integer not null,
                        message text not null,
                        time varchar(20) not null
                    )
                '''
            )
            
            cursor.execute(
                '''           
                    create table if not exists my_userid (
                        user_id integer primary key
                    )
                '''
            )

            
            # 检查 my_userid 表是否包含 token 列
            cursor.execute(
                '''
                    PRAGMA table_info(my_userid)
                '''
            )
            columns = cursor.fetchall()
            column_names = [column[1] for column in columns]
            
            if 'token' not in column_names:
                # 如果 token 列不存在，则添加该列
                cursor.execute(
                    '''
                        alter table my_userid add column token text NULL
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
            # 先检查是否已存在记录
            cursor.execute('SELECT 1 FROM my_userid')
            if cursor.fetchone():  # 如果已有记录
                print(f"用户ID已存在，无需重复保存")
                return
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
                
    def save_message(self, user_id: int, message: str, timestamp=None):
        try:
            # 如果没有提供时间，使用当前时间
            if timestamp is None:
                timestamp = datetime.now()
            
            # 将时间转换为字符串格式
            time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                insert into messages (user_id, message, time) values (?, ?, ?)
            ''', (user_id, message, time_str))  # 使用格式化后的时间字符串
            conn.commit()
        except Exception as e:
            print(f"Error saving message: {e}")
        finally:
            if conn:
                conn.close()
            
    def read_message(self,user_id:str):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                select * from messages where user_id = ?
            ''', (user_id,))
            message = cursor.fetchall()
            conn.close()
        except Exception as e:
            print(f"Error reading message: {e}")
            message = None
        return message
    
    def read_message_with_offline(self,user_id:str):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                select * from messages where user_id = ?
            ''', (user_id,))
            message = cursor.fetchall()
            conn.close()
        except Exception as e:
            print(f"Error reading message: {e}")
            message = None
        return message
    
    def save_token(self, user_id: int, token: str):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                update my_userid set token = ? where user_id = ?
            ''', (token, user_id))
            conn.commit()
        except Exception as e:
            print(f"Error saving token: {e}")
        finally:
            if conn:
                conn.close()
                
    def get_token(self, user_id: int):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                select token from my_userid where user_id = ?
            ''', (user_id,))
            result = cursor.fetchone()
            if result:
                token = result[0]
                logging.info(f"Reading Database: Token for user {user_id} is {token}")
                return token
            else:
                return None
        except Exception as e:
            print(f"Error getting token: {e}")
            return None
        finally:
            if conn:
                conn.close()
                
    
    
if __name__ == "__main__":
    storage = SecureStorage()
    storage.save_key(1, "public_key", "session_key")
    print(storage.get_public_key(1))
    print(type(storage.get_public_key(1)))
    print(storage.get_session_key(1))
    print(type(storage.get_session_key(1)))
    
    
    storage1 = SecureStorage()
    storage2 = SecureStorage()
    
    storage1.save_key(1, "public_key1", "session_key1")
    storage2.save_key(2, "public_key2", "session_key2")
    
    print(storage1.get_public_key(2))
    print(storage2.get_public_key(1))
    
    storage1.save_message(1,"hello0",datetime.now())
    storage2.save_message(1,"hello8",datetime.now())
    
    print(storage1.read_message(1))
    print(storage2.read_message(1))
    print(type(storage1.read_message(1)))
    
    storage1._remove_db()
    storage._remove_db()
    
        
        
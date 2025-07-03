from panel.storage import *
from panel.encrypt import *
from panel.Singleton import Singleton
import threading
import struct
import socket
from concurrent.futures import ThreadPoolExecutor
import time

class P2PEndpoint(Singleton):    
    def __init__(self, host, port):
        self._storage = SecureStorage()
        self._crypto_manager = CryptoManager()
        self._thread_handler = P2PThreadHandler()
        self._host = host
        self._port = port
        self._max_connections = 10
        self.active_connections = {}
        self.passive_connections = {}
        self.session_keys = {}
        self.handle_threads_is_running = {}
        
    def start_server(self):
        """启动服务器监听线程"""
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self._host, self._port))
        self.server.listen(self._max_connections)
        self._thread_handler.stop_event.clear()
        self.server.settimeout(1)
        self._thread_handler.executor.submit(self._accept_connections)
        print(f"[Server] Listening on {self._host}:{self._port}")

    def establish_connection(self, user_id, host, port):
        """发起主动连接并进行密钥交换"""
        with self._thread_handler.get_connections_lock("active_connections"):
            if user_id in self.active_connections:
                print(f"[Connect] Already connected to user {user_id}")
                return

            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                with self._thread_handler.get_conn_lock(client):
                    client.connect((host, port))
                    print(f"[Connect] Connected to {host}:{port}")
            except Exception as e:
                print(f"[ERROR] Failed to connect to {host}:{port} - {e}")
                return

            try:
                print(f"[Connect] Initiating key exchange with user {user_id}")
                payload = self._init_key_exchange(user_id)
                msg = P2PMessage(P2PMessage.MSG_TYPE_KEY_EXCHANGE, self.get_my_user_id(), payload)
                with self._thread_handler.get_conn_lock(client):
                    client.sendall(msg.to_bytes())
                self.active_connections[user_id] = client
                future = self._thread_handler.executor.submit(self._recv_key_exchange_ack, client)
                result = future.result()
                if result:
                    print(f"[Connect] Key exchange with user {user_id} completed")
                    self.handle_threads_is_running[client] = True
                    self._thread_handler.executor.submit(self._handle_connection, client)      
                    print(f"[Connect] _handle_connection is running: {self.handle_threads_is_running[client]},target:{host}:{port}")
                else:
                    print(f"[Connect] Key exchange with user {user_id} failed")
                    self.close_active_connection(user_id)
            except Exception as e:
                print(f"[ERROR] Failed during key exchange with user {user_id} - {e}")
                client.close()
                if user_id in self.active_connections:
                    del self.active_connections[user_id]
    
    def _accept_connections(self):
        print("[Server] Accepting connections...")
        while self.is_running():
            try:
                conn, addr = self.server.accept()
                print(f"[Server] New connection from {addr}")
                self.handle_threads_is_running[conn] = True
                print(f"[Server] _handle_connection is running: {self.handle_threads_is_running[conn]},target:{addr}")
                self._thread_handler.executor.submit(self._handle_connection, conn)
            except socket.timeout:
                continue
            except OSError:
                print("[Server] Socket closed")
                break
        print("[Server] Stopped accepting connections")

    def _handle_connection(self, conn):
        """处理客户端连接"""
        user_id = None
        try:
            while self.is_running() and self.handle_threads_is_running[conn]:
                try:
                    with self._thread_handler.get_conn_lock(conn):
                        conn.settimeout(1.0)
                        data = P2PMessage.from_socket(conn)
                    if data is None:
                        break
                    user_id = data.my_user_id
                    if data.msg_type == P2PMessage.MSG_TYPE_KEY_EXCHANGE:
                        print(f"[Server] Handling key exchange from {user_id}")
                        self._handle_key_exchange(user_id, data.payload)
                        self.passive_connections[user_id] = conn
                        self._send_key_exchange_ack(user_id)
                    elif data.msg_type == P2PMessage.MSG_TYPE_TEXT:
                        self._recv_message(data, conn)
                    elif data.msg_type == P2PMessage.MSG_TYPE_KEY_EXCHANGE_ACK:
                        print(f"[Server] Received ACK from {user_id}")
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"[ERROR] Handling message failed: {str(e)}")
                    break
        except Exception as e:
            print(f"[Server] Connection failed: {str(e)}")
        finally:
            if user_id:
                self.close_passive_connection(user_id)

    def _handle_key_exchange(self, user_id, encrypted_session_key_bytes):
        """处理接收到的密钥交换请求"""
        print(f"[Server] Starting decryption of session key for user {user_id}")
        session_key = self._crypto_manager.decrypt_session_key(encrypted_session_key_bytes,message_type="bytes")
        print(f"[Server] Decrypted session key, user_id: {user_id}, lenth: {len(session_key)}")
        self.save_session_key(user_id, session_key)
        print(f"[Server] Key exchange completed with user {user_id}")

    def _init_key_exchange(self, user_id):
        """生成新的对称密钥并加密发给好友"""
        public_key = self._storage.get_public_key(user_id)
        if not public_key:
            print(f"[WARNING] Public key for user {user_id} not found")
            return None

        res = self._crypto_manager.encrypt_session_key_for_friend(public_key)
        encrypted_key = res["encrypted_key"]
        session_key = res["session_key"]
        print(f"[Server] Cached session key for user {user_id}")
        self.save_session_key(user_id, session_key)
        
        return b64decode(encrypted_key)

    @staticmethod
    def _send_handler(func):
        def wrapper(self, *args):
            try:
                self._thread_handler.finish_handle_event.clear()
                user_id = next((arg for arg in args if isinstance(arg, int)), None)
                data = next((arg for arg in args if type(arg) in SecureStorage.storable_data), None)
                
                if not user_id:
                    raise Exception("No user ID provided")
                
                if data:
                    self._storage.save_sent_data(user_id, data)
                  
                func(self, *args)
            except Exception as e:
                print(f"[Send] Error: {e}")
            finally:
                self._thread_handler.finish_handle_event.set()
        return wrapper
    
    @_send_handler
    def send_message(self, user_id:int, content: str):
        """发送加密文本消息"""
        session_key = self.get_session_key(user_id)
        if session_key:
            res = self._crypto_manager.aes_encrypt_auto(content, session_key)
            encrypted_message = res["encrypted_message"]
            payload = encrypted_message.encode()
            msg = P2PMessage(P2PMessage.MSG_TYPE_TEXT, self.get_my_user_id(), payload)
            conn = self._conn_of_user(user_id)
            if conn:
                conn.sendall(msg.to_bytes())
                print(f"[Send] Sent message to user {user_id}")
        else:
            print(f"[Send] No session key for user {user_id}")

    @_send_handler
    def send_file(self, user_id:int, file_path: str):
        """发送文件"""
        pass

    @_send_handler
    def _send_key_exchange_ack(self, user_id: int):
        """发送密钥交换确认"""
        print(f"[Send] Preparing to send key exchange ACK to user {user_id}")
        session_key = self.get_session_key(user_id)
        if not session_key:
            return

        plain_text = "Your user id is " + str(user_id)
        print(f"[Send] ACK msg before encryption: {plain_text}")
        encrypted_payload_obj = self._crypto_manager.aes_encrypt_auto(plain_text, session_key)
        payload = encrypted_payload_obj["encrypted_message"].encode()
        msg = P2PMessage(P2PMessage.MSG_TYPE_KEY_EXCHANGE_ACK, self.get_my_user_id(), payload)

        conn = self._conn_of_user(user_id)
        if conn:
            conn.sendall(msg.to_bytes())
            print(f"[Send] Sent key exchange ACK to user {user_id}")
        print(f"[ERROR] No connection found for user {user_id}")

    def _conn_of_user(self, user_id):
        if user_id in self.active_connections:
            return self.active_connections[user_id]
        if user_id in self.passive_connections:
            return self.passive_connections[user_id]
        return None
    
    @staticmethod
    def _recv_handler(func):
        def wrapper(self, *args, **kwargs):
            try:
                self._thread_handler.finish_handle_event.clear()
                result = func(self, *args, **kwargs)
                if isinstance(result, tuple) and isinstance(result[0], int) and type(result[1]) in SecureStorage.storable_data:
                    self._storage.save_recv_data(result[0], result[1])
                return result
            except Exception as e:
                print(f"[Recv] Error: {e}")
                return None
            finally:
                self._thread_handler.finish_handle_event.set()
        return wrapper
    
    @_recv_handler
    def _recv_message(self, data, conn) -> tuple[int, str]:
        """接收加密文本消息并解密"""
        if data is None or not isinstance(data, P2PMessage):
            return None
            
        user_id = data.my_user_id
        if not user_id:
            return None
        
        session_key = self.get_session_key(user_id)
        if not session_key:
            print(f"[Recv] No session key for user {user_id}")
            return None
            
        payload_b64 = data.payload.decode()
        msg = self._crypto_manager.aes_decrypt_auto(payload_b64, session_key, "str")
        print(f"[Recv] Message from user {user_id}: {msg}")
        return user_id, msg

    @_recv_handler
    def _recv_file(self, data, conn: socket.socket) -> tuple[int, str]:
        """接收文件"""
        pass
    
    @_recv_handler
    def _recv_key_exchange_ack(self, conn: socket.socket, limit=5) -> bool:
        """接收密钥交换确认"""
        conn_lock = self._thread_handler.get_conn_lock(conn)
        if not conn_lock.acquire(timeout=limit):
            print("[Sever] Failed to acquire connection lock")
            return False
        
        try:
            def _check_key_exchange_ack(data: P2PMessage) -> bool:
                user_id = data.my_user_id
                session_key = self.get_session_key(user_id)
                if not session_key:
                    print(f"[ERROR] No session key available for user {user_id}")
                    return False
                
                encrypted_payload_b64 = data.payload.decode()
                msg = self._crypto_manager.aes_decrypt_auto(encrypted_payload_b64, session_key, "str")
                expected = "Your user id is " + str(self.get_my_user_id())
                
                print(f"[Recv] Key exchange ACK from user {user_id}: {msg}")
                return data.msg_type == P2PMessage.MSG_TYPE_KEY_EXCHANGE_ACK and msg == expected

            start_time = time.time()
            while time.time() - start_time < limit:
                try:
                    conn.settimeout(0.1)
                    data = P2PMessage.from_socket(conn)
                    if data and _check_key_exchange_ack(data):
                        return True
                except socket.timeout:
                    time.sleep(0.1)
                finally:
                    conn.settimeout(None)
            return False
        finally:
            conn_lock.release()
        
    def is_running(self):
        return not self._thread_handler.stop_event.is_set()
    
    def get_my_user_id(self):
        """获取本地用户 ID"""
        if not hasattr(self, "my_user_id") or self.my_user_id is None:
            self.my_user_id = self._storage.get_my_user_id()
        return self.my_user_id

    def close_server_and_connections(self):
        """关闭服务器和所有客户端连接"""
        self._thread_handler.stop_event.set()
        self.server.close()

        for user_id in list(self.passive_connections.keys()):
            self.close_passive_connection(user_id)
        
        for user_id in list(self.active_connections.keys()):
            self.close_active_connection(user_id)
            
        self._thread_handler.executor.shutdown(wait=True)
        print("[Close] Server and all connections closed.")

    def close_passive_connection(self, user_id):
        """关闭与特定用户的连接"""
        if user_id in self.passive_connections:
            with self._thread_handler.get_connections_lock("passive_connections"):
                with self._thread_handler.get_conn_lock(self.passive_connections[user_id]):
                    conn = self.passive_connections.pop(user_id)
                    self.handle_threads_is_running[conn] = False
                    print(f"[Server] _handle_connection {user_id} is running: {self.handle_threads_is_running[conn]}")
                    conn.close()
                    self._storage.remove_session_key(user_id)
                    print(f"[Close] Closed passive connection with user {user_id}")
             
    def close_active_connection(self, user_id):
        if user_id in self.active_connections:
            with self._thread_handler.get_connections_lock("active_connections"):
                with self._thread_handler.get_conn_lock(self.active_connections[user_id]):
                    conn = self.active_connections.pop(user_id)
                    self.handle_threads_is_running[conn] = False
                    print(f"[Server] _handle_connection {user_id} is running: {self.handle_threads_is_running[conn]}")
                    conn.close()
                    self._storage.remove_session_key(user_id)
                    print(f"[Close] Closed active connection with user {user_id}")

    def get_session_key(self, user_id):
        if user_id in self.session_keys:
            return self.session_keys[user_id]
        else:
            return self._storage.get_session_key(user_id)
        
    def save_session_key(self, user_id, session_key):
        self.session_keys[user_id] = session_key
        self._storage.save_session_key(user_id, session_key)
        
    def remove_session_key(self, user_id):
        if user_id in self.session_keys:
            del self.session_keys[user_id]
        self._storage.remove_session_key(user_id)
            
    def get_thread_handler(self):
        return self._thread_handler
        
class P2PMessage:
    HEADER_FORMAT = '!BII'
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    MSG_TYPE_TEXT = 1
    MSG_TYPE_KEY_EXCHANGE = 2
    MSG_TYPE_KEY_EXCHANGE_ACK = 3
    MSG_TYPE_FILE = 4
    MSG_TYPE_LSB = 5
    
    def __init__(self, msg_type: int, my_user_id: int, payload: bytes):
        self.msg_type = msg_type
        self.my_user_id = my_user_id
        self.payload = payload

    def to_bytes(self) -> bytes:
        header = struct.pack(self.HEADER_FORMAT, self.msg_type, self.my_user_id, len(self.payload))
        return header + self.payload

    @classmethod
    def from_socket(cls, conn: socket.socket):
        header = cls._recv_exact(conn, cls.HEADER_SIZE)
        if not header:
            return None
        msg_type, my_user_id, length = struct.unpack(cls.HEADER_FORMAT, header)
        payload = cls._recv_exact(conn, length)
        if not payload:
            return None
        return cls(msg_type, my_user_id, payload)

    @staticmethod
    def _recv_exact(conn: socket.socket, size):
        buf = b''
        while len(buf) < size:
            part = conn.recv(size - len(buf))
            if not part:
                return None
            buf += part
        return buf

class P2PThreadHandler(Singleton):
    def __init__(self, max_workers=14):
        self.conn_lock_map = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.stop_event = threading.Event()
        self.sever_lock = threading.Lock()
        self.finish_handle_event = threading.Event()
        
    def get_conn_lock(self, conn: socket.socket):
        if conn not in self.conn_lock_map:
            self.conn_lock_map[conn] = threading.Lock()
        return self.conn_lock_map[conn]
    
    def get_connections_lock(self, connections: str):
        if connections not in self.conn_lock_map:
            self.conn_lock_map[connections] = threading.Lock()
        return self.conn_lock_map[connections]
    

class P2PAPI(Singleton):
    def __init__(self):
        (host, port) = self._get_local_ip_port()
        self.end_point = P2PEndpoint(host, port)
        self.end_point.start_server()
        
    def p2p_api_thread(self):
        executor = self.end_point.get_thread_handler().executor
        executor.submit(self._run)
    
    def init_session(self, user_id, peer_ip, peer_port):
        return self.end_point.establish_connection(user_id, peer_ip, peer_port)
    
    def _run(self):
        try:
            while self.end_point.is_running():
                time.sleep(1)
        except KeyboardInterrupt:
            print("[API] User exit")
        finally:
            self.close()
        
    def send_message(self, user_id, msg, msg_type):
        if msg_type == "text":
            return self.end_point.send_message(user_id, msg)
        elif msg_type == "file":
            return self.end_point.send_file(user_id, msg)
        else:
            raise Exception("Invalid message type")
        
    def exit_session(self, user_id):
        self.end_point.close_passive_connection(user_id)
        self.end_point.close_active_connection(user_id)

    def close(self):
        self.end_point.close_server_and_connections()
        
    def _get_local_ip_port(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
                udp_socket.connect(('8.8.8.8', 80))
                ip = udp_socket.getsockname()[0]
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
                tcp_socket.bind(('', 0))
                port = tcp_socket.getsockname()[1]
            return (ip, port)
        except Exception as e:
            print(f"Failed to get IP/port: {e}")
            return (None, None)

    def get_crypto_manager(self):
        return self.end_point._crypto_manager

    def get_storage(self):
        return self.end_point._storage
    
if __name__ == "__main__":
    api = P2PAPI()
    api.get_storage().save_my_user_id(2)
    # 已经生成了公钥和私钥，生成则会覆盖，这里测试密钥交换
    
    executor = ThreadPoolExecutor(max_workers=1)
    executor.submit(api.p2p_api_thread)

    while True:
        print("---------------------------------------------------------------")
        print("1. 初始会话\n2. 发送消息\n3. 退出会话\n4. 退出服务")
        choice = input("请输入服务：")
        if choice == "2":
            msg = input("请输入消息：")
            api.send_message(1, msg, "text")
        elif choice == "3":
            api.exit_session(1)
        elif choice == "4":
            api.close()
            break
    
    

    
    
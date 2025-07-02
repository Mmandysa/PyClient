
from storage import *
from encrypt import *
from Singleton import Singleton
import threading
import struct
import socket
from concurrent.futures import ThreadPoolExecutor
class P2PEndpoint(Singleton):    
    def __init__(self, storage: SecureStorage, crypto_manager: CryptoManager, host, port):
        self._storage = storage
        self._crypto_manager = crypto_manager
        self._host = host
        self._port = port
        self._max_connections = 10 #accept队列最大连接数
        self.active_connections = {}  # 作为客户端，维护主动连接的用户，存放对应的socket.socket
        self.passive_connections = {} # 作为服务端，维护被动联接的用户，存放对应的socket.socket
        self.connections_lock = threading.Lock() # 互斥锁，用于保护连接字典
        self.last_heartbeat = {}
        self.executor = ThreadPoolExecutor(max_workers=14)
        

    def start_server(self):
        """启动服务器监听线程"""
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # 使用Ipv4，TCP
        self.server.bind((self._host, self._port)) # 绑定本机IP和端口
        self.server.listen(self._max_connections)  # 持续监听连接请求，accept队列最大为_max_connections
        self.running = True # 运行服务器
        self.server.settimeout(1) # 设置 socket.socket 超时时间，使得 accept 不会永久阻塞而无法关闭
        self._start_heartbeat()
        self._check_heartbeats()
        self.executor.submit(self._accept_connections)
        print(f"[Server] Listening on {self._host}:{self._port}")


    def establish_connection(self, user_id, host, port):
        """发起主动连接并进行密钥交换"""
        #print(f"[DEBUG] Trying to establish connection with user {user_id} at {host}:{port}")
        
        with self.connections_lock:
            if user_id in self.active_connections:
                print(f"[Client] Already connected to user {user_id}")
                return

            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                print(f"[DEBUG] Socket created for connection to {host}:{port}")
                
                client.connect((host, port))
                print(f"[Client] Connected to {host}:{port}")
            except Exception as e:
                print(f"[ERROR] Failed to connect to {host}:{port} - {e}")
                return

            try:
                print(f"[DEBUG] Initiating key exchange with user {user_id}")
                encrypted_key = self._init_key_exchange(user_id).encode()
                print(f"[DEBUG] Encrypted key for user {user_id}: {encrypted_key}")

                msg = P2PMessage(P2PMessage.MSG_TYPE_KEY_EXCHANGE, self.get_my_user_id(), encrypted_key)
                print(f"[DEBUG] Key exchange message created: {msg}")
                
                client.sendall(msg.to_bytes())
                print(f"[DEBUG] Key exchange message sent to {user_id}")

                self.active_connections[user_id] = client
                print(f"[DEBUG] Connection stored in active_connections for user {user_id}")

                self._recv_key_exchange_ack(client)
                print(f"[Client] Sent key exchange to user {user_id}")
            except Exception as e:
                print(f"[ERROR] Failed during key exchange with user {user_id} - {e}")
                client.close()
                if user_id in self.active_connections:
                    del self.active_connections[user_id]
                print(f"[DEBUG] Closed connection and removed from active_connections due to error")

    def _start_heartbeat(self, interval=30):
        """定期发送心跳"""
        def heartbeat_loop():
            from time import sleep
            while self.running:
                sleep(interval)
                
                with self.connections_lock:
                    for conn in self.active_connections.values():
                        self._send_heartbeat(conn)
                    for conn in self.passive_connections.values():
                        self._send_heartbeat(conn)
                        
        threading.Thread(target=heartbeat_loop, daemon=True).start()
        
    def _check_heartbeats(self, timeout=60, interval=10):
        from time import sleep, time
        def loop():
            while self.running:
                sleep(interval)
                now = time()
                to_close = []
                with self.connections_lock:
                    for user_id, t in self.last_heartbeat.items():
                        if now - t > timeout:
                            print(f"[Heartbeat] Timeout from user {user_id}, closing connection.")
                            to_close.append(user_id)
                    for user_id in to_close:
                        self.close_passive_connection(user_id)
        threading.Thread(target=loop, daemon=True).start()  
    
    def _accept_connections(self):
        #print("[Debug] _accept_connections start")
        while self.running:
            try:
                #print("[Debug] waiting for accept()")
                conn, addr = self.server.accept()
                #print(f"[Debug] accepted connection from {addr}")
                threading.Thread(target=self._handle_connection, args=(conn,), daemon=True).start()
                
            except socket.timeout:
                #print("[Debug] accept timed out, check running flag")
                continue
            except OSError:
                #print("[Debug] socket closed, exiting accept loop")
                break
        #print("[Debug] _accept_connections exit")

    def _handle_connection(self, conn):  # view_func
        """处理客户端发来的密钥交换请求"""
        user_id = None
        try:
            print("[Debug] _handle_connection started")
            while self.running:
                if not conn:
                    print("[Server] Connection is None.")
                    return 
                
                print("[Debug] Waiting to receive P2PMessage.from_socket(conn)")
                data = P2PMessage.from_socket(conn)  # 从连接中接收消息
                
                if data is None:
                    print("[Server] Invalid or empty message received.")
                    return
                
                user_id = data.my_user_id
                if not user_id:
                    print("[Server] Received message from unknown user with no user ID.")
                    return
                
                print(f"[Debug] Received message type {data.msg_type} from user {user_id}")
                
                if data.msg_type == P2PMessage.MSG_TYPE_KEY_EXCHANGE:
                    self._handle_key_exchange(user_id, data.payload)
                    self.passive_connections[user_id] = conn
                    print(f"[Server] Key exchange completed with user {user_id}")
                
                elif data.msg_type == P2PMessage.MSG_TYPE_TEXT:
                    msg = self.recv_message(conn)
                    print(f"[Server] Received message from user {user_id}: {msg}")
                
                elif data.msg_type == P2PMessage.MSG_TYPE_FILE:
                    print(f"[Debug] Receiving file from user {user_id}")
                    self._recv_file(conn)
                    print(f"[Debug] File received from user {user_id}")
                
                elif data.msg_type == P2PMessage.MSG_TYPE_HEARTBEAT:
                    from time import time
                    self._recv_heartbeat(conn)
                    self.last_heartbeat[user_id] = time()
                    print(f"[Server] Received heartbeat from user {user_id}")
                
                else:
                    print(f"[Server] Received unknown message type {data.msg_type} from user {user_id}")
        
        except Exception as e:
            print(f"[Server] Connection with user {user_id} failed: {e}")
            print(f"[Debug] Closing passive connection for user {user_id}")
            self.close_passive_connection(user_id)
            print(f"[Debug] Passive connection for user {user_id} closed")

                    

    def _handle_key_exchange(self, user_id, encrypted_session_key):
        """处理接收到的密钥交换请求"""
        public_key, private_key = self._crypto_manager.get_my_keys()
        session_key = self._crypto_manager.decrypt_session_key(encrypted_session_key, private_key)
        self._storage.save_key(user_id, public_key, session_key)

    def _init_key_exchange(self, user_id):
        """生成新的对称密钥并加密发给好友"""
        print(f"[DEBUG] Starting key exchange initialization with user {user_id}")
        
        # 获取好友公钥
        public_key = self._storage.get_public_key(user_id)
        if public_key:
            print(f"[DEBUG] Retrieved public key for user {user_id}: {public_key}")
        else:
            print(f"[WARNING] Public key for user {user_id} not found")

        # 使用公钥生成对称密钥并加密
        try:
            encrypted_key, session_key = self._crypto_manager.encrypt_session_key_for_friend(public_key)
            print(f"[DEBUG] Encrypted session key for user {user_id}: {encrypted_key}")
            print(f"[DEBUG] Generated session key for user {user_id}: {session_key}")
        except Exception as e:
            print(f"[ERROR] Failed to encrypt session key for user {user_id}: {e}")
            raise

        # 存储密钥
        try:
            self._storage.save_key(user_id, public_key, session_key)
            print(f"[DEBUG] Saved public key and session key for user {user_id}")
        except Exception as e:
            print(f"[ERROR] Failed to save keys for user {user_id}: {e}")
            raise

        # 缓存对称密钥（客户端层）
        self.session_key = session_key
        print(f"[DEBUG] Cached session key for user {user_id}")

        return encrypted_key


    @staticmethod
    def _send_error_handler(func):
        def wrapper(user_id, *args, **kwargs):
            try:
                if not user_id:
                    print("[Send] User ID is None")
                    return
                func(user_id, *args, **kwargs)
            except Exception as e:
                print(f"[Send] Error sending message to user {user_id}: {e}")
        return wrapper
    
    @_send_error_handler
    def send_message(self, user_id:int, content: str):
        """发送加密文本消息"""
        session_key = self._storage.get_session_key(user_id) # 获取好友的会话密钥
        if session_key:
            encrypted = self._crypto_manager.aes_encrypt_auto(content, session_key) # 加密
            payload = encrypted.encode() # 转化为字节流
            msg = P2PMessage(P2PMessage.MSG_TYPE_TEXT, self.get_my_user_id(), payload) # 创建文本消息
            conn = self._conn_of_user(user_id)
            conn.sendall(msg.to_bytes()) # 发送
            print(f"[Send] Sent encrypted message to user {user_id}")
        else:
            print(f"[Send] No session key for user {user_id}")

    @_send_error_handler
    def send_file(self, user_id, file_path: str):
        """发送文件"""
        pass
    
    @_send_error_handler
    def _send_heartbeat(self, user_id:int):
        """发送心跳包"""
        heartbeat = P2PMessage(
            P2PMessage.MSG_TYPE_HEARTBEAT,
            self.get_my_user_id(),
            b''
        )
        conn = self._conn_of_user(user_id)
        conn.sendall(heartbeat.to_bytes())

    @_send_error_handler
    def _send_key_exchange_ack(self,user_id:int):
        """发送密钥交换确认"""
        if not self.session_key:
            return P2PMessage(P2PMessage.MSG_TYPE_KEY_EXCHANGE_ACK, self.get_my_user_id(), b"I don't have a session key")
        payload = self._crypto_manager.aes_decrypt_auto("Your user id is " + user_id,self.session_key).encode()
        msg = P2PMessage(P2PMessage.MSG_TYPE_KEY_EXCHANGE_ACK, self.get_my_user_id(), payload)
        conn = self._conn_of_user(user_id)
        conn.sendall(msg.to_bytes())      

    def _conn_of_user(self, user_id):
        return self.active_connections.get(user_id) or self.passive_connections.get(user_id)
    @staticmethod
    def _recv_error_handler(func):
        def wrapper(*args):
            try:
                if not args:
                    raise Exception("[Recv] No arguments")
                for arg in args:
                    if isinstance(arg, socket.socket):
                        return func(*arg)
                raise Exception("[Recv] Argument is not a socket")
            except Exception as e:
                print(f"[Recv] Receive failed: {e}")
                
        return wrapper
    
    @_recv_error_handler
    def _recv_message(self, conn: socket.socket) -> str:
        """接收加密文本消息并解密"""
        try:
            data = P2PMessage.from_socket(conn)
            if data is None:
                return None
            user_id = data.my_user_id
            session_key = self._storage.get_session_key(user_id)
            
            if not session_key:
                print(f"[Recv] No session key for user {user_id}, trying to reconnect")
                peer_ip, peer_port = conn.getpeername()
                self.establish_connection(user_id, peer_ip, peer_port)
                return None
                
            payload = self._crypto_manager.aes_decrypt_auto(data.payload, session_key)
            msg = payload.decode()
            print(f"[Recv] Received message from user {user_id}: {msg}")
            return msg
        except Exception as e:
            print(f"[Recv] Message failed: {e}")
            return None

    @_recv_error_handler
    def _recv_file(self, conn: socket.socket) -> str:
        """接收文件"""
        pass
    
    @_recv_error_handler
    def _recv_heartbeat(self, conn: socket.socket):
        """接收心跳包"""
        user_ip, user_port = conn.getpeername()
        print(f"[Heartbeat] Received heartbeat from {user_ip}:{user_port}")

    @_recv_error_handler
    def _recv_key_exchange_ack(self, conn: socket.socket)->bool:
        """接收密钥交换确认"""
        from time import time,sleep
        def _check_key_exchange_ack(data: P2PMessage)->bool:
            msg = self._crypto_manager.aes_decrypt_auto(data.payload, self.session_key)
            if data.msg_type == P2PMessage.MSG_TYPE_KEY_EXCHANGE_ACK and msg == "Your user id is " + str(data.my_user_id):
                print("[Recv] Received key exchange ack from user", data.my_user_id)
                return True
            return False
        start_time = time()
        while time() - start_time < 5:
            try:
                conn.settimeout(0.1)
                data = P2PMessage.from_socket(conn)
                if _check_key_exchange_ack(data):
                    conn.settimeout(None)
                    return True
            except socket.socket.timeout:
                sleep(0.1)
                continue
        conn.settimeout(None)
        return False
            
        

    
    def get_my_user_id(self):
        """获取本地用户 ID"""
        if not hasattr(self, "my_user_id") or self.my_user_id is None:
            self.my_user_id = self._storage.get_my_user_id()
        return self.my_user_id

    def close_server_and_connections(self):
        """关闭服务器和所有客户端连接"""
        self.running = False
        for user_id in list(self.passive_connections.keys()):
            self.close_passive_connection(user_id) # 关闭所有客户端连接
        for user_id in list(self.active_connections.keys()):
            self.close_active_connection(user_id)
        self.server.close() # 关闭服务器
        print("[Close] Server and all connections closed.")

    def close_passive_connection(self, user_id):
        """关闭与特定用户的连接"""
        if user_id in self.passive_connections:
            conn = self.passive_connections.pop(user_id) # 移除连接
            conn.close() # 关闭连接
            self._storage.remove_session_key(user_id) # 删除存储的会话密钥
            print(f"[Close] Closed passive connection with user {user_id}")
    

             
    def close_active_connection(self,user_id):
        if user_id in self.active_connections:
            conn = self.active_connections.pop(user_id)
            conn.close()
            self._storage.remove_session_key(user_id)
            print(f"[Close] Closed active connection with user {user_id}")

class P2PMessage:  #定义消息格式
    HEADER_FORMAT = '!BII'  # msg_type:1B, my_user_id:4B, payload_len:4B
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    MSG_TYPE_TEXT = 1
    MSG_TYPE_KEY_EXCHANGE = 2
    MSG_TYPE_KEY_EXCHANGE_ACK = 3
    MSG_TYPE_FILE = 4
    MSG_TYPE_HEARTBEAT = 5
    MSG_TYPE_CLOSE = 6
    

    def __init__(self, msg_type: int, my_user_id: int, payload: bytes): #根据传入的消息类型，my_user_id，payload生成消息字段
        self.msg_type = msg_type
        self.my_user_id = my_user_id
        self.payload = payload

    def to_bytes(self) -> bytes: # 将消息转换为字节流
        header = struct.pack(self.HEADER_FORMAT, self.msg_type, self.my_user_id, len(self.payload)) # 打包消息头
        return header + self.payload

    @classmethod
    def from_socket(cls, conn: socket.socket): # 定义静态方法，用于从socket.socket中接收消息
        header = cls._recv_exact(conn, cls.HEADER_SIZE) # 接收消息头
        if not header:
            return None
        msg_type, my_user_id, length = struct.unpack(cls.HEADER_FORMAT, header) # 解析消息头
        payload = cls._recv_exact(conn, length) # 接收消息体
        if not payload:
            return None
        return cls(msg_type, my_user_id, payload) 

    @staticmethod
    def _recv_exact(conn: socket.socket, size): # 定义静态方法，用于接收指定大小的数据
        buf = b''
        while len(buf) < size: # 分多次接收数据，直到接收到指定大小的数据
            part = conn.recv(size - len(buf)) 
            if not part:
                return None
            buf += part
        return buf

class P2PAPI:
    def __init__(self):
        (host, port) = self._get_local_ip_port()
        self.end_point = P2PEndpoint(SecureStorage(), CryptoManager(), host, port)
        self.end_point.start_server()
        

        
    def init_session(self,user_id, peer_ip, peer_port):
        return self.end_point.establish_connection(user_id, peer_ip, peer_port)
    
    def send_message(self,user_id, msg ,type):
        if type == "text":
            return self.end_point.send_message(user_id, msg)
        elif type == "file":
            return self.end_point.send_file(user_id, msg)
        else:
            raise Exception("Invalid message type")
        
    def exit_session(self,user_id):
        self.end_point.close_passive_connection(user_id)
        self.end_point.close_active_connection(user_id)

    def close(self):
        self.end_point.close_server_and_connections()
        

    def _get_local_ip_port(self):
        try:
            # 获取本地IP（使用UDP socket.socket）
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
                udp_socket.connect(('8.8.8.8', 80))  # 连接到Google DNS
                ip = udp_socket.getsockname()[0]
            
            # 获取随机可用端口（使用新的TCP socket.socket）
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
                tcp_socket.bind(('', 0))  # 绑定到任意IP和随机端口
                port = tcp_socket.getsockname()[1]
            udp_socket.close()
            tcp_socket.close()
            print(f"获取IP和端口成功: {ip}:{port}")
            return (ip, port)
        except Exception as e:
            print(f"获取IP和端口失败: {e}")
            return (None, None)  # fallback

    def get_crypto_manager(self):
        return self.end_point._crypto_manager

    def get_storage(self):
        return self.end_point._storage
        
if __name__ == "__main__":
    api = P2PAPI()
    api.get_storage().save_my_user_id(2)
    #ip = input("请输入IP：")
    #port = (int)(input("请输入端口："))
    ip = "10.21.211.249"
    port = 60199
    public_key, private_key = api.get_crypto_manager().get_my_keys()
    api.get_storage().save_key(1, public_key)
    api.init_session(1, ip, port)
    
    

    
    
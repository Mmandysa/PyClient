import socket
import threading
import struct
import base64
from concurrent.futures import ThreadPoolExecutor
from PyQt6.QtCore import QObject, pyqtSignal

# ================= 简化加解密 =================
class SimpleCrypto:
    def aes_encrypt_auto(self, plaintext, key):
        return {"encrypted_message": base64.b64encode(plaintext.encode()).decode()}

    def aes_decrypt_auto(self, encrypted, key, msg_type):
        return base64.b64decode(encrypted.encode()).decode()

# ================= 消息结构 =================
class P2PMessage:
    HEADER_FORMAT = '!BII'
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
    MSG_TYPE_TEXT = 1

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

# ================= P2P 主体类 =================
class P2PEndpoint(QObject):
    message_received = pyqtSignal(int, str)  # sender_id, text

    def __init__(self, user_id, host, port):
        super().__init__()
        self.my_id = user_id
        self.host = host
        self.port = port
        self.crypto = SimpleCrypto()
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(5)
        self.connections = {}
        self.session_keys = {}
        self.running = True
        self.thread_handler = ThreadPoolExecutor(max_workers=10)

    def start(self):
        threading.Thread(target=self.accept_loop, daemon=True).start()

    def stop(self):
        self.running = False
        self.server.close()
        for conn in self.connections.values():
            conn.close()
        self.thread_handler.shutdown(wait=True)

    def accept_loop(self):
        while self.running:
            try:
                conn, addr = self.server.accept()
                self.thread_handler.submit(self.handle_connection, conn)
            except:
                break

    def handle_connection(self, conn):
        while self.running:
            try:
                msg = P2PMessage.from_socket(conn)
                if not msg:
                    break
                self.connections[msg.my_user_id] = conn
                self.session_keys[msg.my_user_id] = b"dummy_key"
                self.handle_data(msg)
            except:
                break

    def handle_data(self, msg: P2PMessage):
        sender = msg.my_user_id
        if msg.msg_type == P2PMessage.MSG_TYPE_TEXT:
            session_key = self.get_session_key(sender)
            if session_key:
                encrypted = msg.payload.decode()
                text = self.crypto.aes_decrypt_auto(encrypted, session_key, "str")
                self.message_received.emit(sender, text)

    def connect(self, peer_id, ip, port, peer_pubkey):
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect((ip, port))
            self.connections[peer_id] = conn
            self.session_keys[peer_id] = b"dummy_key"
        except Exception as e:
            print(f"连接失败: {e}")

    def send(self, user_id, message):
        session_key = self.get_session_key(user_id)
        if not session_key:
            print(f"⚠️ 无法发送，用户 {user_id} 的会话密钥不存在")
            return
        encrypted = self.crypto.aes_encrypt_auto(message, session_key)["encrypted_message"]
        payload = encrypted.encode()
        msg = P2PMessage(P2PMessage.MSG_TYPE_TEXT, self.my_id, payload)
        conn = self.connections.get(user_id)
        if conn:
            try:
                conn.sendall(msg.to_bytes())
            except Exception as e:
                print(f"❌ 消息发送失败: {e}")

    def get_session_key(self, user_id):
        return self.session_keys.get(user_id, None)

# ================= 对外接口 =================
class P2PAPI(QObject):
    def __init__(self, user_id, host, port):
        super().__init__()
        self.endpoint = P2PEndpoint(user_id, host, port)
        self.endpoint.message_received.connect(self._handle_message)
        self._external_callback = None
        self.endpoint.start()

    def on_message(self, callback):
        self._external_callback = callback

    def _handle_message(self, sender, text):
        if self._external_callback:
            self._external_callback(sender, text)

    def connect(self, peer_id, ip, port, peer_pubkey):
        self.endpoint.connect(peer_id, ip, port, peer_pubkey)

    def send(self, user_id, message):
        self.endpoint.send(user_id, message)

    def stop(self):
        self.endpoint.stop()

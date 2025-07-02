import base64
import os
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Util.Padding import pad, unpad
from panel.Singleton import Singleton


def is_base64(s: str) -> bool:
    try:
        return base64.b64encode(base64.b64decode(s)) == s.encode()
    except Exception:
        return False


class CryptoManager(Singleton):
    def __init__(self):
        if os.path.exists("rsa_key.pem"):
            with open("rsa_key.pem", "rb") as f:
                self.rsa_key = RSA.import_key(f.read())
            self.private_key_str = base64.b64encode(self.rsa_key.export_key()).decode()
            self.public_key_str = base64.b64encode(self.rsa_key.publickey().export_key()).decode()
            return
        else:
            self.rsa_key = RSA.generate(2048)
            self.private_key_str = base64.b64encode(self.rsa_key.export_key()).decode()
            self.public_key_str = base64.b64encode(self.rsa_key.publickey().export_key()).decode()
            with open("rsa_key.pem", "wb") as f:
                f.write(self.rsa_key.export_key())


    def get_my_keys(self):
        return self.public_key_str, self.private_key_str

    def encrypt_session_key_for_friend(self, friend_public_key_str: str):
        import os, base64
        from Crypto.PublicKey import RSA
        from Crypto.Cipher import PKCS1_OAEP

        print("[DEBUG] Starting session key encryption for friend")

        try:
            session_key = os.urandom(16)
            print(f"[DEBUG] Generated random session key (raw bytes): {session_key}")
            print(f"[DEBUG] Generated random session key (base64): {base64.b64encode(session_key).decode()}")

            friend_key_bytes = base64.b64decode(friend_public_key_str)
            print(f"[DEBUG] Decoded friend's public key from base64, length: {len(friend_key_bytes)} bytes")

            friend_key = RSA.import_key(friend_key_bytes)
            print(f"[DEBUG] Imported friend's RSA public key: {friend_key.export_key().decode('utf-8').splitlines()[0]} ...")

            cipher_rsa = PKCS1_OAEP.new(friend_key)
            encrypted_key = cipher_rsa.encrypt(session_key)
            print(f"[DEBUG] Encrypted session key length: {len(encrypted_key)} bytes")

            encrypted_key_b64 = base64.b64encode(encrypted_key).decode()
            session_key_b64 = base64.b64encode(session_key).decode()

            print(f"[DEBUG] Encrypted session key (base64): {encrypted_key_b64}")

            return encrypted_key_b64, session_key_b64

        except Exception as e:
            print(f"[ERROR] Failed to encrypt session key: {e}")
            raise


    def decrypt_session_key(self, encrypted_key_str: str, private_key_str: str):
        encrypted_key = base64.b64decode(encrypted_key_str)
        private_key = RSA.import_key(base64.b64decode(private_key_str))
        cipher_rsa = PKCS1_OAEP.new(private_key)
        session_key = cipher_rsa.decrypt(encrypted_key)
        return base64.b64encode(session_key).decode()

    def aes_decrypt_auto(self, cipher_b64_with_type: str, base64_key_str: str):
        """
        自动处理解密，返回原始内容（str 或 base64 或 bytes）
        """
        if ':' not in cipher_b64_with_type:
            raise ValueError("密文格式错误，缺少类型信息")

        content_type, cipher_b64 = cipher_b64_with_type.split(':', 1)

        raw = base64.b64decode(cipher_b64)
        key = base64.b64decode(base64_key_str)
        iv = raw[:16]
        ciphertext = raw[16:]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)

        if content_type == 'str':
            return plaintext.decode('utf-8')
        elif content_type == 'base64':
            return base64.b64encode(plaintext).decode()
        elif content_type == 'bytes':
            return plaintext
        else:
            raise ValueError("未知的内容类型")

    def aes_encrypt_auto(self, content, base64_key_str: str):
        """
        自动处理 str / bytes / base64 编码输入，加密并返回 base64(IV + ciphertext)
        """
        key = base64.b64decode(base64_key_str)
        iv = os.urandom(16)
        cipher = AES.new(key, AES.MODE_CBC, iv)

        # 🧠 自动识别并处理输入内容
        if isinstance(content, bytes):
            raw = content
            content_type = 'bytes'
        elif isinstance(content, str):
            if is_base64(content):
                raw = base64.b64decode(content)
                content_type = 'base64'
            else:
                raw = content.encode('utf-8')
                content_type = 'str'
        else:
            raise TypeError("内容必须是 str 或 bytes")

        ciphertext = cipher.encrypt(pad(raw, AES.block_size))
        result = base64.b64encode(iv + ciphertext).decode()
        return f"{content_type}:{result}"
    
    

def test_with_plain_text():
    print("🧪 测试原文输入加密")
    cm = CryptoManager()
    pub, pri = cm.get_my_keys()

    encrypted_session_key, session_key = cm.encrypt_session_key_for_friend(pub)
    print("🔐 原始 AES session_key:", session_key)

    msg = "你好，世界！这是原文消息。"
    encrypted = cm.aes_encrypt_auto(msg, session_key)
    print("📦 加密后:", encrypted)

    decrypted = cm.aes_decrypt_auto(encrypted, session_key)
    print("🔓 解密后:", decrypted)
    assert decrypted == msg


def test_with_base64_input():
    print("🧪 测试 base64 输入加密")
    cm = CryptoManager()
    pub, pri = cm.get_my_keys()

    encrypted_session_key, session_key = cm.encrypt_session_key_for_friend(pub)

    raw_bytes = b"\xff\xd8\xff\xe0"  # 模拟图片或二进制内容（非 UTF-8）
    base64_input = base64.b64encode(raw_bytes).decode()
    print("📄 模拟 base64 输入:", base64_input)

    encrypted = cm.aes_encrypt_auto(base64_input, session_key)
    print("📦 加密后:", encrypted)

    decrypted = cm.aes_decrypt_auto(encrypted, session_key)
    print("🔓 解密后 (仍是 base64):", decrypted)
    assert decrypted == base64_input

def test_with_bytes_input():
    
    print("🧪 测试 bytes 输入加密")
    cm = CryptoManager()
    pub, pri = cm.get_my_keys()
    _, session_key = cm.encrypt_session_key_for_friend(pub)

    raw_bytes = b"\x00\x01\x02\x03hello\xff\xfe"
    print("📄 原始字节:", raw_bytes)

    encrypted = cm.aes_encrypt_auto(raw_bytes, session_key)
    print("📦 加密后:", encrypted)

    decrypted = cm.aes_decrypt_auto(encrypted, session_key)
    print("🔓 解密后:", decrypted)
    assert decrypted == raw_bytes
    
def remove_pem_file():
    if __name__ == "__main__":
        if os.path.exists("rsa_key.pem"):
            os.remove("rsa_key.pem")

if __name__ == "__main__":
    test_with_plain_text()
    print("\n" + "=" * 60 + "\n")
    test_with_base64_input()
    print("\n" + "=" * 60 + "\n")
    test_with_bytes_input()
    remove_pem_file()

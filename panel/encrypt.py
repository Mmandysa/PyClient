import os
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Util.Padding import pad, unpad
from panel.Singleton import Singleton


def b64encode(data: bytes) -> str:
    return base64.b64encode(data).decode('ascii')


def b64decode(data: str) -> bytes:
    return base64.b64decode(data)


def _check_aes_key_len(key: bytes):
    if len(key) not in (16, 24, 32):
        raise ValueError(f"AES key length must be 16/24/32 bytes, got {len(key)}")


class CryptoManager(Singleton):
    def __init__(self):
        if os.path.exists("rsa_key.pem"):
            with open("rsa_key.pem", "rb") as f:
                self.rsa_key = RSA.import_key(f.read())
        else:
            self.rsa_key = RSA.generate(2048)
            with open("rsa_key.pem", "wb") as f:
                f.write(self.rsa_key.export_key())

        # 公私钥均为 base64(PEM bytes) ascii str
        self.private_key_str = b64encode(self.rsa_key.export_key())
        self.public_key_str = b64encode(self.rsa_key.publickey().export_key())

    def get_my_keys(self):
        """返回 (public_key_base64_str, private_key_base64_str)"""
        return self.public_key_str, self.private_key_str

    def encrypt_session_key_for_friend(self, friend_public_key_b64: str):
        """
        用好友公钥RSA加密随机生成的AES会话密钥
        返回 dict:
          {
            "encrypted_key": base64 string, # RSA加密AES密钥
            "session_key": base64 string    # AES原始密钥，调试/对比用
          }
        """
        session_key = os.urandom(16)
        friend_key = RSA.import_key(b64decode(friend_public_key_b64))
        cipher_rsa = PKCS1_OAEP.new(friend_key)
        encrypted_key = cipher_rsa.encrypt(session_key)

        return {
            "encrypted_key": b64encode(encrypted_key),
            "session_key": b64encode(session_key)
        }

    def decrypt_session_key(self, encrypted_key, private_key_b64: str = None,message_type="str"):
        """
        用本地私钥RSA解密加密的AES密钥，返回 base64编码的原始AES密钥
        """
        
        if private_key_b64 is None:
            private_key_b64 = self.private_key_str
            
        if message_type == "str":
            encrypted_key_bytes = b64decode(encrypted_key)
        
        elif message_type ==  "bytes":
            encrypted_key_bytes = encrypted_key

            
        private_key_bytes = b64decode(private_key_b64)
        private_key = RSA.import_key(private_key_bytes)    
        cipher_rsa = PKCS1_OAEP.new(private_key)
        try:
            session_key_bytes = cipher_rsa.decrypt(encrypted_key_bytes)
        except Exception as e:
            print("[DEBUG] encrypted_key_bytes:", encrypted_key_bytes)
            print("[DEBUG] type(encrypted_key_bytes):", type(encrypted_key_bytes))
            print("[DEBUG] len(encrypted_key_bytes):", len(encrypted_key_bytes))
            print("[ERROR] Failed to decrypt session key:", e)
        
        return b64encode(session_key_bytes)


    def aes_encrypt_auto(self, content: str, key_b64: str):
        """
        使用 AES CBC + PKCS7 填充加密字符串
        返回 dict:
          {
            "encrypted_message": base64 string,
            "message_type": "str"
          }
        """
        key = b64decode(key_b64)
        _check_aes_key_len(key)

        iv = os.urandom(16)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        ciphertext = cipher.encrypt(pad(content.encode('utf-8'), AES.block_size))
        return {
            "encrypted_message": b64encode(iv + ciphertext),
            "message_type": "str"
        }

    def aes_decrypt_auto(self, encrypted_message_b64: str, key_b64: str, message_type: str):
        """
        解密 AES CBC 加密消息，返回字符串（通常是明文）
        """
        key = b64decode(key_b64)
        _check_aes_key_len(key)

        raw = b64decode(encrypted_message_b64)
        iv, ciphertext = raw[:16], raw[16:]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)

        if message_type == 'str':
            return plaintext.decode('utf-8')
        elif message_type == 'base64':
            return b64encode(plaintext)
        elif message_type == 'bytes':
            return plaintext
        else:
            raise ValueError(f"未知 message_type: {message_type}")

def test_p2p_communication():
    alice = CryptoManager()
    bob = CryptoManager()

    # Alice、Bob 各自拿公钥（base64字符串）
    alice_pub = alice.public_key_str
    bob_pub = bob.public_key_str

    print("[Alice] 公钥:", alice_pub[:40] + "...")
    print("[Bob] 公钥:", bob_pub[:40] + "...")

    # Bob 用 Alice 公钥生成 AES session key，并加密
    res = bob.encrypt_session_key_for_friend(alice_pub)
    encrypted_key = res['encrypted_key']
    session_key = res['session_key']
    print("[Bob] 生成并加密的 AES 会话密钥:", session_key)

    # Alice 用自己的私钥解密 AES session key
    decrypted_session_key = alice.decrypt_session_key(encrypted_key)
    print("[Alice] 解密出的 AES 会话密钥:", decrypted_session_key)
    assert decrypted_session_key == session_key

    # Bob 用 AES 会话密钥加密消息给 Alice
    plaintext = "Hello Alice, this is Bob."
    encrypted_msg_obj = bob.aes_encrypt_auto(plaintext, session_key)
    encrypted_msg = encrypted_msg_obj['encrypted_message']
    message_type = encrypted_msg_obj['message_type']
    print("[Bob] AES加密消息:", encrypted_msg)

    # Alice 解密消息
    decrypted_msg = alice.aes_decrypt_auto(encrypted_msg, decrypted_session_key, message_type)
    print("[Alice] 解密消息:", decrypted_msg)
    assert decrypted_msg == plaintext

    print("✅ P2P通信测试通过！")


if __name__ == "__main__":
    test_p2p_communication()


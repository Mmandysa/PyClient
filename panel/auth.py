from settings import BaseUrl
from panel.encrypt import *
from panel.storage import SecureStorage
import requests

Url = f"{BaseUrl}/api/auth"

def register(username, password,email):
    cryptoManager = CryptoManager()
    public_key, private_key = cryptoManager.get_my_keys()
    
    url = f"{Url}/register/"
    response = requests.post(
        url,
        json={
            "username": username,
            "password": sha256(password),
            "email": email,
            "userpk": public_key
        }
    )
    data = response.json()
    user_id = data.get("user_id")
    
    storage = SecureStorage()
    storage.save_my_user_id(user_id)
    return data

def login(type,username, password):
    url = f"{Url}/login/"
    if type == "username":
        response = requests.post(url, json={
            "username": username,
            "password": sha256(password)
        })
    elif type == "email":
        response = requests.post(url, json={
            "email": username,
            "password": sha256(password)
        })
    else:
        return {"error": "参数错误", "message": "type必须是'username'或'email'"}
    
    token = response.json().get("token")
    if token:
        storage = SecureStorage()
        user_id = storage.get_my_user_id()
        storage.save_token(user_id, token)
    
    return response.json()

def logout():
    url = f"{Url}/logout/"
    token = SecureStorage().get_token(SecureStorage().get_my_user_id())
    headers = {"Authorization": f"Token {token}"}
    response = requests.post(
        url,
        headers=headers,
    )    
    print(response.json())
    return response.json()

def sha256(password):
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

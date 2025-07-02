from settings import BaseUrl
import requests
from panel.encrypt import *
from panel.storage import SecureStorage
import logging

logging.basicConfig(level=logging.DEBUG)

Url = f"{BaseUrl}/api/contact"
def getlist():
    url = f"{Url}/getlist/"
    token = SecureStorage().get_token(SecureStorage().get_my_user_id())
    headers = {"Authorization": f"Token {token}"}
    response = requests.get(url, headers=headers)
    data = response.json()
    print(data)

    if response.status_code == 200:
        friends = data.get("friends", [])
        try:
            for friend in friends:                       # 这些字段都是字典。                                      
                user_id = friend.get("userid")
                nickname = friend.get("nickname")
                username = friend.get("username")
                user_pk = friend.get("userpk")
                user_status = friend.get("user_status")
                user_ipaddr = friend.get("user_ipaddr")
                user_port = friend.get("user_port")

                storage = SecureStorage()
                storage.save_key(user_id, user_pk)

                
        except Exception as e:
            return {"error": "获取好友列表失败", "message": str(e)}
        
        # 这里是返回值
        
        return {"message": "获取好友列表成功", "friends": friends} # friends 是一个 列表，单元是字典，包括以上的字段
    else:
        return {"error": "获取好友列表失败", "message": data.get("message", "")}

def addfriend(type,str):
    token = SecureStorage().get_token(SecureStorage().get_my_user_id())
    headers = {"Authorization": f"Token {token}"}
    if type == "username":
        response = requests.post(f"{Url}/addfriend/", headers=headers, json={"username": str})
    elif type == "email":
        response = requests.post(f"{Url}/addfriend/", headers=headers, json={"email": str})
    else:
        return {"error": "参数错误", "message": "type必须是'username'或'email'"}
    return response.json()

def deletefriend(type,str):
    token = SecureStorage().get_token(SecureStorage().get_my_user_id())
    headers = {"Authorization": f"Token {token}"}
    if type == "username":
        response = requests.post(f"{Url}/deletefriend/", headers=headers, json={"username": str})
    elif type == "email":
        response = requests.post(f"{Url}/deletefriend/", headers=headers, json={"email": str})
    else:
        return {"error": "参数错误", "message": "type必须是'username'或'email'"}
    return response.json()

def updateinfo(nickname):
    token = SecureStorage().get_token(SecureStorage().get_my_user_id())
    headers = {"Authorization": f"Token {token}"}
    response = requests.post(f"{Url}/updateinfo/", headers=headers, json={"nickname": nickname})
    return response.json()

def create_friend_request(username):
    token = SecureStorage().get_token(SecureStorage().get_my_user_id())
    headers = {"Authorization": f"Token {token}"}
    response = requests.post(
        f"{Url}/createfriendrequest/",
        headers=headers,
        json={"username": username}
    )
    data = response.json()
    
    if response.status_code == 200:
        return data
    else:
        return {"error": "创建好友申请失败", "message": data}

def deal_friend_request(username, action):
    token = SecureStorage().get_token(SecureStorage().get_my_user_id())
    headers = {"Authorization": f"Token {token}"}
    response = requests.post(
        f"{Url}/dealfriendrequest/",
        headers=headers,
        json={
            "username": username,
            "action": action
        }
    )
    data = response.json()
    
    if response.status_code == 200:
        return data
    else:
        return {"error": "好友申请处理失败", "message": data}
        

def show_friend_request_list():
    headers = {"Authorization": f"Token {SecureStorage().get_token(SecureStorage().get_my_user_id())}"}
    response = requests.get(f"{Url}/showfriendrequestlist/", headers=headers)
    data = response.json()
    print(data)
    
    if response.status_code == 200:
        return data
    else:
        return {"error": "获取好友申请列表失败", "message": data}


def show_self_friend_request_list():
    headers = {"Authorization": f"Token {SecureStorage().get_token(SecureStorage().get_my_user_id())}"}
    response = requests.get(f"{Url}/showselfrequestlist/", headers=headers)
    data = response.json()
    
    if response.status_code == 200:
        return data
    else:
        return {"error": "获取主动发起的好友申请列表失败", "message": data}


def get_user_profile():
    """获取当前用户个人资料"""
    token = SecureStorage().get_token(SecureStorage().get_my_user_id())
    headers = {"Authorization": f"Token {token}"}
    
    profile_url = f"{Url}/profile/"  # <-- 请根据后端实际接口调整
    response = requests.get(profile_url, headers=headers)
    data = response.json()

    if response.status_code == 200:
        return {
            "username": data.get("username", ""),
            "nickname": data.get("nickname", ""),
            "email": data.get("email", "")
        }
    else:
        return {
            "error": "获取用户资料失败",
            "message": data.get("message", "")
        }

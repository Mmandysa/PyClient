#from settings import BaseUrl
import requests
from .encrypt import *
from .storage import SecureStorage

Url = "baseurlconnect"
def getlist():
    response={
        "message": "获取好友列表成功",
        "friends": [
            {
                "user_id": "user123",
                "user_nickname": "张三",
                "user_pk": "public_key_abc123",
                "user_status": "online",
                "user_ipaddr": "192.168.1.100",
                "user_port": 8080
            },
            {
                "user_id": "user456",
                "user_nickname": "李四",
                "user_pk": "public_key_def456",
                "user_status": "offline",
                "user_ipaddr": "10.0.0.15",
                "user_port": 9090
            },
            {
                "user_id": "user789",
                "user_nickname": "王五",
                "user_pk": "public_key_ghi789",
                "user_status": "away",
                "user_ipaddr": "172.16.0.20",
                "user_port": 7070
            }
        ]
    }
    return response
    response = requests.get(f"{Url}/getlist")
    data = response.json()

    if response.status_code == 200:
        friends = data.get("friends", [])
        try:
            for friend in friends:                              # 这些字段都是字典。                                      
                user_id = friend.get("user_id")
                user_nickname = friend.get("user_nickname")
                user_pk = friend.get("user_pk")
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

def addfriend(user_id):
    response = requests.post(f"{Url}/addfriend", json={"user_id": user_id})
    return response.json()

def deletefriend(user_id):
    response = requests.post(f"{Url}/deletefriend", json={"user_id": user_id})
    return response.json()

def updateinfo(user_nickname):
    response = requests.post(f"{Url}/updateinfo", json={"user_nickname": user_nickname})
    return response.json()
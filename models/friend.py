class Friend:
    def __init__(self,user_id,username,nickname, status,ip,port):
        self.nickname =nickname
        self.username = username
        self.user_id =user_id                                                  
        self.user_ipaddr = ip
        self.user_port = port
        if status=="online":
            self.online=True
        else:
            self.online=False
    
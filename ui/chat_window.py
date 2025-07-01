import sys
from pathlib import Path
from datetime import datetime
import os
from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QListWidget, QListWidgetItem, 
    QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QLabel, QSizePolicy, QApplication,QDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QFont
from panel.connect import getlist,addfriend,deletefriend,updateinfo
from widgets.profile_widget import ProfileDialog

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from models.friend import Friend
from widgets.avatar_label import AvatarLabel
from widgets.chat_bubble import ChatBubble
from widgets.friend_item import FriendItemWidget
from widgets.friend_list_header import FriendListHeader
from widgets.profile_widget import ProfileWidget
from widgets.chat_input import ChatInputWidget

class ChatWindow(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.current_user = username  # 使用current_user替代username
        self.friends = []  # 好友列表
        self.friends_list = []  # 好友用户名列表
        self.current_friend = None
        self.setWindowTitle(f"我的QQ - {username}")
        self.setGeometry(100, 100, 800, 600)
        
        # 主分割布局
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        # 左侧好友列表区域
        self.create_friend_list()
        # 右侧聊天区域
        self.create_chat_area()
        # 设置主窗口中心部件
        self.setCentralWidget(self.splitter)
        # 设置初始分割比例
        self.splitter.setSizes([200, 600])
        # 底部状态栏
        self.statusBar().showMessage("状态: 已连接")
        
        # 设置聊天区域和输入区域的比例为7:3
        self.chat_layout.setStretch(1, 3)
        
        # 初始化好友列表
        self.init_friends()

        # 连接头像点击事件
        self.friend_list_header.avatar_clicked.connect(
            lambda: self.show_profile(self.current_user, is_current_user=True)
        )

        # 用户数据初始化
        self.user_data = {
            "username": self.current_user,
            "nickname": self.current_user,  
            "email": f"{self.current_user}@example.com"
        }
        self.friends_data = {} 
    
    def create_friend_list(self):
        """创建好友列表区域"""
        # 左侧整体容器
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_widget.setLayout(left_layout)
        
        # 添加顶部头像和搜索框
        self.friend_list_header = FriendListHeader(self.current_user)
        left_layout.addWidget(self.friend_list_header)
        
        # 好友列表
        self.friend_list = QListWidget()
        self.friend_list.setStyleSheet("""
            QListWidget {
                border: none;
                background: #f5f5f5;
                font-family: Microsoft YaHei;
            }
            QListWidget::item {
                height: 50px;
                border-bottom: 1px solid #e0e0e0;
            }
            QListWidget::item:hover {
                background: #e6e6e6;
            }
            QListWidget::item:selected {
                background: #d6d6d6;
            }
        """)
        self.friend_list.itemClicked.connect(self.on_friend_selected)
        
        left_layout.addWidget(self.friend_list)
        self.splitter.addWidget(left_widget)
    
    def create_chat_area(self):
        """创建聊天区域"""
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout()
        self.chat_widget.setLayout(self.chat_layout)
        
        # 聊天标题
        self.chat_title = QLabel("开始聊天...")
        self.chat_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chat_title.setStyleSheet("""
            QLabel {
                font-family: Microsoft YaHei;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                border-bottom: 1px solid #e0e0e0;
                background: white;
            }
        """)
        self.chat_layout.addWidget(self.chat_title)
        
        # 聊天内容区域
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet("background: #f5f5f5; border: none;")
        
        self.chat_content = QWidget()
        self.chat_content_layout = QVBoxLayout()
        self.chat_content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_content_layout.setContentsMargins(20, 20, 20, 20)
        self.chat_content_layout.setSpacing(10)
        self.chat_content.setLayout(self.chat_content_layout)
        
        # 添加弹性空间使内容顶部对齐
        self.chat_content_layout.addStretch()
        
        self.chat_scroll.setWidget(self.chat_content)
        self.chat_layout.addWidget(self.chat_scroll)
        
        # 输入区域
        self.create_input_area()
        
        self.splitter.addWidget(self.chat_widget)
    
    def create_input_area(self):
        """替换为封装的输入组件"""
        self.input_area = ChatInputWidget()
        self.input_area.send_message_signal.connect(self.send_message_from_input)
        self.input_area.send_file_signal.connect(self.handle_file_selected)  # 新增
        self.chat_layout.addWidget(self.input_area)

    def handle_file_selected(self, file_path):
        """处理选择的文件"""
        if self.current_friend:
            file_name = os.path.basename(file_path)
            self.append_message(self.username, f"[文件] {file_name}", True)
            # 这里可以添加实际的文件发送逻辑
    
    def init_friends(self):
        """初始化好友列表数据"""
        # 调用API获取好友列表
        response = getlist()
        
        # 清空当前列表
        self.friends.clear()
        self.friend_list.clear()
        self.friends_list = []
        
        # 检查API响应是否成功
        if "error" in response:
            print(f"[错误] 获取好友列表失败: {response['error']}")
            QMessageBox.warning(self, "错误", "获取好友列表失败")
            return
        
        # 创建Friend对象并添加到列表
        for friend_data in response.get("friends", []):
            try:
                friend = Friend(
                    user_id=friend_data["user_id"],
                    username=friend_data["user_id"],
                    nickname=friend_data["user_nickname"],
                    status=friend_data["user_status"],
                    ip=friend_data["user_ipaddr"],
                    port=friend_data["user_port"],
                )
                self.friends.append(friend)
                self.friends_list.append(friend.username)
                self.add_friend_item(friend)
            except KeyError as e:
                print(f"[错误] 好友数据字段缺失: {e}")
                continue
    
    def add_friend_item(self, friend):
        """添加好友到列表"""
        item = QListWidgetItem()
        item.setSizeHint(QSize(200, 50))
        
        widget = FriendItemWidget(friend)
        self.friend_list.addItem(item)
        self.friend_list.setItemWidget(item, widget)
    
    def on_friend_selected(self, item):
        """好友选择事件处理"""
        index = self.friend_list.row(item)
        self.current_friend = self.friends[index]
        self.chat_title.setText(f"与 {self.current_friend.nickname} 聊天中")
        
        # 加载历史消息 (这里可以添加实际加载逻辑)
        # self.load_chat_history(self.current_friend)
    
    def clear_chat_area(self):
        """清空聊天区域"""
        # 保留最后的弹性空间
        while self.chat_content_layout.count() > 1:
            item = self.chat_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def send_message_from_input(self, message):
        """由输入组件触发的发送处理"""
        if message and self.current_friend:
# <<<<<<< HEAD
#             self.append_message(self.username, message, True)

#             if self.current_friend.username == "张三":
#                 QTimer.singleShot(1000, lambda: self.append_message(
#                     self.current_friend.username,
#                     "自动回复: 你好，我现在不在线，稍后回复你",
#                     False
#                 ))

# =======
            #调用api发送消息
            # 添加自己的消息
            self.append_message(self.current_user, message, True)
            
            # # 模拟自动回复 (如果是张三)
            # if self.current_friend.nickname == "张三":
            #     QTimer.singleShot(1000, lambda: self.append_message(
            #         self.current_friend.username,
            #         "自动回复: 你好，我现在不在线，稍后回复你",
            #         False
            #     ))
# >>>>>>> 0c39141b438e53d3f630a469de325f4e5b6b8182
    
    def append_message(self, sender, message, is_me):
        """添加消息到聊天区域"""
        # 时间标签
        time_label = QLabel(datetime.now().strftime("%H:%M"))
        time_label.setStyleSheet("""
            QLabel {
                font-family: Microsoft YaHei;
                font-size: 10px;
                color: gray;
                background: transparent;
            }
        """)
        time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 消息容器
        message_widget = QWidget()
        message_widget.setStyleSheet("background: transparent;")
        message_layout = QHBoxLayout()
        message_widget.setLayout(message_layout)
        
        # 头像
        avatar = AvatarLabel(sender, size=40)
        avatar.clicked.connect(lambda *args, u=sender, m=is_me: self.show_profile(u, m))
        
        # 聊天气泡
        bubble = ChatBubble(message, is_me)
        
        # 根据发送者决定布局
        if is_me:
            # 自己的消息靠右
            message_layout.addStretch()
            message_layout.addWidget(bubble)
            message_layout.addWidget(avatar)
        else:
            # 对方的消息靠左
            message_layout.addWidget(avatar)
            message_layout.addWidget(bubble)
            message_layout.addStretch()
        
        # 添加时间到聊天区域
        self.chat_content_layout.insertWidget(
            self.chat_content_layout.count() - 1,
            time_label
        )
        self.chat_content_layout.insertWidget(
            self.chat_content_layout.count() - 1,
            message_widget
        )
        
        # 滚动到底部
        self.scroll_to_bottom()

    def show_profile(self, username, is_current_user=False):
        """显示用户资料对话框"""
        if is_current_user:
            # 当前用户资料
            profile_data = {
                'username': self.current_user,
                'nickname': self.user_data.get('nickname', self.current_user),
                'email': self.user_data.get('email', ''),
                'friends': self.friends_list  # 好友列表
            }
        else:
            # 其他用户资料
            if username not in self.friends_data:
                # 如果数据不存在，初始化默认数据
                self.friends_data[username] = {
                    "username": username,
                    "nickname": f"{username}的昵称",
                    "email": f"{username}@example.com",
                    "friends": []
                }
            profile_data = self.friends_data[username]
        
        # 创建并显示对话框
        profile_dialog = ProfileDialog(
            user_data=profile_data,
            current_user=self.current_user if is_current_user else None,
            parent=self
        )
        
        # 连接信号
        if not is_current_user:
            profile_dialog.profile_widget.add_friend_requested.connect(
                lambda: self.send_friend_request(username))
            profile_dialog.profile_widget.send_message_requested.connect(
                lambda: self.start_private_chat(username))
        else:
            # 当前用户资料更新信号
            profile_dialog.profile_widget.profile_updated.connect(
                self.update_profile)
        
        profile_dialog.exec()

    def update_profile(self, updated_data):
        """更新个人资料"""
        try:
            valid_data = {
                'nickname': updated_data.get('nickname', self.user_data.get('nickname'))
            }
            
            # 调用API更新资料
            response = updateinfo(self.current_user, valid_data)
            
            if response.get('success'):
                # 更新本地数据
                self.user_data['nickname'] = valid_data['nickname']
                
                # 更新UI显示
                if hasattr(self, 'user_name_label'):
                    self.user_name_label.setText(valid_data['nickname'])
                
                # 更新好友列表中自己的昵称
                if self.current_user in self.friends_data:
                    self.friends_data[self.current_user]['nickname'] = valid_data['nickname']
                
                QMessageBox.information(self, "成功", "昵称更新成功！")
            else:
                QMessageBox.warning(self, "错误", response.get('message', '更新昵称失败'))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新资料时出错: {str(e)}")
        
    def scroll_to_bottom(self):
        """滚动聊天区域到底部"""
        scrollbar = self.chat_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        # 确保完全滚动到底部
        QTimer.singleShot(50, lambda: scrollbar.setValue(scrollbar.maximum()))



if __name__ == "__main__":
    # 测试用代码
    app = QApplication(sys.argv)
    window = ChatWindow("测试用户")
    window.show()
    sys.exit(app.exec())
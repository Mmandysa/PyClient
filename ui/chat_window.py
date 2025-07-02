import sys
from pathlib import Path
from datetime import datetime
import os
from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QListWidget, QListWidgetItem, 
    QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QLabel, QSizePolicy, QApplication, QDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from panel.connect import getlist, addfriend, deletefriend, updateinfo, get_user_profile
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
        self.current_user = username
        self.friends = []  # 好友列表
        self.friends_list = []  # 好友用户名列表
        self.current_friend = None
        self.setWindowTitle(f"我的QQ - {username}")
        self.setGeometry(100, 100, 800, 600)

        # 用户数据初始化
        self.user_data = get_user_profile()
        if "error" in self.user_data:
            QMessageBox.critical(self, "错误", self.user_data["message"])
            self.user_data = {
                "username": self.current_user,
                "nickname": "",  # fallback
                "email": ""
            }
        
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
        # 连接好友列表更新信号
        self.friend_list_header.need_update_friends.connect(self.init_friends)
    
    def create_friend_list(self):
        """创建好友列表区域"""
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_widget.setLayout(left_layout)
        
        # 添加顶部头像和搜索框
        self.friend_list_header = FriendListHeader(self.user_data.get("nickname", self.current_user))
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
        
        self.chat_content_layout.addStretch()
        self.chat_scroll.setWidget(self.chat_content)
        self.chat_layout.addWidget(self.chat_scroll)
        
        # 输入区域
        self.create_input_area()
        
        self.splitter.addWidget(self.chat_widget)
    
    def create_input_area(self):
        """创建输入区域"""
        self.input_area = ChatInputWidget()
        self.input_area.send_message_signal.connect(self.send_message_from_input)
        self.input_area.send_file_signal.connect(self.handle_file_selected)
        self.chat_layout.addWidget(self.input_area)

    def handle_file_selected(self, file_path):
        """处理选择的文件"""
        if self.current_friend:
            file_name = os.path.basename(file_path)
            self.append_message(self.username, f"[文件] {file_name}", True)

    def init_friends(self):
        if not hasattr(self, "friends_data"):
            self.friends_data = {}
        """初始化好友列表数据"""
        try:
            response = getlist()
            
            self.friends.clear()
            self.friend_list.clear()
            self.friends_list = []
            
            if "error" in response:
                QMessageBox.warning(self, "错误", "获取好友列表失败")
                return
            
            for friend_data in response.get("friends", []):
                try:
                    friend = Friend(
                        user_id=friend_data.get("userid"),
                        username=friend_data.get("username"),
                        nickname=friend_data.get("nickname", ""),
                        status=friend_data.get("user_status", ""),
                        ip=friend_data.get("user_ipaddr", ""),
                        port=friend_data.get("user_port", ""),
                    )
                    self.friends.append(friend)
                    self.friends_list.append(friend.username)
                    self.add_friend_item(friend)
                    
                    # 保存好友数据
                    self.friends_data[friend.username] = {
                        "username": friend.username,
                        "nickname": friend.nickname,
                        "email": "",
                        "friends": []
                    }
                except Exception as e:
                    print(f"[错误] 好友数据字段缺失: {e}, 数据内容: {friend_data}")
                    continue
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载好友列表时出错: {str(e)}")
    
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
        if index < len(self.friends):
            self.current_friend = self.friends[index]
            self.chat_title.setText(f"与 {self.current_friend.nickname or self.current_friend.username} 聊天中")
    
    def clear_chat_area(self):
        """清空聊天区域"""
        while self.chat_content_layout.count() > 1:
            item = self.chat_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def send_message_from_input(self, message):
        """发送消息处理"""
        if message and self.current_friend:
            self.append_message(self.current_user, message, True)

    def append_message(self, sender, message, is_me):
        """添加消息到聊天区域"""
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
        
        message_widget = QWidget()
        message_widget.setStyleSheet("background: transparent;")
        message_layout = QHBoxLayout()
        message_widget.setLayout(message_layout)
        
        avatar = AvatarLabel(sender, size=40)
        avatar.clicked.connect(lambda *args, u=sender, m=is_me: self.show_profile(u, m))
        
        bubble = ChatBubble(message, is_me)
        
        if is_me:
            message_layout.addStretch()
            message_layout.addWidget(bubble)
            message_layout.addWidget(avatar)
        else:
            message_layout.addWidget(avatar)
            message_layout.addWidget(bubble)
            message_layout.addStretch()
        
        self.chat_content_layout.insertWidget(
            self.chat_content_layout.count() - 1,
            time_label
        )
        self.chat_content_layout.insertWidget(
            self.chat_content_layout.count() - 1,
            message_widget
        )
        
        self.scroll_to_bottom()

    def show_profile(self, username, is_current_user=False):
        """显示用户资料对话框"""
        if is_current_user:
            profile_data = {
                'username': self.current_user,
                'nickname': self.user_data.get('nickname', self.current_user),
                'email': self.user_data.get('email', ''),
                'friends': self.friends_list
            }
        else:
            profile_data = self.friends_data.get(username, {
                "username": username,
                "nickname": username,
                "email": "",
                "friends": []
            })
        
        profile_dialog = ProfileDialog(
            user_data=profile_data,
            current_user=self.current_user if is_current_user else None,
            parent=self
        )
        
        if not is_current_user:
            profile_dialog.profile_widget.add_friend_requested.connect(
                lambda: self.send_friend_request(username))
            profile_dialog.profile_widget.send_message_requested.connect(
                lambda: self.start_private_chat(username))
        else:
            profile_dialog.profile_widget.profile_updated.connect(
                self.update_profile)
        
        profile_dialog.exec()

    def update_profile(self, updated_data):
        """更新个人资料"""
        try:
            valid_data = {
                'nickname': updated_data.get('nickname', self.user_data.get('nickname'))
            }
            
            response = updateinfo(valid_data["nickname"])
            
            if response.get('success'):
                self.user_data['nickname'] = valid_data['nickname']
                
                if hasattr(self.friend_list_header, "set_nickname"):
                    self.friend_list_header.set_nickname(valid_data['nickname'])
                
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
        QTimer.singleShot(50, lambda: scrollbar.setValue(scrollbar.maximum()))

    def send_friend_request(self, username):
        """发送好友请求"""
        try:
            response = addfriend(self.current_user, username)
            if "error" in response:
                QMessageBox.warning(self, "错误", response["error"])
            else:
                QMessageBox.information(self, "成功", "好友请求已发送")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"发送好友请求时出错: {str(e)}")

    def start_private_chat(self, username):
        """开始私聊"""
        for i, friend in enumerate(self.friends):
            if friend.username == username:
                self.friend_list.setCurrentRow(i)
                self.on_friend_selected(self.friend_list.currentItem())
                break


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatWindow("测试用户")
    window.show()
    sys.exit(app.exec())
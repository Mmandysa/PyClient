from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QSizePolicy, QSpacerItem)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon
from widgets.avatar_label import AvatarLabel
from ui.application_window import FriendRequestWindow

__all__ = ['FriendListHeader']

class FriendListHeader(QWidget):
    # 信号定义
    avatar_clicked = pyqtSignal(str)
    add_button_clicked = pyqtSignal() 
    
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.username = username
        self.setFixedHeight(60)
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI布局"""
        self.setStyleSheet("""
            FriendListHeader {
                background-color: #f5f5f5;
                border-bottom: 1px solid #e0e0e0;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)  # 保持原有边距
        layout.setSpacing(15)
        
        # 创建头像标签 (固定在左侧)
        self.avatar = AvatarLabel(self.username, size=30)
        self.avatar.setFixedSize(30, 30)
        self.avatar.clicked.connect(self.handle_avatar_click)
        layout.addWidget(self.avatar)
        
        # 添加水平弹簧
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        # 创建加号按钮 (固定在右侧)
        self.add_button = QPushButton()
        self.add_button.setFixedSize(30, 30)
        self.add_button.setIcon(QIcon("icons/add.png"))
        self.add_button.setIconSize(QSize(20, 20))
        self.add_button.setStyleSheet("""
            QPushButton {
                border: none;
                background: #e6e6e6;
                border-radius: 15px;
            }
            QPushButton:hover {
                background: #d6d6d6;
                border: 1px solid #c6c6c6;
            }
            QPushButton:pressed {
                background: #c6c6c6;
            }
        """)
        self.add_button.setToolTip("添加好友")
        self.add_button.clicked.connect(self.handle_add_button_click)
        layout.addWidget(self.add_button)
        
        self.setLayout(layout)
    
    def handle_avatar_click(self):
        """处理头像点击事件"""
        self.avatar_clicked.emit(self.username)
    
    def handle_add_button_click(self):
        """处理加号按钮点击事件 - 打开好友申请管理窗口"""
        
        # 检查是否已经存在窗口实例，避免重复创建
        if not hasattr(self, 'friend_request_window'):
            self.friend_request_window = FriendRequestWindow(
                current_user=self.username,
                parent=self  # 设置父组件确保窗口关闭时释放资源
            )
            # 连接信号到主窗口的处理方法
            self.friend_request_window.send_request.connect(self.handle_send_friend_request)
            self.friend_request_window.respond_request.connect(self.handle_respond_request)
        
        # 显示窗口（如果窗口已存在则带到前台）
        self.friend_request_window.show()
        self.friend_request_window.raise_()  # 窗口置顶
        self.friend_request_window.activateWindow()  # 激活窗口

    def handle_send_friend_request(self, username_or_email):
        """处理发送好友申请"""
        print(f"发送好友申请给: {username_or_email}")
        # 这里应该调用实际的API发送请求
        # 示例: self.api_client.send_friend_request(username_or_email)
        
    def handle_respond_request(self, username, accepted):
        """处理对好友申请的响应"""
        action = "同意" if accepted else "拒绝"
        print(f"{action} {username} 的好友申请")
        # 这里应该调用实际的API响应请求
        # 示例: self.api_client.respond_to_request(username, accepted)
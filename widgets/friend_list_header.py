# widgets/friend_list_header.py
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from widgets.avatar_label import AvatarLabel

__all__ = ['FriendListHeader']

class FriendListHeader(QWidget):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.setFixedHeight(60)
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI布局"""
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 用户头像 - 移除 size 参数或根据 AvatarLabel 定义调整
        self.avatar = AvatarLabel(self.username)  # 修改这里
        
        # 如果需要设置大小，可以通过样式表或固定大小
        self.avatar.setFixedSize(40, 40)
        
        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索好友...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                font-family: Microsoft YaHei;
                font-size: 14px;
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 15px;
                background: white;
            }
        """)
        self.search_input.setMinimumHeight(30)
        self.search_input.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Fixed
        )
        
        # 添加部件到布局
        layout.addWidget(self.avatar)
        layout.addWidget(self.search_input)
        
        self.setLayout(layout)
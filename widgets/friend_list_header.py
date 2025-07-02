from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QSizePolicy, QSpacerItem)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon
from widgets.avatar_label import AvatarLabel
from ui.application_window import FriendRequestWindow

__all__ = ['FriendListHeader']

class FriendListHeader(QWidget):
    # 信号定义
    need_update_friends = pyqtSignal()  # 需要更新好友列表信号
    avatar_clicked = pyqtSignal(str)    # 头像点击信号
    add_button_clicked = pyqtSignal()   # 添加按钮点击信号
    
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
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)
        
        # 创建头像标签
        self.avatar = AvatarLabel(self.username, size=30)
        self.avatar.setFixedSize(30, 30)
        self.avatar.clicked.connect(self.handle_avatar_click)
        layout.addWidget(self.avatar)
        
        # 添加水平弹簧
        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        # 创建加号按钮
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
        if not hasattr(self, 'friend_request_window'):
            self.friend_request_window = FriendRequestWindow(
                current_user=self.username,
                parent=self
            )
            # 连接好友删除信号到更新好友列表的方法
            self.friend_request_window.friend_deleted.connect(self.handle_friend_deleted)
        
        self.friend_request_window.show()
        self.friend_request_window.raise_()
        self.friend_request_window.activateWindow()
    
    def handle_friend_deleted(self):
        """处理好友删除事件，触发更新好友列表信号"""
        self.need_update_friends.emit()

    def set_nickname(self, nickname):
        self.nickname_label.setText(nickname)
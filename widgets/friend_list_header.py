from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from widgets.avatar_label import AvatarLabel

__all__ = ['FriendListHeader']

class FriendListHeader(QWidget):
    # 添加信号，用于通知外部头像被点击
    avatar_clicked = pyqtSignal(str)
    
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.username = username
        self.setFixedHeight(60)
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI布局"""
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 创建头像标签
        self.avatar = AvatarLabel(self.username, size=40)
        self.avatar.setFixedSize(40, 40)
        
        # 连接头像点击信号
        self.avatar.clicked.connect(self.handle_avatar_click)
        
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
    
    def handle_avatar_click(self):
        """处理头像点击事件"""
        self.avatar_clicked.emit(self.username)
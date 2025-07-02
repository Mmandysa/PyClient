from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont
from widgets.avatar_label import AvatarLabel


class FriendRequestWidget(QWidget):
    """单个好友申请项组件"""
    request_responded = pyqtSignal(str, bool)  # (username, accepted)

    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.username = username
        self.setup_ui()

    def setup_ui(self):
        """初始化UI"""
        self.setFixedHeight(60)
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        # 左侧：头像和用户名
        left_widget = QWidget()
        left_layout = QHBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # 头像
        self.avatar = AvatarLabel(self.username, size=40)
        self.avatar.setFixedSize(40, 40)
        left_layout.addWidget(self.avatar)

        # 用户名
        self.name_label = QLabel(self.username)
        self.name_label.setFont(QFont("Microsoft YaHei", 10))
        left_layout.addWidget(self.name_label)
        left_layout.addStretch()

        # 右侧：操作按钮
        right_widget = QWidget()
        right_layout = QHBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # 同意按钮
        self.accept_btn = QPushButton()
        self.accept_btn.setIcon(QIcon("icons/accept.png"))
        self.accept_btn.setIconSize(QSize(20, 20))
        self.accept_btn.setFixedSize(30, 30)
        self.accept_btn.setToolTip("同意申请")
        self.accept_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
            }
            QPushButton:hover {
                background: #e0f7fa;
            }
        """)
        self.accept_btn.clicked.connect(lambda: self.request_responded.emit(self.username, True))

        # 拒绝按钮
        self.reject_btn = QPushButton()
        self.reject_btn.setIcon(QIcon("icons/reject.png"))
        self.reject_btn.setIconSize(QSize(20, 20))
        self.reject_btn.setFixedSize(30, 30)
        self.reject_btn.setToolTip("拒绝申请")
        self.reject_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
            }
            QPushButton:hover {
                background: #ffebee;
            }
        """)
        self.reject_btn.clicked.connect(lambda: self.request_responded.emit(self.username, False))

        right_layout.addWidget(self.accept_btn)
        right_layout.addWidget(self.reject_btn)

        # 组合布局
        layout.addWidget(left_widget)
        layout.addWidget(right_widget)
        self.setLayout(layout)
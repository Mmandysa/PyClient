from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class FriendItemWidget(QWidget):
    def __init__(self, friend, parent=None):
        """
        好友列表项控件
        :param friend: Friend对象，包含username和online状态
        :param parent: 父组件
        """
        super().__init__(parent)
        self.friend = friend
        
        # 设置整体样式
        self.setStyleSheet("""
            QWidget {
                background: transparent;
                border: none;
            }
        """)
        
        # 在线状态指示器
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(10, 10)
        self.status_dot.setStyleSheet("""
            QLabel {
                background-color: %s;
                border-radius: 5px;
                border: none;
            }
        """ % ("#00c800" if friend.online else "gray"))
        
        # 用户名标签
        self.name_label = QLabel(friend.nickname)
        self.name_label.setFont(QFont("Microsoft YaHei", 12))
        self.name_label.setStyleSheet("""
            QLabel {
                color: %s;
                background: transparent;
            }
        """ % ("black" if friend.online else "gray"))
        
        # 布局
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 5, 15, 5) 
        layout.setSpacing(10)
        
        layout.addWidget(self.status_dot)
        layout.addWidget(self.name_label)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def update_status(self, is_online):
        """
        更新在线状态
        :param is_online: 是否在线
        """
        self.friend.status = is_online
        self.status_dot.setStyleSheet(f"""
            QLabel {{
                background-color: {"#00c800" if is_online else "gray"};
                border-radius: 5px;
            }}
        """)
        self.name_label.setStyleSheet(f"""
            QLabel {{
                color: {"black" if is_online else "gray"};
            }}
        """)
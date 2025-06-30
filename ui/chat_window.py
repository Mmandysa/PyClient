import sys
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QListWidget, QListWidgetItem, 
    QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QLabel, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QFont

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from models.friend import Friend
from widgets.avatar_label import AvatarLabel
from widgets.chat_bubble import ChatBubble
from widgets.friend_item import FriendItemWidget

class ChatWindow(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.username = username
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
        
        # 初始化好友列表
        self.init_friends()
    
    def create_friend_list(self):
        """创建好友列表区域"""
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
        self.splitter.addWidget(self.friend_list)
    
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
        """创建消息输入区域"""
        input_widget = QWidget()
        input_layout = QHBoxLayout()
        input_widget.setLayout(input_layout)
        
        # 消息输入框
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入消息...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                font-family: Microsoft YaHei;
                font-size: 14px;
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        
        # 发送按钮
        self.send_btn = QPushButton("发送")
        self.send_btn.setStyleSheet("""
            QPushButton {
                font-family: Microsoft YaHei;
                font-size: 14px;
                color: white;
                background-color: #00b400;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #00c800;
            }
            QPushButton:pressed {
                background-color: #009a00;
            }
        """)
        self.send_btn.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        self.chat_layout.addWidget(input_widget)
    
    def init_friends(self):
        """初始化好友列表数据"""
        #调用实际api获得好友列表
        self.friends = [
            Friend("张三", True),
            Friend("李四", False),
            Friend("王五", True),
            Friend("赵六", True),
            Friend("钱七", False)
        ]
        
        for friend in self.friends:
            self.add_friend_item(friend)
    
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
        self.chat_title.setText(f"与 {self.current_friend.username} 聊天中")
        
        # 清空聊天区域
        self.clear_chat_area()
        
        # 加载历史消息 (这里可以添加实际加载逻辑)
        # self.load_chat_history(self.current_friend)
    
    def clear_chat_area(self):
        """清空聊天区域"""
        # 保留最后的弹性空间
        while self.chat_content_layout.count() > 1:
            item = self.chat_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def send_message(self):
        """发送消息处理"""
        message = self.input_field.text().strip()
        if message and self.current_friend:
            #调用api发送消息
            # 添加自己的消息
            self.append_message(self.username, message, True)
            self.input_field.clear()
            
            # 模拟自动回复 (如果是张三)
            if self.current_friend.username == "张三":
                QTimer.singleShot(1000, lambda: self.append_message(
                    self.current_friend.username,
                    "自动回复: 你好，我现在不在线，稍后回复你",
                    False
                ))
    
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
        avatar = AvatarLabel(sender)
        
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
        
        # 添加到聊天区域 (在弹性空间之前)
        self.chat_content_layout.insertWidget(
            self.chat_content_layout.count() - 1,  # 在弹性空间前插入
            time_label
        )
        self.chat_content_layout.insertWidget(
            self.chat_content_layout.count() - 1,
            message_widget
        )
        
        # 滚动到底部
        self.scroll_to_bottom()
    
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
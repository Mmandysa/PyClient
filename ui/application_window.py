from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import  QFont

from widgets.application_item import FriendRequestWidget

from panel.connect import addfriend,show_friend_request_list,deal_friend_request


class FriendRequestWindow(QMainWindow):
    """好友申请管理主窗口"""
    send_request = pyqtSignal(str)  # 发送好友申请
    respond_request = pyqtSignal(str, bool)  # 响应好友申请(username, accept)

    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.setWindowTitle("好友申请管理")
        self.setGeometry(300, 300, 400, 500)
        self.setup_ui()
        self.respond_request.connect(self.on_respond_request)

    def setup_ui(self):
        """初始化主界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        central_widget.setLayout(main_layout)

        # 1. 搜索和添加区域
        self.setup_search_area(main_layout)

        # 2. 申请列表区域
        self.setup_request_list(main_layout)

        # 3.获取申请列表
        self.load_friend_requests(test_mode=True) 

    def setup_search_area(self, layout):
        """设置搜索和添加好友区域"""
        search_widget = QWidget()
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(10, 0, 10, 0)

        # 搜索输入框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入用户名或邮箱")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
        """)

        # 添加好友按钮
        self.add_btn = QPushButton("发送申请")
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        self.add_btn.clicked.connect(self.on_send_request)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.add_btn)
        layout.addWidget(search_widget)

    def setup_request_list(self, layout):
        """设置好友申请列表区域"""
        # 标题
        title = QLabel("收到的好友申请")
        title.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        title.setStyleSheet("padding: 5px 10px;")
        layout.addWidget(title)

        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
            }
            QScrollBar:vertical {
                width: 8px;
            }
        """)

        # 列表容器
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setSpacing(5)
        self.list_layout.setContentsMargins(5, 5, 5, 5)
        self.list_layout.addStretch()  # 初始时添加弹簧

        scroll_area.setWidget(self.list_container)
        layout.addWidget(scroll_area)

    def on_send_request(self):
        """处理发送好友申请 - 调用addfriend API"""
        search_text = self.search_input.text().strip()
        if not search_text:
            QMessageBox.warning(self, "提示", "请输入用户名或邮箱")
            return

        try:
            self.add_btn.setEnabled(False)
            self.add_btn.setText("发送中...")
            is_email = "@" in  search_text and "." in search_text
            #print(is_email)
            # 调用API
            response = addfriend("email" if is_email else "username",search_text)
            
            # 判断返回结果
            if 'error' in response:
                QMessageBox.critical(self, "", response['error'])
                
                
        except ConnectionError:
            QMessageBox.critical(
                self,
                "网络错误",
                "无法连接到服务器，请检查网络连接"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "错误",
                f"发生未知错误: {str(e)}"
            )
        finally:
            # 恢复按钮状态
            self.add_btn.setEnabled(True)
            self.add_btn.setText("发送申请")

    def load_friend_requests(self, test_mode=False):
        """加载好友申请列表
        
        Args:
            test_mode: 是否使用测试数据
        """
        # 先清空当前列表
        self.clear_requests()
        
        if test_mode:
            # 测试数据
            test_requests = ["user1", "user2", "user3@example.com"]
            for request in test_requests:
                self.add_request(request)
            return
        
        try:
            response = show_friend_request_list()
            if isinstance(response, list):
                for request in response:
                    username = request.get("username") or request.get("email", "")
                    if username:
                        self.add_request(username)
            else:
                QMessageBox.warning(self, "提示", "获取好友申请列表失败")
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "错误",
                f"加载好友申请时出错: {str(e)}"
            )

    def add_request(self, username):
        """添加新的好友申请项"""
        # 移除底部的弹簧
        if self.list_layout.count() > 0:
            item = self.list_layout.itemAt(self.list_layout.count() - 1)
            if item.spacerItem():
                self.list_layout.removeItem(item)

        # 创建新的申请项
        request_item = FriendRequestWidget(username)
        request_item.request_responded.connect(self.respond_request.emit)
        self.list_layout.addWidget(request_item)

        # 重新添加弹簧
        self.list_layout.addStretch()

    def clear_requests(self):
        """清空所有申请项"""
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.list_layout.addStretch()

    def on_respond_request(self, username, accepted):
        """处理好友申请响应"""
        
        try:
            if accepted:
                action = "accept"
                success_msg = f"已同意 {username} 的好友申请"
            else:
                action = "reject"
                success_msg = f"已拒绝 {username} 的好友申请"
            print(success_msg)
            response=deal_friend_request(username,action)
            
            if 'error' in response: 
                QMessageBox.warning(self, "失败", 
                                f"处理好友申请失败: {response.get('error', '未知错误')}")
            else:
                QMessageBox.information(self, "成功", success_msg)
                self._remove_request(username)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", 
                            f"处理好友申请时出错: {str(e)}")
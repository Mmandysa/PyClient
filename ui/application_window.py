from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon

from widgets.application_item import FriendRequestWidget
from panel.connect import addfriend, deletefriend, show_friend_request_list, deal_friend_request

class FriendRequestWindow(QMainWindow):
    """好友申请管理主窗口"""
    send_request = pyqtSignal(str)  # 发送好友申请
    respond_request = pyqtSignal(str, bool)  # 响应好友申请(username, accept)
    friend_deleted = pyqtSignal(str)  # 删除好友信号，传递用户名

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

        # 搜索和添加区域
        self.setup_search_area(main_layout)

        # 申请列表区域
        self.setup_request_list(main_layout)

        # 获取申请列表
        self.load_friend_requests()

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
        self.add_btn = QPushButton()
        self.add_btn.setIcon(QIcon("icons/add_friend.png"))
        self.add_btn.setIconSize(QSize(20, 20))
        self.add_btn.setFixedSize(30, 30)
        self.add_btn.setToolTip("发送好友申请")
        self.add_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
            }
            QPushButton:hover {
                background: #e0f7fa;
            }
        """)
        self.add_btn.clicked.connect(self.on_send_request)

        # 删除好友按钮
        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(QIcon("icons/delete_friend.png")) 
        self.delete_btn.setIconSize(QSize(20, 20))
        self.delete_btn.setFixedSize(30, 30)
        self.delete_btn.setToolTip("删除好友")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
            }
            QPushButton:hover {
                background: #ffebee;
            }
        """)
        self.delete_btn.clicked.connect(self.on_delete_friend)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.add_btn)
        search_layout.addWidget(self.delete_btn)
        layout.addWidget(search_widget)

    def setup_request_list(self, layout):
        """设置好友申请列表区域"""
        title = QLabel("收到的好友申请")
        title.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        title.setStyleSheet("padding: 5px 10px;")
        layout.addWidget(title)

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

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setSpacing(5)
        self.list_layout.setContentsMargins(5, 5, 5, 5)
        self.list_layout.addStretch()

        scroll_area.setWidget(self.list_container)
        layout.addWidget(scroll_area)

    def on_send_request(self):
        """处理发送好友申请"""
        search_text = self.search_input.text().strip()
        if not search_text:
            QMessageBox.warning(self, "提示", "请输入用户名或邮箱")
            return

        try:
            self.add_btn.setEnabled(False)
            self.add_btn.setIcon(QIcon("icons/loading.png"))  # 加载中图标
            
            is_email = "@" in search_text and "." in search_text
            response = addfriend("email" if is_email else "username", search_text)
            
            if 'error' in response:
                QMessageBox.critical(self, "错误", response['error'])
            else:
                QMessageBox.information(self, "成功", "好友申请已发送")
                self.search_input.clear()
                
        except ConnectionError:
            QMessageBox.critical(self, "网络错误", "无法连接到服务器，请检查网络连接")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"发生未知错误: {str(e)}")
        finally:
            self.add_btn.setEnabled(True)
            self.add_btn.setIcon(QIcon("icons/add_friend.png"))

    def on_delete_friend(self):
        """处理删除好友请求"""
        search_text = self.search_input.text().strip()
        if not search_text:
            QMessageBox.warning(self, "提示", "请输入用户名或邮箱")
            return

        try:
            reply = QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除好友 {search_text} 吗?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return

            self.delete_btn.setEnabled(False)
            self.delete_btn.setIcon(QIcon("icons/loading.png"))  # 加载中图标
            
            is_email = "@" in search_text and "." in search_text
            response = deletefriend("email" if is_email else "username", search_text)
            
            if "error" in response:
                QMessageBox.warning(self, "失败", response.get('error', '未知错误'))
            else:
                QMessageBox.information(self, "成功", f"已删除好友 {search_text}")
                self.search_input.clear()
                # 发射信号并传递被删除的用户名
                self.friend_deleted.emit(search_text)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除好友时出错: {str(e)}")
        finally:
            self.delete_btn.setEnabled(True)
            self.delete_btn.setIcon(QIcon("icons/delete_friend.png"))

    def load_friend_requests(self, test_mode=False):
        """加载好友申请列表"""
        self.clear_requests()
        
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
            QMessageBox.critical(self, "错误", f"加载好友申请时出错: {str(e)}")

    def add_request(self, username):
        """添加新的好友申请项"""
        if self.list_layout.count() > 0:
            item = self.list_layout.itemAt(self.list_layout.count() - 1)
            if item.spacerItem():
                self.list_layout.removeItem(item)

        request_item = FriendRequestWidget(username)
        request_item.request_responded.connect(self.respond_request.emit)
        self.list_layout.addWidget(request_item)
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
            action = "accept" if accepted else "reject"
            response = deal_friend_request(username, action)
            
            if 'error' in response: 
                QMessageBox.warning(self, "失败", response.get('error', '未知错误'))
            else:
                msg = f"已{'同意' if accepted else '拒绝'} {username} 的好友申请"
                QMessageBox.information(self, "成功", msg)
                self._remove_request(username)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理好友申请时出错: {str(e)}")

    def _remove_request(self, username):
        """从列表中移除指定的好友申请"""
        for i in range(self.list_layout.count()):
            item = self.list_layout.itemAt(i)
            if item.widget() and isinstance(item.widget(), FriendRequestWidget):
                if item.widget().username == username:
                    widget = item.widget()
                    self.list_layout.removeWidget(widget)
                    widget.deleteLater()
                    # 如果列表为空，添加弹簧
                    if self.list_layout.count() == 0:
                        self.list_layout.addStretch()
                    return
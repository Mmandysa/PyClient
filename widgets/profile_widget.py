from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QDialog, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont

from widgets.avatar_label import AvatarLabel
from panel.auth import logout

class ProfileWidget(QWidget):
    """个人资料展示组件"""
    profile_updated = pyqtSignal(dict)
    add_friend_requested = pyqtSignal(str)
    send_message_requested = pyqtSignal(str)
    logout_requested = pyqtSignal()  # 新增登出信号

    def __init__(self, user_data, current_user=None, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.current_user = current_user
        self.is_current_user = (current_user == user_data.get('username'))
        
        self.setup_ui()

    def setup_ui(self):
        """初始化界面布局"""
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(30, 20, 30, 20)
        self.layout.setSpacing(15)
        
        # 1. 头像区域
        self.setup_avatar_section()
        
        # 2. 信息区域
        self.setup_info_section()
        
        # 3. 操作按钮区域
        self.setup_action_buttons()
        
        self.setLayout(self.layout)

    def setup_avatar_section(self):
        """头像显示区域"""
        avatar_container = QWidget()
        avatar_layout = QVBoxLayout()
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        avatar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.avatar = AvatarLabel(
            self.user_data.get("username", ""), 
            size=180,
            parent=self
        )
        self.avatar.setFixedSize(180, 180)
        avatar_layout.addWidget(self.avatar)
        
        avatar_container.setLayout(avatar_layout)
        self.layout.addWidget(avatar_container)

    def setup_info_section(self):
        """信息区域"""
        info_container = QWidget()
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(10, 0, 10, 0)
        info_layout.setSpacing(12)
        
        self.add_info_row(info_layout, "用户名", self.user_data.get("username", ""), editable=False)
        
        nickname = self.user_data.get("nickname", "")
        self.nickname_edit = self.add_info_row(
            info_layout,
            "昵称", 
            nickname,
            editable=self.is_current_user
        )
        
        self.add_info_row(info_layout, "邮箱", self.user_data.get("email", ""), editable=False)
        
        info_container.setLayout(info_layout)
        self.layout.addWidget(info_container)

    def add_info_row(self, layout, label, value, editable):
        """添加信息行"""
        row = QWidget()
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(10)
        
        lbl = QLabel(f"{label}:")
        lbl.setFixedWidth(60)
        lbl.setFont(QFont("Microsoft YaHei", 10))
        
        if editable:
            edit = QLineEdit()
            edit.setText(value)
            edit.setStyleSheet("""
                QLineEdit {
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 6px 8px;
                }
            """)
            content_widget = edit
        else:
            content_widget = QLabel(value)
        
        row_layout.addWidget(lbl)
        row_layout.addWidget(content_widget, stretch=1)
        row.setLayout(row_layout)
        layout.addWidget(row)
        
        return edit if editable else None

    def setup_action_buttons(self):
        """设置底部操作按钮"""
        btn_container = QWidget()
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 20, 0, 0)
        
        if self.is_current_user:
            # 当前用户显示操作按钮
            self.logout_btn = QPushButton("退出登录")
            self.logout_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
            self.logout_btn.clicked.connect(self.on_logout_clicked)
            
            self.save_btn = QPushButton("保存修改")
            self.save_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background-color: #388E3C;
                }
            """)
            self.save_btn.clicked.connect(self.on_save_clicked)
            
            btn_layout.addWidget(self.logout_btn)
            btn_layout.addStretch()
            btn_layout.addWidget(self.save_btn)
        else:
            # 非当前用户显示互动按钮
            btn_layout.addStretch()
            
            if not self._is_friend():
                self.add_btn = QPushButton("添加好友")
                self.add_btn.setStyleSheet(self.get_button_style("#2196F3"))
                self.add_btn.clicked.connect(
                    lambda: self.add_friend_requested.emit(self.user_data["username"])
                )
                btn_layout.addWidget(self.add_btn)
            
            self.msg_btn = QPushButton("发送消息")
            self.msg_btn.setStyleSheet(self.get_button_style("#ff9800"))
            self.msg_btn.clicked.connect(
                lambda: self.send_message_requested.emit(self.user_data["username"])
            )
            btn_layout.addWidget(self.msg_btn)
        
        btn_container.setLayout(btn_layout)
        self.layout.addWidget(btn_container)

    def get_button_style(self, bg_color):
        """生成按钮的统一样式"""
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(bg_color)};
            }}
        """

    @staticmethod
    def darken_color(hex_color, factor=0.8):
        """颜色变暗效果"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(int(c * factor) for c in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"

    def _is_friend(self):
        """判断是否为好友关系"""
        return self.current_user in self.user_data.get('friends', [])

    def on_save_clicked(self):
        """保存修改的昵称"""
        new_nickname = self.nickname_edit.text().strip()
        if not new_nickname:
            QMessageBox.warning(self, "错误", "昵称不能为空")
            return
        
        if new_nickname == self.user_data.get("nickname", ""):
            QMessageBox.information(self, "提示", "昵称未修改")
            return
        
        self.profile_updated.emit({
            "nickname": new_nickname
        })

    def on_logout_clicked(self):
        """处理登出按钮点击"""
        reply = QMessageBox.question(
            self, 
            "确认退出",
            "确定要退出登录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.logout_btn.setEnabled(False)
                self.logout_btn.setText("登出中...")
                
                response = logout()
                
                # 判断是否有error字段
                if 'error' not in response:
                    # 登出成功，发射信号
                    self.logout_requested.emit()
                    # 关闭当前窗口
                    if self.parent() and hasattr(self.parent(), 'close'):
                        self.parent().close()
                else:
                    QMessageBox.warning(self, "登出失败", response.get('error', '登出请求失败'))
            except Exception as e:
                QMessageBox.critical(self, "错误", f"登出时出错: {str(e)}")
            finally:
                self.logout_btn.setEnabled(True)
                self.logout_btn.setText("退出登录")

class ProfileDialog(QDialog):
    """个人资料对话框"""
    def __init__(self, user_data, current_user=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self._generate_title(user_data, current_user))
        self.setFixedSize(400, 500)
        
        self.profile_widget = ProfileWidget(
            user_data=user_data,
            current_user=current_user,
            parent=self
        )
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.profile_widget)
        
        # 连接信号
        self.profile_widget.profile_updated.connect(self.close)
        self.profile_widget.logout_requested.connect(self.handle_logout)

    def handle_logout(self):
        """处理登出信号"""
        self.accept()  # 关闭对话框
        if self.parent():
            self.parent().close()  # 关闭父窗口(聊天窗口)

    @staticmethod
    def _generate_title(user_data, current_user):
        """生成对话框标题"""
        if current_user == user_data.get('username'):
            return "我的资料"
        return f"{user_data.get('nickname', user_data.get('username', ''))}的资料"
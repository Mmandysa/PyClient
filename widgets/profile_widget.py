from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont

from widgets.avatar_label import AvatarLabel

from panel.auth import logout

class ProfileWidget(QWidget):
    """个人资料展示和编辑组件"""
    profile_updated = pyqtSignal(dict)  # 资料更新信号
    add_friend_requested = pyqtSignal(str)  # 添加好友信号
    send_message_requested = pyqtSignal(str)  # 发起聊天信号
    logout_requested = pyqtSignal()  # 新增登出信号

    def __init__(self, user_data, current_user=None, parent=None):
        """
        初始化
        :param user_data: 用户数据字典，包含 username/nickname/email/friends 等字段
        :param current_user: 当前登录用户名（用于判断是否显示编辑按钮）
        :param parent: 父组件
        """
        super().__init__(parent)
        self.user_data = user_data
        self.current_user = current_user
        self.is_current_user = (current_user == user_data.get('username'))
        
        self.setup_ui()

    def setup_ui(self):
        """初始化界面布局"""
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)
        
        # 1. 头像区域
        self.setup_avatar_section()
        
        # 2. 信息区域
        self.setup_info_section()
        
        # 3. 操作按钮区域
        self.setup_action_buttons()
        
        self.setLayout(self.layout)

    def setup_avatar_section(self):
        """设置头像显示区域"""
        avatar_container = QWidget()
        avatar_layout = QVBoxLayout()
        avatar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 使用 AvatarLabel 显示圆形头像
        self.avatar = AvatarLabel(
            self.user_data.get("username", ""), 
            size=100,
            parent=self
        )
        self.avatar.setFixedSize(100, 100)
        avatar_layout.addWidget(self.avatar)
        
        avatar_container.setLayout(avatar_layout)
        self.layout.addWidget(avatar_container)

    def setup_info_section(self):
        """设置用户信息编辑区域"""
        # 用户名（不可编辑）
        self.add_info_row("用户名", self.user_data.get("username", ""), editable=False)
        
        # 昵称（当前用户可编辑）
        self.nickname_edit = self.add_info_row(
            "昵称", 
            self.user_data.get("nickname", self.user_data.get("username", "")),
            editable=self.is_current_user
        )
        
        # 邮箱（不可编辑）
        self.add_info_row("邮箱", self.user_data.get("email", ""), editable=False)

    def add_info_row(self, label, value, editable):
        """
        添加一行信息项
        :param label: 字段标签（如"用户名"）
        :param value: 字段值
        :param editable: 是否可编辑
        """
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 字段标签
        lbl = QLabel(f"{label}:")
        lbl.setFixedWidth(80)
        lbl.setFont(QFont("Microsoft YaHei", 10))
        
        # 内容控件（根据是否可编辑选择 QLineEdit 或 QLabel）
        if editable:
            edit = QLineEdit()
            edit.setText(value)
            edit.setStyleSheet("""
                QLineEdit {
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 6px;
                }
            """)
            self.current_edit = edit  # 保存引用用于后续获取值
        else:
            edit = QLabel(value)
            edit.setStyleSheet("QLabel { color: #555; }")
        
        layout.addWidget(lbl)
        layout.addWidget(edit)
        layout.addStretch()
        container.setLayout(layout)
        self.layout.addWidget(container)
        
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
            
            # 如果不是好友，显示"添加好友"按钮
            if not self._is_friend():
                self.add_btn = QPushButton("添加好友")
                self.add_btn.setStyleSheet(self.get_button_style("#2196F3"))
                self.add_btn.clicked.connect(
                    lambda: self.add_friend_requested.emit(self.user_data["username"])
                )
                btn_layout.addWidget(self.add_btn)
            
            # 显示"发送消息"按钮
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
        """颜色变暗效果（用于按钮hover状态）"""
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
        
        # 发射信号通知外部保存
        self.profile_updated.emit({
            "nickname": new_nickname
        })

    def on_logout_clicked(self):
        """处理登出按钮点击"""
        # 确认对话框
        reply = QMessageBox.question(
            self, 
            "确认退出",
            "确定要退出登录吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 显示加载状态
                self.logout_btn.setEnabled(False)
                self.logout_btn.setText("登出中...")
                
                # 调用API
                response = logout()
                
                # 判断是否有error字段
                if 'error' not in response:
                    # 登出成功
                    self.logout_requested.emit()
                    self.window().close()
                else:
                    # 登出失败，显示错误信息
                    QMessageBox.warning(
                        self,
                        "登出失败",
                        response.get('error', '登出请求失败')
                    )
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
                self.logout_btn.setEnabled(True)
                self.logout_btn.setText("退出登录")


class ProfileDialog(QDialog):
    """封装的个人资料对话框"""
    def __init__(self, user_data, current_user=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self._generate_title(user_data, current_user))
        self.setFixedSize(400, 350)
        
        # 设置对话框样式
        self.setStyleSheet("""
            QDialog {
                background: #f9f9f9;
                font-family: Microsoft YaHei;
            }
        """)
        
        # 初始化内部组件
        self.profile_widget = ProfileWidget(
            user_data=user_data,
            current_user=current_user,
            parent=self
        )
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.profile_widget)
        
        # 连接信号
        self.profile_widget.profile_updated.connect(self.close)

    @staticmethod
    def _generate_title(user_data, current_user):
        """生成对话框标题"""
        if current_user == user_data.get('username'):
            return "我的资料"
        return f"{user_data.get('nickname', user_data.get('username', ''))}的资料"
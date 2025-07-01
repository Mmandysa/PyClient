from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont
from widgets.avatar_label import AvatarLabel

class ProfileWidget(QWidget):
    profile_updated = pyqtSignal(dict)
    
    def __init__(self, user_data, is_current_user=False, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.is_current_user = is_current_user
        self.setup_ui()
        
    def setup_ui(self):
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)
        
        # 头像区域
        self.avatar = AvatarLabel(self.user_data.get("username", ""), size=80)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.avatar, 0, Qt.AlignmentFlag.AlignCenter)
        
        # 信息区域
        self.setup_info_section()
        
        # 操作按钮区域
        if self.is_current_user:
            self.setup_action_buttons()
        
        self.setLayout(self.layout)
    
    def setup_avatar_section(self):
        """设置头像区域"""
        avatar_container = QWidget()
        avatar_layout = QVBoxLayout()
        avatar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 使用改进后的AvatarLabel
        self.avatar = AvatarLabel(self.user_data.get("username", ""), size=100)
        self.avatar.setFixedSize(100, 100)
        
        # 头像上传按钮（仅当前用户）
        if self.is_current_user:
            self.upload_btn = QPushButton("更换头像")
            self.upload_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #3498db;
                    border: 1px solid #3498db;
                    border-radius: 4px;
                    padding: 4px;
                    margin-top: 8px;
                }
                QPushButton:hover {
                    background: #f0f8ff;
                }
            """)
            self.upload_btn.setFixedWidth(100)
            self.upload_btn.clicked.connect(self.change_avatar)
            avatar_layout.addWidget(self.upload_btn)
        
        avatar_layout.addWidget(self.avatar, 0, Qt.AlignmentFlag.AlignCenter)
        avatar_container.setLayout(avatar_layout)
        self.layout.addWidget(avatar_container)
    
    def setup_info_section(self):
        """设置信息编辑区域"""
        # 用户名（不可编辑）
        self.username_field = self.create_info_field(
            "用户名", 
            self.user_data.get("username", ""),
            editable=False
        )
        
        # 昵称
        self.nickname_field = self.create_info_field(
            "昵称", 
            self.user_data.get("nickname", ""),
            editable=self.is_current_user
        )
        
        # 邮箱
        self.email_field = self.create_info_field(
            "邮箱", 
            self.user_data.get("email", ""),
            editable=self.is_current_user
        )
        
        # 密码（仅当前用户可见）
        if self.is_current_user:
            self.password_field = self.create_info_field(
                "修改密码", 
                "",
                editable=True,
                is_password=True,
                placeholder="留空则不修改"
            )
    
    def create_info_field(self, label, value, editable=True, is_password=False, placeholder=""):
        """创建统一的信息字段"""
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 标签
        field_label = QLabel(f"{label}:")
        field_label.setFixedWidth(80)
        field_label.setFont(QFont("Microsoft YaHei", 10))
        
        # 输入框
        field_edit = QLineEdit()
        field_edit.setText(value)
        field_edit.setPlaceholderText(placeholder)
        
        if is_password:
            field_edit.setEchoMode(QLineEdit.EchoMode.Password)
        
        if not editable:
            field_edit.setReadOnly(True)
            field_edit.setStyleSheet("""
                QLineEdit {
                    background: transparent;
                    border: none;
                    color: #333;
                }
            """)
        else:
            field_edit.setStyleSheet("""
                QLineEdit {
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 6px;
                }
            """)
        
        layout.addWidget(field_label)
        layout.addWidget(field_edit)
        container.setLayout(layout)
        self.layout.addWidget(container)
        
        return field_edit
    
    def setup_action_buttons(self):
        """设置操作按钮"""
        btn_container = QWidget()
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 20, 0, 0)
        
        # 保存按钮
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
                background-color: #45a049;
            }
        """)
        self.save_btn.clicked.connect(self.on_save_clicked)
        
        # 取消按钮
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setStyleSheet("""
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
        self.cancel_btn.clicked.connect(lambda: self.parent().close())
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        btn_container.setLayout(btn_layout)
        self.layout.addWidget(btn_container)
    
    def change_avatar(self):
        """更换头像处理"""
        # 这里可以添加实际的图片选择逻辑
        QMessageBox.information(self, "提示", "头像更换功能需实现图片选择逻辑")
    
    def on_save_clicked(self):
        """保存修改处理"""
        updated_data = {
            "nickname": self.nickname_field.text(),
            "email": self.email_field.text(),
        }
        
        # 只有当前用户才能修改密码
        if self.is_current_user:
            new_password = self.password_field.text()
            if new_password:
                updated_data["password"] = new_password
        
        # 验证邮箱格式
        if "@" not in updated_data["email"]:
            QMessageBox.warning(self, "错误", "请输入有效的邮箱地址")
            return
        
        self.profile_updated.emit(updated_data)
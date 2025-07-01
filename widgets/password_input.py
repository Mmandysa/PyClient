from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QSize

class PasswordInput(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        # 主布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)  # 稍微增加间距
        
        
        # 密码输入框 - 与用户名输入框样式一致
        self.password_field = QLineEdit()
        self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_field.setFixedHeight(30)
        self.password_field.setPlaceholderText("输入密码")
        layout.addWidget(self.password_field)
        
        # 显示/隐藏密码按钮 - 调整为更简洁的样式
        self.toggle_button = QPushButton()
        self.toggle_button.setCheckable(True)
        self.toggle_button.setFixedSize(30, 30)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
            }
            QPushButton:hover {
                background: #f0f0f0;
                border-radius: 4px;
            }
        """)
        self.toggle_button.clicked.connect(self.toggle_password_visibility)
        self.update_button_icon()
        layout.addWidget(self.toggle_button)
        
    def toggle_password_visibility(self):
        """切换密码可见性"""
        if self.toggle_button.isChecked():
            self.password_field.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.update_button_icon()
    
    def update_button_icon(self):
        """更新按钮图标"""
        if self.toggle_button.isChecked():
            self.toggle_button.setIcon(QIcon("icons/eye_open.png"))  # 睁眼图标
        else:
            self.toggle_button.setIcon(QIcon("icons/eye_close.png"))  # 闭眼图标
        self.toggle_button.setIconSize(QSize(16, 16))
    
    def text(self):
        """获取密码文本"""
        return self.password_field.text()
    
    def setPlaceholderText(self, text):
        """设置占位文本"""
        self.password_field.setPlaceholderText(text)
        
    def setLabelText(self, text):
        """设置标签文本"""
        self.label.setText(text)
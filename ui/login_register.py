import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton, 
    QVBoxLayout, QHBoxLayout, QMessageBox, QStackedWidget
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt

from .chat_window import ChatWindow
class LoginRegisterWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("我的QQ - 登录")
        self.setFixedSize(450, 400)
        
        # 主布局使用 QStackedWidget 实现界面切换
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # 创建登录和注册页面
        self.login_page = self.create_login_page()
        self.register_page = self.create_register_page()
        self.stacked_widget.addWidget(self.login_page)
        self.stacked_widget.addWidget(self.register_page)
        
        # 默认显示登录页面
        self.stacked_widget.setCurrentIndex(0)
    
    def create_login_page(self):
        page = QWidget()
        page.setStyleSheet("background-color: white;")
        
        # 标题
        title_label = QLabel("我的QQ登录")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 用户名输入
        user_label = QLabel("用户名:")
        self.user_field = QLineEdit()
        self.user_field.setFixedHeight(30)
        
        # 密码输入
        pass_label = QLabel("密码:")
        self.pass_field = QLineEdit()
        self.pass_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_field.setFixedHeight(30)
        
        # 状态标签
        status_label = QLabel("状态: 已连接")
        status_label.setStyleSheet("color: green;")
        
        # 按钮
        login_btn = QPushButton("登录")
        login_btn.setFixedSize(100, 35)
        register_btn = QPushButton("注册")
        register_btn.setFixedSize(100, 35)
        
        # 按钮布局
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(login_btn)
        btn_layout.addWidget(register_btn)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 主布局
        layout = QVBoxLayout()
        layout.addWidget(title_label)
        layout.addSpacing(20)
        layout.addWidget(user_label)
        layout.addWidget(self.user_field)
        layout.addSpacing(10)
        layout.addWidget(pass_label)
        layout.addWidget(self.pass_field)
        layout.addSpacing(10)
        layout.addWidget(status_label)
        layout.addSpacing(20)
        layout.addLayout(btn_layout)
        layout.setContentsMargins(50, 30, 50, 30)
        
        page.setLayout(layout)
        
        # 按钮事件
        login_btn.clicked.connect(self.handle_login)
        register_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        
        return page
    
    def create_register_page(self):
        page = QWidget()
        page.setStyleSheet("background-color: white;")
        
        # 标题
        title_label = QLabel("注册新用户")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 用户名
        user_label = QLabel("用户名:")
        self.reg_user_field = QLineEdit()
        self.reg_user_field.setFixedHeight(30)
        
        # 邮箱
        email_label = QLabel("邮箱:")
        self.email_field = QLineEdit()
        self.email_field.setFixedHeight(30)
        
        # 密码
        pass_label = QLabel("密码:")
        self.reg_pass_field = QLineEdit()
        self.reg_pass_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_pass_field.setFixedHeight(30)
        
        # 确认密码
        confirm_label = QLabel("确认密码:")
        self.confirm_field = QLineEdit()
        self.confirm_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_field.setFixedHeight(30)
        
        # 按钮
        register_btn = QPushButton("注册")
        register_btn.setFixedSize(100, 35)
        back_btn = QPushButton("返回登录")
        back_btn.setFixedSize(100, 35)
        
        # 按钮布局
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(register_btn)
        btn_layout.addWidget(back_btn)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 主布局
        layout = QVBoxLayout()
        layout.addWidget(title_label)
        layout.addSpacing(10)
        layout.addWidget(user_label)
        layout.addWidget(self.reg_user_field)
        layout.addSpacing(5)
        layout.addWidget(email_label)
        layout.addWidget(self.email_field)
        layout.addSpacing(5)
        layout.addWidget(pass_label)
        layout.addWidget(self.reg_pass_field)
        layout.addSpacing(5)
        layout.addWidget(confirm_label)
        layout.addWidget(self.confirm_field)
        layout.addSpacing(20)
        layout.addLayout(btn_layout)
        layout.setContentsMargins(50, 20, 50, 30)
        
        page.setLayout(layout)
        
        # 按钮事件
        register_btn.clicked.connect(self.handle_register)
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        
        return page
    
    def handle_login(self):
        username = self.user_field.text().strip()
        password = self.pass_field.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "警告", "用户名或密码不能为空！")
        else:
           #填写api逻辑
            self.chat_window = ChatWindow(username) # 创建聊天窗口实例
            self.chat_window.show()# 显示聊天窗口
            self.close()# 关闭登录窗口
    
    def handle_register(self):
        username = self.reg_user_field.text().strip()
        email = self.email_field.text().strip()
        password = self.reg_pass_field.text().strip()
        confirm = self.confirm_field.text().strip()
        
        if not all([username, email, password, confirm]):
            QMessageBox.warning(self, "警告", "请填写所有字段！")
            return
        
        if "@" not in email or "." not in email:
            QMessageBox.warning(self, "警告", "邮箱格式不合法！")
            return
        
        if password != confirm:
            QMessageBox.warning(self, "警告", "两次密码不一致！")
            return
        
        # 实际注册api调用
        QMessageBox.information(self, "成功", "注册成功！")
        self.stacked_widget.setCurrentIndex(0)  # 返回登录页面
        # 清空注册表单
        self.reg_user_field.clear()
        self.email_field.clear()
        self.reg_pass_field.clear()
        self.confirm_field.clear()

def main():
    app = QApplication(sys.argv)
    
    # 设置全局字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    window = LoginRegisterWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
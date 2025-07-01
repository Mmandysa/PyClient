import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton, 
    QVBoxLayout, QHBoxLayout, QMessageBox, QStackedWidget, QCheckBox
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QSettings

from panel.auth import login, register
from .chat_window import ChatWindow
from widgets.password_input import PasswordInput  # 导入自定义组件

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
        layout = QVBoxLayout(page)
        layout.setContentsMargins(50, 30, 50, 30)
        
        # 标题
        title_label = QLabel("我的QQ登录")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        layout.addSpacing(20)
        
        # 用户名/邮箱输入
        account_label = QLabel("用户名/邮箱:")
        self.account_field = QLineEdit()
        self.account_field.setFixedHeight(30)
        self.account_field.setPlaceholderText("输入用户名或邮箱")
        layout.addWidget(account_label)
        layout.addWidget(self.account_field)
        layout.addSpacing(10)
        
        # 密码输入 - 使用自定义组件
        pass_label = QLabel("密码:")
        self.password_input = PasswordInput()
        self.password_input.setPlaceholderText("输入密码")
        layout.addWidget(pass_label)
        layout.addWidget(self.password_input)
        layout.addSpacing(10)
        
        # 记住我复选框
        self.remember_me = QCheckBox("记住我")
        self.remember_me.setChecked(False)
        layout.addWidget(self.remember_me)
        layout.addSpacing(10)
        
        # 状态标签
        status_label = QLabel("状态: 已连接")
        status_label.setStyleSheet("color: green;")
        layout.addWidget(status_label)
        layout.addSpacing(20)
        
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
        layout.addLayout(btn_layout)
        
        # 加载保存的登录信息
        self.load_saved_login()
        
        # 按钮事件
        login_btn.clicked.connect(self.handle_login)
        register_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        
        return page
    
    def create_register_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(50, 20, 50, 30)
        
        # 标题
        title_label = QLabel("注册新用户")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        layout.addSpacing(10)
        
        # 用户名
        user_label = QLabel("用户名:")
        self.reg_user_field = QLineEdit()
        self.reg_user_field.setFixedHeight(30)
        layout.addWidget(user_label)
        layout.addWidget(self.reg_user_field)
        layout.addSpacing(5)
        
        # 邮箱
        email_label = QLabel("邮箱:")
        self.email_field = QLineEdit()
        self.email_field.setFixedHeight(30)
        layout.addWidget(email_label)
        layout.addWidget(self.email_field)
        layout.addSpacing(5)
        
        # 密码 - 使用自定义组件
        pass_label = QLabel("密码:")
        self.reg_password_input = PasswordInput()
        self.reg_password_input.setPlaceholderText("设置密码")
        layout.addWidget(pass_label)
        layout.addWidget(self.reg_password_input)
        layout.addSpacing(5)
        
        # 确认密码 - 使用自定义组件
        confirm_label = QLabel("确认密码:")
        self.confirm_password_input = PasswordInput()
        self.confirm_password_input.setPlaceholderText("确认密码")
        layout.addWidget(confirm_label)
        layout.addWidget(self.confirm_password_input)
        layout.addSpacing(20)
        
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
        layout.addLayout(btn_layout)
        
        # 按钮事件
        register_btn.clicked.connect(self.handle_register)
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        
        return page
    
    def handle_login(self):
        account = self.account_field.text().strip()
        password = self.password_input.text()  # 使用组件的text()方法获取密码
        
        if not account or not password:
            QMessageBox.warning(self, "警告", "账号或密码不能为空！")
            return
        
        try:
            is_email = "@" in account and "." in account
            response = login("email" if is_email else "username", account, password)
            
            if 'error' in response:
                QMessageBox.critical(self, "登录失败", response['error'])
            else:
                username = response.get('username', account)
                if self.remember_me.isChecked():
                    self.save_login_info(account, password)
                
                self.chat_window = ChatWindow(username)
                self.chat_window.show()
                self.close()
                
        except Exception as e:
            QMessageBox.critical(self, "系统错误", f"登录过程中发生异常：{str(e)}")

    def handle_register(self):
        username = self.reg_user_field.text().strip()
        email = self.email_field.text().strip()
        password = self.reg_password_input.text()  # 使用组件的text()方法
        confirm = self.confirm_password_input.text()  # 使用组件的text()方法
        
        if not all([username, email, password, confirm]):
            QMessageBox.warning(self, "警告", "请填写所有字段！")
            return
        
        if "@" not in email or "." not in email:
            QMessageBox.warning(self, "警告", "邮箱格式不合法！")
            return
        
        if password != confirm:
            QMessageBox.warning(self, "警告", "两次密码不一致！")
            return
        
        try:
            response = register(username, password, email)
            if 'error' in response:
                QMessageBox.critical(self, "注册失败", response['error'])
            else:
                QMessageBox.information(self, "成功", "注册成功！")
                self.stacked_widget.setCurrentIndex(0)
                self.clear_register_form()
                
        except Exception as e:
            QMessageBox.critical(self, "系统错误", f"注册过程中发生异常：{str(e)}")

    def save_login_info(self, account, password):
        settings = QSettings("MyCompany", "MyQQ")
        settings.setValue("account", account)
        settings.setValue("password", password)

    def load_saved_login(self):
        settings = QSettings("MyCompany", "MyQQ")
        account = settings.value("account", "")
        password = settings.value("password", "")
        
        if account and password:
            self.account_field.setText(account)
            self.password_input.password_field.setText(password)  # 直接访问组件内部字段
            self.remember_me.setChecked(True)

    def clear_register_form(self):
        self.reg_user_field.clear()
        self.email_field.clear()
        self.reg_password_input.password_field.clear()
        self.confirm_password_input.password_field.clear()

def main():
    app = QApplication(sys.argv)
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    window = LoginRegisterWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
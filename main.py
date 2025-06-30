import sys
from PyQt6.QtGui import QFont 
from PyQt6.QtWidgets import QApplication
from ui.login_register import LoginRegisterWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置全局字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    # 显示登录窗口
    login_window = LoginRegisterWindow()
    login_window.show()
    
    sys.exit(app.exec())
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QToolButton, QDialog, QGridLayout, QFileDialog
)
from PyQt6.QtGui import QIcon

class EmojiDialog(QDialog):
    emoji_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择表情")
        self.setFixedSize(300, 200)
        
        layout = QGridLayout()
        
        emojis = ["😀", "😁", "😂", "🤣", "😃", "😄", "😅", "😆", "😉", "😊",
                  "😋", "😎", "😍", "😘", "😗", "😙", "😚", "🙂", "🤗", "🤩"]
        
        row, col = 0, 0
        for emoji in emojis:
            btn = QPushButton(emoji)
            btn.setStyleSheet("font-size: 20px;")
            btn.clicked.connect(lambda _, e=emoji: self.on_emoji_clicked(e))
            layout.addWidget(btn, row, col)
            col += 1
            if col > 4:
                col = 0
                row += 1
        
        self.setLayout(layout)
    
    def on_emoji_clicked(self, emoji):
        self.emoji_selected.emit(emoji)
        self.close()

class ChatInputWidget(QWidget):
    send_message_signal = pyqtSignal(str)
    send_file_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                background: white;
            }
        """)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(5, 3, 5, 3)
        container_layout.setSpacing(3)

        # 功能按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        
        self.emoji_btn = QToolButton()
        self.emoji_btn.setIcon(QIcon("icons/emoji.png"))
        self.emoji_btn.setToolTip("表情")
        self.emoji_btn.clicked.connect(self.show_emoji_dialog)
        
        self.file_btn = QToolButton()
        self.file_btn.setIcon(QIcon("icons/file.png"))
        self.file_btn.setToolTip("文件")
        self.file_btn.clicked.connect(self.select_file)
        
        self.image_btn = QToolButton()
        self.image_btn.setIcon(QIcon("icons/image.png"))
        self.image_btn.setToolTip("图片")

        btn_layout.addWidget(self.emoji_btn)
        btn_layout.addWidget(self.file_btn)
        btn_layout.addWidget(self.image_btn)
        btn_layout.addStretch()
        
        # 输入区域
        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("输入消息...")
        self.input_field.setStyleSheet("""
            QTextEdit {
                font-family: Microsoft YaHei;
                font-size: 14px;
                padding: 5px;
                border: none;
                min-height: 30px;
                max-height: 80px;
            }
        """)
        
        # 发送按钮区域
        send_layout = QHBoxLayout()
        send_layout.setContentsMargins(0, 0, 0, 0)

        # 图片隐写按钮（文字按钮）
        self.stego_btn = QPushButton("隐写")
        self.stego_btn.setStyleSheet("""
            QPushButton {
                font-family: Microsoft YaHei;
                font-size: 14px;
                color: #333;
                background-color: #f0f0f0;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #cccccc;
            }
        """)
        self.stego_btn.clicked.connect(self.choose_stego_image)

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
        self.send_btn.clicked.connect(self.on_send)
        
        send_layout.addStretch()
        send_layout.addWidget(self.stego_btn)
        send_layout.addWidget(self.send_btn)
        
        container_layout.addLayout(btn_layout)
        container_layout.addWidget(self.input_field)
        container_layout.addLayout(send_layout)
        main_layout.addWidget(container)
        self.setLayout(main_layout)

    def show_emoji_dialog(self):
        dialog = EmojiDialog(self)
        dialog.emoji_selected.connect(self.insert_emoji)
        dialog.exec()

    def insert_emoji(self, emoji):
        self.input_field.insertPlainText(emoji)

    def on_send(self):
        message = self.input_field.toPlainText().strip()
        if message:
            self.send_message_signal.emit(message)
            self.input_field.clear()

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "", "所有文件 (*.*)"
        )
        if file_path:
            self.send_file_signal.emit(file_path)

    def choose_stego_image(self):
        image_path, _ = QFileDialog.getOpenFileName(
            self, "选择要隐写的图片", "", "图片文件 (*.png *.jpg *.bmp)"
        )
        if image_path:
            print(f"你选择了用于隐写的图片: {image_path}")
            # 未来可添加：读取 self.input_field 中的内容进行隐写处理

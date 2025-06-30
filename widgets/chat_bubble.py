from PyQt6.QtWidgets import QFrame, QTextEdit, QHBoxLayout, QSizePolicy
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QTextDocument
from PyQt6.QtCore import Qt, QRectF, QSize

class ChatBubble(QFrame):
    def __init__(self, text, is_me, parent=None):
        """
        聊天气泡控件
        :param text: 消息文本
        :param is_me: 是否是自己发送的消息
        :param parent: 父组件
        """
        super().__init__(parent)
        self.is_me = is_me
        self.text = text
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet("background: transparent; border: none;")
        
        # 气泡内文本
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText(text)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background: transparent;
                border: none;
                padding: 8px;
                font-family: Microsoft YaHei;
                font-size: 14px;
                color: black;
            }
        """)
        
        # 禁用滚动条
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 自动调整大小
        doc = self.text_edit.document()
        doc.documentLayout().documentSizeChanged.connect(self.adjust_size)
        
        # 布局
        layout = QHBoxLayout()
        layout.addWidget(self.text_edit)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        # 初始大小调整
        self.adjust_size()
    
    def adjust_size(self):
        """根据文本内容调整气泡大小"""
        doc = self.text_edit.document()
        doc.setTextWidth(self.text_edit.width())
        new_height = doc.size().height()
        
        # 设置最小高度（包含padding）
        self.setMinimumHeight(int(new_height) + 16)
        self.updateGeometry()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 气泡颜色
        if self.is_me:
            color = QColor(154, 217, 105)  # 绿色气泡
        else:
            color = Qt.GlobalColor.white  # 白色气泡
        
        # 绘制圆角矩形
        rect = self.rect().adjusted(0, 0, -1, -1)
        rect_f = QRectF(rect)  # 转换为QRectF
        
        path = QPainterPath()
        path.addRoundedRect(rect_f, 15, 15)

        painter.fillPath(path, color)
    
    def sizeHint(self):
        """返回建议大小"""
        doc = self.text_edit.document()
        width = min(doc.idealWidth() + 30, 300)  # 最大宽度300
        height = doc.size().height() + 16
        return QSize(int(width), int(height))
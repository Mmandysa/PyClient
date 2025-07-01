from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPainter, QColor, QFont, QImage, QPixmap, QBrush
from PyQt6.QtCore import Qt, QSize, pyqtSignal
import hashlib

class AvatarLabel(QLabel):
    clicked = pyqtSignal()
    
    def __init__(self, username, size=40, parent=None):
        """
        初始化头像标签
        :param username: 用户名，用于生成头像
        :param size: 头像尺寸
        :param parent: 父组件
        """
        super().__init__(parent)
        self.username = username
        self.size = size
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        self.generate_avatar()  # 生成头像
        self.setFixedSize(self.size, self.size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def generate_avatar(self):
        """生成圆形头像，包含用户名的首字母"""
        # 创建透明背景的图像
        image = QImage(self.size, self.size, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. 生成确定性颜色（基于用户名哈希）
        color = self._generate_color_from_username()
        painter.setBrush(QBrush(color))

        # 2. 绘制圆形背景
        painter.drawEllipse(0, 0, self.size, self.size)

        # 3. 绘制首字母
        painter.setPen(Qt.GlobalColor.white)
        font = QFont("Microsoft YaHei", int(self.size * 0.4))  # 字体大小为尺寸的40%
        font.setBold(True)
        painter.setFont(font)

        # 获取用户名的第一个字符（支持中文）
        initial = self.username[0].upper() if self.username else "?"
        font_metrics = painter.fontMetrics()
        text_width = font_metrics.horizontalAdvance(initial)
        text_height = font_metrics.height()

        # 居中绘制文字
        painter.drawText(
            (self.size - text_width) // 2,
            (self.size - text_height) // 2 + font_metrics.ascent(),
            initial
        )

        painter.end()

        # 设置生成的图像
        self.setPixmap(QPixmap.fromImage(image))

    def _generate_color_from_username(self):
        """根据用户名生成确定性颜色"""
        # 使用MD5哈希确保相同用户名总是相同颜色
        hash_obj = hashlib.md5(self.username.encode('utf-8'))
        hash_int = int(hash_obj.hexdigest(), 16)
        
        # 从哈希值生成RGB颜色
        r = (hash_int & 0xFF) % 180 + 50  # 50-230
        g = ((hash_int >> 8) & 0xFF) % 180 + 50
        b = ((hash_int >> 16) & 0xFF) % 180 + 50
        
        return QColor(r, g, b)

    def mousePressEvent(self, event):
        """重写鼠标点击事件"""
        self.clicked.emit()
        super().mousePressEvent(event)

    def sizeHint(self):
        """返回建议大小"""
        return QSize(self.size, self.size)
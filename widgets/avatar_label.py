from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPainter, QColor, QFont, QImage, QPixmap, QBrush
from PyQt6.QtCore import Qt, QSize  # 添加 QSize 导入
import random
import hashlib

class AvatarLabel(QLabel):
    def __init__(self, username, parent=None):
        """
        初始化头像标签
        :param username: 用户名，用于生成头像
        :param parent: 父组件
        """
        super().__init__(parent)
        self.username = username
        self.setFixedSize(40, 40)  # 固定头像大小
        self.setStyleSheet("background: transparent; border: none;")
        self.generate_avatar()

    def generate_avatar(self):
        """生成圆形头像，包含用户名的首字母"""
        # 创建透明背景的图像
        image = QImage(40, 40, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. 生成确定性颜色（基于用户名哈希）
        color = self._generate_color_from_username()
        painter.setBrush(QBrush(color))

        # 2. 绘制圆形背景
        painter.drawEllipse(0, 0, 40, 40)

        # 3. 绘制首字母
        painter.setPen(Qt.GlobalColor.white)
        font = QFont("Microsoft YaHei", 16)
        font.setBold(True)
        painter.setFont(font)

        # 获取用户名的第一个字符（支持中文）
        initial = self.username[0].upper() if self.username else "?"
        font_metrics = painter.fontMetrics()
        text_width = font_metrics.horizontalAdvance(initial)
        text_height = font_metrics.height()

        # 居中绘制文字
        painter.drawText(
            (40 - text_width) // 2,
            (40 - text_height) // 2 + font_metrics.ascent(),
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
        
        # 从哈希值生成RGB颜色（避免太亮或太暗）
        r = (hash_int & 0xFF) % 180 + 50  # 50-230
        g = ((hash_int >> 8) & 0xFF) % 180 + 50
        b = ((hash_int >> 16) & 0xFF) % 180 + 50
        
        return QColor(r, g, b)

    def sizeHint(self):
        """返回建议大小"""
        return QSize(40, 40)
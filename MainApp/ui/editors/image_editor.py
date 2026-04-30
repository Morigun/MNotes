from ui.editors.base_editor import BaseEditor

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, QScrollArea,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage


class ImageEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._image_data = bytes()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        btn_row = QHBoxLayout()
        load_btn = QPushButton("📂 Загрузить изображение")
        load_btn.clicked.connect(self._load_file)
        btn_row.addWidget(load_btn)

        rotate_btn = QPushButton("↻ Повернуть")
        rotate_btn.clicked.connect(self._rotate)
        btn_row.addWidget(rotate_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._image_label = QLabel("Изображение не загружено")
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setMinimumSize(400, 300)
        scroll.setWidget(self._image_label)
        layout.addWidget(scroll, stretch=1)

    def _load_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Загрузить изображение", "",
            "Изображения (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;Все файлы (*)",
        )
        if path:
            from PIL import Image
            img = Image.open(path)
            if img.mode == "RGBA":
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")
            self._image_data = self._pil_to_bytes(img)
            self._display_image()

    def _pil_to_bytes(self, img) -> bytes:
        import io
        buf = io.BytesIO()
        fmt = "PNG" if img.mode == "RGBA" else "JPEG"
        img.save(buf, format=fmt)
        return buf.getvalue()

    def _display_image(self):
        if not self._image_data:
            return
        qimg = QImage()
        qimg.loadFromData(self._image_data)
        pixmap = QPixmap.fromImage(qimg)
        scaled = pixmap.scaled(
            self._image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._image_label.setPixmap(scaled)

    def _rotate(self):
        if not self._image_data:
            return
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(self._image_data))
        img = img.rotate(-90, expand=True)
        self._image_data = self._pil_to_bytes(img)
        self._display_image()

    def get_content(self) -> bytes:
        return self._image_data

    def set_content(self, data: bytes):
        self._image_data = data
        if data:
            self._display_image()

    def clear(self):
        self._image_data = bytes()
        self._image_label.clear()
        self._image_label.setText("Изображение не загружено")

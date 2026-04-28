from PyQt6.QtWidgets import QScrollArea, QWidget, QLayout, QLayoutItem, QSizePolicy
from PyQt6.QtCore import QPoint, QRect, QSize, Qt


class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=-1, hspacing=-1, vspacing=-1):
        super().__init__(parent)
        self._hspace = hspacing
        self._vspace = vspacing
        self._items: list[QLayoutItem] = []
        if margin >= 0:
            self.setContentsMargins(margin, margin, margin, margin)

    def addItem(self, item: QLayoutItem):
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int) -> QLayoutItem | None:
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int) -> QLayoutItem | None:
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self) -> Qt.Orientation:
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect: QRect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _do_layout(self, rect: QRect, move: bool) -> int:
        margins = self.contentsMargins()
        effective = rect.adjusted(margins.left(), margins.top(), -margins.right(), -margins.bottom())
        x = effective.x()
        y = effective.y()
        row_height = 0

        for item in self._items:
            item_size = item.sizeHint()
            next_x = x + item_size.width() + self._hspacing(effective.width())
            if next_x - self._hspacing(effective.width()) > effective.right() and row_height > 0:
                x = effective.x()
                y = y + row_height + self._vspacing(effective.width())
                next_x = x + item_size.width() + self._hspacing(effective.width())
                row_height = 0
            if move:
                item.setGeometry(QRect(QPoint(x, y), item_size))
            x = next_x
            row_height = max(row_height, item_size.height())

        return y + row_height - rect.y() + margins.bottom()

    def _hspacing(self, width: int) -> int:
        if self._hspace >= 0:
            return self._hspace
        return 10

    def _vspacing(self, width: int) -> int:
        if self._vspace >= 0:
            return self._vspace
        return 10

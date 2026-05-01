from database.models import Category, Tag
from database.repository import Repository

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QMenu, QInputDialog,
    QColorDialog,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor, QAction


class Sidebar(QWidget):
    category_selected = pyqtSignal(int)
    tag_selected = pyqtSignal(int)
    all_notes_selected = pyqtSignal()

    def __init__(self, repo: Repository | None = None, parent=None):
        super().__init__(parent)
        self._repo = repo or Repository()
        self.setFixedWidth(220)
        self.setObjectName("sidebar")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        all_btn = QPushButton("📋 Все заметки")
        all_btn.setObjectName("sidebarAllBtn")
        all_btn.clicked.connect(self.all_notes_selected.emit)
        layout.addWidget(all_btn)

        layout.addWidget(QLabel("Категории"))
        self._cat_tree = QTreeWidget()
        self._cat_tree.setHeaderHidden(True)
        self._cat_tree.setFixedHeight(200)
        self._cat_tree.itemClicked.connect(self._on_category_click)
        self._cat_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._cat_tree.customContextMenuRequested.connect(self._cat_context_menu)
        layout.addWidget(self._cat_tree)

        cat_btn_row = QHBoxLayout()
        add_cat_btn = QPushButton("+ Категория")
        add_cat_btn.clicked.connect(self._add_category)
        cat_btn_row.addWidget(add_cat_btn)
        cat_btn_row.addStretch()
        layout.addLayout(cat_btn_row)

        layout.addWidget(QLabel("Теги"))
        self._tag_tree = QTreeWidget()
        self._tag_tree.setHeaderHidden(True)
        self._tag_tree.setFixedHeight(180)
        self._tag_tree.itemClicked.connect(self._on_tag_click)
        self._tag_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tag_tree.customContextMenuRequested.connect(self._tag_context_menu)
        layout.addWidget(self._tag_tree)

        tag_btn_row = QHBoxLayout()
        add_tag_btn = QPushButton("+ Тег")
        add_tag_btn.clicked.connect(self._add_tag)
        tag_btn_row.addWidget(add_tag_btn)
        tag_btn_row.addStretch()
        layout.addLayout(tag_btn_row)

        layout.addStretch()

        self.refresh()

    def refresh(self):
        self._load_categories()
        self._load_tags()

    def _load_categories(self):
        self._cat_tree.clear()
        categories = self._repo.get_all_categories()
        for cat in categories:
            item = QTreeWidgetItem([cat.name])
            item.setData(0, Qt.ItemDataRole.UserRole, cat.id)
            color = QColor(cat.color)
            item.setForeground(0, color)
            self._cat_tree.addTopLevelItem(item)

    def _load_tags(self):
        self._tag_tree.clear()
        tags = self._repo.get_all_tags()
        counts = self._repo.get_tag_note_counts()
        for tag in tags:
            cnt = counts.get(tag.id, 0)
            item = QTreeWidgetItem([f"{tag.name} ({cnt})"])
            item.setData(0, Qt.ItemDataRole.UserRole, tag.id)
            self._tag_tree.addTopLevelItem(item)

    def _on_category_click(self, item: QTreeWidgetItem):
        cat_id = item.data(0, Qt.ItemDataRole.UserRole)
        if cat_id is not None:
            self.category_selected.emit(cat_id)

    def _on_tag_click(self, item: QTreeWidgetItem):
        tag_id = item.data(0, Qt.ItemDataRole.UserRole)
        if tag_id is not None:
            self.tag_selected.emit(tag_id)

    def _add_category(self):
        name, ok = QInputDialog.getText(self, "Новая категория", "Название:")
        if ok and name.strip():
            color = QColorDialog.getColor(QColor("#ffffff"), self, "Цвет категории")
            if color.isValid():
                self._repo.create_category(name.strip(), color.name())
            else:
                self._repo.create_category(name.strip())
            self._load_categories()

    def _cat_context_menu(self, pos):
        item = self._cat_tree.itemAt(pos)
        if item is None:
            return
        cat_id = item.data(0, Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        rename_action = menu.addAction("Переименовать")
        delete_action = menu.addAction("Удалить")
        action = menu.exec(self._cat_tree.mapToGlobal(pos))
        if action == rename_action:
            name, ok = QInputDialog.getText(self, "Переименовать", "Название:", text=item.text(0))
            if ok and name.strip():
                cats = self._repo.get_all_categories()
                cat = next((c for c in cats if c.id == cat_id), None)
                if cat:
                    cat.name = name.strip()
                    self._repo.update_category(cat)
                    self._load_categories()
        elif action == delete_action:
            self._repo.delete_category(cat_id)
            self._load_categories()

    def _add_tag(self):
        name, ok = QInputDialog.getText(self, "Новый тег", "Название:")
        if ok and name.strip():
            self._repo.create_tag(name.strip())
            self._load_tags()

    def _tag_context_menu(self, pos):
        item = self._tag_tree.itemAt(pos)
        if item is None:
            return
        tag_id = item.data(0, Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        delete_action = menu.addAction("Удалить")
        action = menu.exec(self._tag_tree.mapToGlobal(pos))
        if action == delete_action:
            self._repo.delete_tag(tag_id)
            self._load_tags()

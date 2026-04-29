from database.repository import Repository

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QHBoxLayout, QLabel,
)
from PyQt6.QtCore import Qt


class FolderPickerDialog(QDialog):
    def __init__(self, repo: Repository, exclude_ids: set[int] | None = None, parent=None):
        super().__init__(parent)
        self._repo = repo
        self._exclude = exclude_ids or set()
        self.selected_folder_id: int | None = None

        self.setWindowTitle("Выбрать папку")
        self.setMinimumSize(350, 400)
        self.resize(400, 450)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Выберите папку:"))

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.itemDoubleClicked.connect(self._on_double_click)

        root_item = QTreeWidgetItem(self._tree, ["/ (Корень)"])
        root_item.setData(0, Qt.ItemDataRole.UserRole, 0)
        root_item.setExpanded(True)

        self._build_tree(repo.get_all_folders(), root_item, None)
        self._tree.setCurrentItem(root_item)
        layout.addWidget(self._tree, stretch=1)

        btn_row = QHBoxLayout()
        ok_btn = QPushButton("Выбрать")
        ok_btn.clicked.connect(self._on_accept)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _build_tree(self, all_folders: list, parent_item: QTreeWidgetItem, parent_id: int | None):
        for folder in all_folders:
            if folder.id in self._exclude:
                continue
            pid = folder.parent_id if folder.parent_id else None
            if pid != parent_id:
                continue
            item = QTreeWidgetItem(parent_item, [f"📁 {folder.title}"])
            item.setData(0, Qt.ItemDataRole.UserRole, folder.id)
            item.setExpanded(True)
            self._build_tree(all_folders, item, folder.id)

    def _on_double_click(self, item, _col):
        self._on_accept()

    def _on_accept(self):
        item = self._tree.currentItem()
        if item:
            self.selected_folder_id = item.data(0, Qt.ItemDataRole.UserRole)
        self.accept()

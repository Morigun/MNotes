from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QProgressBar,
    QLabel, QPushButton, QMessageBox,
)
from PyQt6.QtCore import QThread, pyqtSignal


class SyncWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)

    def __init__(self, engine, last_sync, parent=None):
        super().__init__(parent)
        self._engine = engine
        self._last_sync = last_sync

    def run(self):
        self._engine.set_progress_callback(lambda msg: self.progress.emit(msg))
        try:
            result = self._engine.sync(self._last_sync)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({"error": str(e)})


class SyncDialog(QDialog):
    def __init__(self, engine, last_sync, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Синхронизация")
        self.setMinimumWidth(400)
        self.setModal(True)

        layout = QVBoxLayout(self)

        self._status_label = QLabel("Подготовка...")
        layout.addWidget(self._status_label)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)
        layout.addWidget(self._progress_bar)

        self._result_label = QLabel("")
        self._result_label.setWordWrap(True)
        layout.addWidget(self._result_label)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._cancel_btn = QPushButton("Отмена")
        self._cancel_btn.clicked.connect(self._on_cancel)
        btn_row.addWidget(self._cancel_btn)
        self._close_btn = QPushButton("Закрыть")
        self._close_btn.clicked.connect(self.accept)
        self._close_btn.setVisible(False)
        btn_row.addWidget(self._close_btn)
        layout.addLayout(btn_row)

        self._worker = SyncWorker(engine, last_sync, self)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)

    def start(self):
        self._worker.start()

    def _on_progress(self, msg: str):
        self._status_label.setText(msg)

    def _on_finished(self, result: dict):
        self._progress_bar.setRange(0, 1)
        self._progress_bar.setValue(1)
        if "error" in result:
            self._status_label.setText("Ошибка")
            self._result_label.setText(f"Ошибка: {result['error']}")
            QMessageBox.warning(self, "Ошибка синхронизации", result["error"])
        else:
            if result.get("last_sync"):
                from plugins.cloud_sync.settings import set_cloud_last_sync
                set_cloud_last_sync(result["last_sync"])
            self._status_label.setText("Синхронизация завершена")
            parts = []
            if result.get("pushed"):
                parts.append(f"Отправлено: {result['pushed']}")
            if result.get("pulled"):
                parts.append(f"Получено: {result['pulled']}")
            if result.get("conflicts"):
                parts.append(f"Конфликтов: {result['conflicts']}")
            self._result_label.setText("\n".join(parts) if parts else "Нет изменений")
        self._cancel_btn.setVisible(False)
        self._close_btn.setVisible(True)

    def _on_cancel(self):
        self._worker._engine.cancel()
        self._status_label.setText("Отмена...")
        self._cancel_btn.setEnabled(False)

    def reject(self):
        self._worker._engine.cancel()
        self._worker.wait(3000)
        super().reject()

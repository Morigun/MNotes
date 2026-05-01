import os
import tempfile

from ui.editors.base_editor import BaseEditor

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QLabel, QFileDialog,
    QMessageBox, QApplication,
)
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtMultimedia import (
    QMediaPlayer, QAudioOutput, QMediaCaptureSession,
    QMediaRecorder, QAudioInput, QMediaFormat,
)


class AudioEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._audio_data = bytearray()
        self._temp_dir = tempfile.mkdtemp(prefix="mnotes_")
        self._recording = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        btn_row = QHBoxLayout()

        self._record_btn = QPushButton("● Запись")
        self._record_btn.setCheckable(True)
        self._record_btn.setObjectName("recordBtn")
        self._record_btn.toggled.connect(self._toggle_record)
        btn_row.addWidget(self._record_btn)

        self._stop_btn = QPushButton("■ Стоп")
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop_all)
        btn_row.addWidget(self._stop_btn)

        self._play_btn = QPushButton("▶ Воспроизвести")
        self._play_btn.setEnabled(False)
        self._play_btn.clicked.connect(self._toggle_playback)
        btn_row.addWidget(self._play_btn)

        self._load_btn = QPushButton("📂 Загрузить")
        self._load_btn.clicked.connect(self._load_file)
        btn_row.addWidget(self._load_btn)

        self._plugin_btns: list[QPushButton] = []
        try:
            from plugins.plugin_manager import get_editor_actions
            for action in get_editor_actions("audio"):
                btn = QPushButton(action["label"])
                btn.setEnabled(False)
                btn.clicked.connect(lambda checked, h=action["handler"]: h(self))
                btn_row.addWidget(btn)
                self._plugin_btns.append(btn)
        except Exception:
            pass

        self._status_label = QLabel("")
        btn_row.addWidget(self._status_label)
        btn_row.addStretch()

        layout.addLayout(btn_row)

        slider_row = QHBoxLayout()
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, 0)
        self._slider.sliderMoved.connect(self._seek)
        slider_row.addWidget(self._slider)

        self._time_label = QLabel("00:00 / 00:00")
        slider_row.addWidget(self._time_label)
        layout.addLayout(slider_row)

        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.playbackStateChanged.connect(self._on_state_changed)

        self._audio_input = QAudioInput()
        self._capture_session = QMediaCaptureSession()
        self._capture_session.setAudioInput(self._audio_input)

        self._recorder = QMediaRecorder()
        self._capture_session.setRecorder(self._recorder)

        fmt = QMediaFormat()
        fmt.setFileFormat(QMediaFormat.FileFormat.Wave)
        self._recorder.setMediaFormat(fmt)

        self._update_timer = QTimer()
        self._update_timer.setInterval(200)
        self._update_timer.timeout.connect(self._update_slider)

    def _temp_path(self) -> str:
        return os.path.join(self._temp_dir, "recording.wav")

    def _toggle_record(self, checked: bool):
        if checked:
            self._player.stop()
            self._play_btn.setEnabled(False)
            self._play_btn.setText("▶ Воспроизвести")
            self._update_timer.stop()

            path = self._temp_path()
            if os.path.exists(path):
                os.remove(path)

            self._recorder.setOutputLocation(QUrl.fromLocalFile(path))
            self._recorder.record()
            self._record_btn.setText("● Запись...")
            self._stop_btn.setEnabled(True)
            self._status_label.setText("Запись...")
            self._recording = True
        else:
            self._recorder.stop()
            QTimer.singleShot(300, self._finalize_recording)

    def _finalize_recording(self):
        self._recording = False
        path = self._temp_path()
        if os.path.exists(path) and os.path.getsize(path) > 0:
            with open(path, "rb") as f:
                self._audio_data = bytearray(f.read())
            self._play_btn.setEnabled(True)
            self._set_plugin_btns_enabled(True)
            self._status_label.setText(f"Записано {len(self._audio_data)} байт")
        else:
            self._status_label.setText("Запись не удалась")
        self._record_btn.setText("● Запись")

    def _stop_all(self):
        if self._recording:
            self._recorder.stop()
            QTimer.singleShot(300, self._finalize_recording)
            self._record_btn.setChecked(False)
        self._player.stop()
        self._play_btn.setText("▶ Воспроизвести")
        self._stop_btn.setEnabled(False)
        self._update_timer.stop()

    def _toggle_playback(self):
        if not self._audio_data:
            return
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
            self._play_btn.setText("▶ Продолжить")
            self._update_timer.stop()
        else:
            self._ensure_player_source()
            self._player.play()
            self._play_btn.setText("⏸ Пауза")
            self._update_timer.start()

    def _ensure_player_source(self):
        path = self._temp_path()
        current_data = bytes(self._audio_data)
        if not os.path.exists(path):
            with open(path, "wb") as f:
                f.write(current_data)
        else:
            with open(path, "rb") as f:
                existing = f.read()
            if existing != current_data:
                with open(path, "wb") as f:
                    f.write(current_data)
        self._player.setSource(QUrl.fromLocalFile(path))

    def _on_position_changed(self, pos: int):
        self._slider.setValue(pos)
        self._update_time_label()

    def _on_duration_changed(self, dur: int):
        self._slider.setRange(0, max(dur, 0))
        self._update_time_label()

    def _on_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self._play_btn.setText("▶ Воспроизвести")
            self._update_timer.stop()
            self._slider.setValue(0)

    def _update_slider(self):
        self._slider.setValue(self._player.position())
        self._update_time_label()

    def _update_time_label(self):
        pos = self._player.position() // 1000
        dur = self._player.duration() // 1000
        self._time_label.setText(f"{pos // 60:02d}:{pos % 60:02d} / {dur // 60:02d}:{dur % 60:02d}")

    def _seek(self, pos: int):
        self._player.setPosition(pos)

    def _load_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load audio", "", "WAV (*.wav);;All files (*)"
        )
        if path:
            with open(path, "rb") as f:
                self._audio_data = bytearray(f.read())
            self._play_btn.setEnabled(True)
            self._set_plugin_btns_enabled(True)
            self._status_label.setText(f"Загружено {len(self._audio_data)} байт")

    def get_content(self) -> bytes:
        return bytes(self._audio_data)

    def set_content(self, data: bytes):
        self._audio_data = bytearray(data)
        if data:
            self._play_btn.setEnabled(True)
            self._set_plugin_btns_enabled(True)
            self._status_label.setText(f"Аудио {len(data)} байт")
        else:
            self._play_btn.setEnabled(False)
            self._set_plugin_btns_enabled(False)

    def clear(self):
        self._audio_data = bytearray()
        self._player.stop()
        self._player.setSource(QUrl())
        self._play_btn.setEnabled(False)
        self._set_plugin_btns_enabled(False)
        self._play_btn.setText("▶ Воспроизвести")
        self._slider.setValue(0)
        self._time_label.setText("00:00 / 00:00")
        self._status_label.setText("")
        self._update_timer.stop()

    def _set_plugin_btns_enabled(self, enabled: bool):
        for btn in self._plugin_btns:
            btn.setEnabled(enabled)

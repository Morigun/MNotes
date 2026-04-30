from pathlib import Path
import sys

from PyQt6.QtCore import QSettings

_SETTINGS = QSettings("MNotes", "MNotes")


def stt_model_path() -> Path:
    custom = _SETTINGS.value("stt/model_path", "")
    if custom and Path(custom).exists():
        return Path(custom)
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent / "vosk" / "small-model"
    return Path(__file__).resolve().parent.parent.parent / "vosk" / "small-model"


def set_stt_model_path(path: str):
    _SETTINGS.setValue("stt/model_path", path)


def stt_vosk_dir() -> Path:
    custom = _SETTINGS.value("stt/vosk_dir", "")
    if custom and Path(custom).exists():
        return Path(custom)
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent / "vosk"
    return Path(__file__).resolve().parent.parent.parent / "vosk"


def set_stt_vosk_dir(path: str):
    _SETTINGS.setValue("stt/vosk_dir", path)


def available_models() -> list[str]:
    vosk_dir = stt_vosk_dir()
    if not vosk_dir.exists():
        return []
    models = []
    for d in sorted(vosk_dir.iterdir()):
        if d.is_dir() and (d / "am").exists():
            models.append(d.name)
    return models

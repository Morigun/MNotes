import base64

from PyQt6.QtCore import QSettings

_SETTINGS = QSettings("MNotes", "MNotes")


def cloud_server_url() -> str:
    return _SETTINGS.value("cloud/server_url", "")


def set_cloud_server_url(url: str):
    _SETTINGS.setValue("cloud/server_url", url.rstrip("/"))


def cloud_login() -> str:
    return _SETTINGS.value("cloud/login", "")


def set_cloud_login(login: str):
    _SETTINGS.setValue("cloud/login", login)


def cloud_password() -> str:
    raw = _SETTINGS.value("cloud/password", "")
    if not raw:
        return ""
    try:
        return base64.b64decode(raw).decode("utf-8")
    except Exception:
        return ""


def set_cloud_password(password: str):
    _SETTINGS.setValue("cloud/password", base64.b64encode(password.encode("utf-8")).decode("ascii"))


def cloud_last_sync() -> str:
    return _SETTINGS.value("cloud/last_sync_at", "")


def set_cloud_last_sync(dt_str: str):
    _SETTINGS.setValue("cloud/last_sync_at", dt_str)

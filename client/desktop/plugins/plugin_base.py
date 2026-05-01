from abc import ABC, abstractmethod
from PyQt6.QtWidgets import QWidget


class PluginBase(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    def is_available(self) -> bool:
        return True

    def on_load(self): pass

    def on_unload(self): pass

    def get_settings_widget(self, parent=None) -> QWidget | None:
        return None

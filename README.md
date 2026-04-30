# MNotes

Десктопное приложение для управления заметками с поддержкой 8 типов контента, шифрованием, напоминаниями, папками и системой плагинов.

## Возможности

- **8 типов заметок**: текст, Markdown, форматированный текст (HTML), списки задач, таблицы, аудиозаписи, изображения, папки
- **Шифрование**: AES-256-GCM с паролем (Argon2 + PBKDF2)
- **Папки**: вложенная иерархия, drag-and-drop перемещение, breadcrumb-навигация
- **Напоминания**: разовые и повторяющиеся (daily/weekly/monthly/yearly) с системными уведомлениями
- **Корзина**: мягкое удаление с восстановлением (включая воссоздание папок)
- **Экспорт/импорт**: отдельные файлы (txt, md, html, csv, wav, png) или ZIP-архив
- **Резервное копирование**: копия базы данных через меню
- **Темы**: тёмная (Catppuccin Mocha) и светлая (Catppuccin Latte) с переключением
- **Поиск и замена**: поиск и замена текста в выделенных заметках
- **Дублирование**: копирование заметок одним кликом
- **Один экземпляр (Singleton)**: повторный запуск раскрывает уже запущенное приложение из трея
- **Системный трей**: сворачивание в трей, быстрое создание заметок
- **Система плагинов**: расширение функциональности через плагины с интерфейсом настроек
- **Распознавание речи**: плагин speech2text на базе Vosk для транскрибации аудиозаметок

## Скриншоты

<img width="1202" height="832" alt="image" src="https://github.com/user-attachments/assets/0b7d9f42-9bbf-46f4-a24c-a3888c9f9877" />
<img width="902" height="682" alt="image" src="https://github.com/user-attachments/assets/39ea63f1-9d77-4326-b81f-b968c42756ed" />
<img width="502" height="220" alt="image" src="https://github.com/user-attachments/assets/7000ac02-7406-41ca-b689-55c92c2355f9" />


## Требования

- Python 3.10+
- Windows 10/11

## Быстрый старт

### Запуск из исходников

```batch
run.bat
```

Скрипт создаст виртуальное окружение, установит зависимости и запустит приложение.

### Сборка EXE

```batch
build.bat
```

Готовый файл: `MainApp/dist/MNotes.exe`

### Ручная установка

```bash
cd MainApp
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Установка плагина speech2text

```bash
cd Plugins/speech2text
pip install -r requirements.txt
```

Для сборки плагина как дистрибутива:

```batch
cd Plugins/speech2text
build.bat
```

## Зависимости

| Пакет         | Назначение                  |
|---------------|-----------------------------|
| PyQt6         | UI-фреймворк                |
| markdown2     | Markdown → HTML             |
| cryptography  | AES-256-GCM шифрование     |
| argon2-cffi   | Хеширование паролей         |
| Pillow        | Обработка изображений       |

### Плагин speech2text (опционально)

| Пакет         | Назначение                  |
|---------------|-----------------------------|
| vosk          | Распознавание речи (FFI)    |

## Горячие клавиши

| Клавиша   | Действие                     |
|-----------|------------------------------|
| Ctrl+N    | Новая текстовая заметка      |
| Ctrl+F    | Поиск                        |
| Ctrl+H    | Найти и заменить             |
| Ctrl+D    | Дублировать выделенные       |
| Ctrl+A    | Выделить все                 |
| Ctrl+R    | Обновить                     |
| Delete    | В корзину                    |
| Escape    | Снять выделение              |
| Alt+F4    | Выход                        |

## Структура проекта

```
MNotes/
├── run.bat                     # Запуск приложения (обёртка)
├── build.bat                   # Сборка EXE (обёртка)
├── MainApp/                     # Основное приложение
│   ├── main.py                  # Точка входа, темы, singleton, заголовки окон
│   ├── database/                # SQLite: модели, репозиторий, миграции
│   ├── plugins/                 # Система плагинов (базовый класс, менеджер)
│   ├── services/                # Шифрование, экспорт, напоминания
│   ├── ui/                      # Окна, диалоги, редакторы
│   │   └── editors/             # 8 редакторов по типам заметок
│   └── resources/               # Темы (QSS): тёмная и светлая
└── Plugins/                     # Плагины (каждый в своей папке)
    └── speech2text/             # Распознавание речи (Vosk)
        ├── plugin.json          # Манифест плагина
        ├── stt_service.py       # Сервис транскрибации
        ├── vosk_shim.py         # FFI-обёртка libvosk.dll
        ├── settings.py          # Настройки модели (QSettings)
        └── build.py             # Сборка дистрибутива плагина
```

Подробная архитектура описана в [ARCHITECTURE.md](ARCHITECTURE.md).

## Система плагинов

Приложение поддерживает плагины, которые могут расширять функциональность редакторов и предоставлять свои настройки.

### Как создать плагин

1. Создайте папку в `Plugins/` с файлом `plugin.json`:

```json
{
    "name": "my-plugin",
    "version": "1.0.0",
    "description": "Описание плагина",
    "requires": []
}
```

2. Создайте `__init__.py` с классом `Plugin`, унаследованным от `PluginBase`:

```python
from plugins.plugin_base import PluginBase

class Plugin(PluginBase):
    @property
    def name(self) -> str:
        return "my-plugin"

    @property
    def description(self) -> str:
        return "Описание плагина"

    def on_load(self):
        from plugins.plugin_manager import register_editor_action
        register_editor_action("text", "Моё действие", self._my_handler)

    def _my_handler(self, editor):
        ...
```

3. Плагин автоматически обнаруживается и загружается при старте приложения.

### Доступные хуки

- `register_editor_action(editor_type, label, handler)` — добавляет кнопку в редактор заданного типа
- `get_settings_widget(parent)` — возвращает виджет настроек плагина (отображается в диалоге настроек)

## Лицензия

MIT

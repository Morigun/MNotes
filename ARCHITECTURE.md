# MNotes — Архитектура проекта

## Обзор

MNotes — десктопное приложение для управления заметками, написанное на Python с использованием фреймворка PyQt6. Поддерживает 8 типов заметок, шифрование AES-256-GCM, напоминания, папки с drag-and-drop навигацией, корзину с восстановлением, экспорт/импорт, тёмную и светлую темы, системный трей, систему плагинов, singleton-режим (один экземпляр).

## Версионирование

Версия приложения задаётся константой `APP_VERSION` в `client/desktop/main.py`. Текущая версия: **1.1.1**.

Используется в:
- `QApplication.setApplicationVersion()` — доступна через `QApplication.applicationVersion()`
- Tooltip иконки в трее: `"MNotes v1.0.0"`
- Диалог «О программе»: `"MNotes v1.0.0"`

## Технологический стек

| Компонент       | Технология                  |
|-----------------|-----------------------------|
| Язык            | Python 3.10+                |
| UI-фреймворк    | PyQt6                       |
| База данных     | SQLite 3 (WAL-режим)        |
| Шифрование      | AES-256-GCM + Argon2/PBKDF2 |
| Markdown        | markdown2                   |
| Изображения     | Pillow                      |
| Аудио           | PyQt6 Multimedia            |
| Плагины         | Собственная система (importlib + plugin.json) |

## Структура каталогов

```
MNotes/
├── .gitignore
├── README.md
├── ARCHITECTURE.md
├── run.bat                         # Запуск приложения (обёртка → client/desktop/run.bat)
├── build.bat                       # Сборка EXE (обёртка → client/desktop/build.bat)
├── build_installer.bat             # Сборка MSI-инсталлятора (WiX v4)
├── installer.wxs                   # WiX v4 определение инсталлятора
├── client/                         # Клиентская часть
│   └── desktop/                    # Десктопное приложение
│       ├── main.py                 # Точка входа, темы, заголовки окон
│       ├── requirements.txt        # Зависимости приложения
│       ├── run.bat                 # Скрипт запуска (Windows)
│       ├── build.bat               # Сборка PyInstaller EXE
│       ├── app.ico                 # Иконка приложения
│       ├── database/
│       │   ├── __init__.py
│       │   ├── db_manager.py       # Подключение к БД, миграции
│       │   ├── repository.py       # Data-access слой (CRUD)
│       │   └── models.py           # Data-модели (Note, Category, Tag)
│       ├── plugins/
│       │   ├── __init__.py
│       │   ├── plugin_base.py      # Абстрактный базовый класс плагина
│       │   └── plugin_manager.py   # Обнаружение, загрузка, реестр плагинов
│       ├── services/
│       │   ├── __init__.py
│       │   ├── crypto_service.py   # Шифрование и хеширование
│       │   ├── export_service.py   # Экспорт/импорт заметок
│       │   └── reminder_service.py # Сервис напоминаний (QTimer)
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── main_window.py      # Главное окно с меню, выделением, навигацией
│       │   ├── sidebar.py          # Боковая панель (категории, теги)
│       │   ├── search_bar.py       # Поиск с фильтром по типу
│       │   ├── notes_grid.py       # FlowLayout для карточек
│       │   ├── notes_table.py      # QTableWidget — табличный вид заметок
│       │   ├── note_card.py        # Карточка заметки (drag-and-drop, выделение)
│       │   ├── detail_dialog.py    # Диалог редактирования заметки
│       │   ├── trash_view.py       # Корзина с восстановлением папок
│       │   ├── calendar_widget.py  # Календарь с подсветкой дат
│       │   ├── export_dialog.py    # Диалог экспорта/импорта
│       │   ├── notification_popup.py # Всплывающее уведомление с анимацией
│       │   ├── folder_picker_dialog.py # Диалог выбора папки (дерево)
│       │   ├── find_replace_dialog.py  # Поиск и замена в текстовых заметках
│       │   ├── settings_dialog.py  # Диалог настроек (вкладка плагинов)
│       │   └── editors/
│       │       ├── __init__.py
│       │       ├── base_editor.py  # Абстрактный класс редактора
│       │       ├── text_editor.py  # Текстовый редактор
│       │       ├── markdown_editor.py # Markdown с превью
│       │       ├── richtext_editor.py # WYSIWYG-редактор (HTML)
│       │       ├── list_editor.py  # Список задач (чекбоксы)
│       │       ├── table_editor.py # Таблица (QTableWidget)
│       │       ├── audio_editor.py # Запись/воспроизведение аудио
│       │       ├── image_editor.py # Загрузка/поворот изображений
│       │       └── folder_editor.py # Папка (контейнер)
│       └── resources/
│           ├── style.qss           # Тёмная тема (Catppuccin Mocha)
│           └── style_light.qss     # Светлая тема (Catppuccin Latte)
├── server/                         # Серверная часть (PHP)
│   ├── index.php                   # Точка входа API
│   ├── auth.php                    # Авторизация (логин/пароль → JWT-токен)
│   ├── sync.php                    # Синхронизация (push/pull/file/delete)
│   ├── config.php                  # Конфигурация подключения к БД
│   ├── schema.sql                  # Схема серверной БД (MySQL)
│   ├── setup_db.php                # Создание таблиц
│   └── .htaccess                   # Перенаправление на index.php
└── plugins/                        # Плагины (каждый в своей папке)
    ├── cloud_sync/
    │   ├── __init__.py             # Точка входа: класс Plugin(PluginBase)
    │   ├── plugin.json             # Манифест (имя, версия, зависимости)
    │   ├── api_client.py           # HTTP-клиент для сервера
    │   ├── sync_engine.py          # Логика синхронизации (push/pull)
    │   ├── sync_dialog.py          # Диалог прогресса синхронизации
    │   ├── settings.py             # Настройки сервера (QSettings)
    │   └── requirements.txt        # Зависимости (requests)
    └── speech2text/
        ├── __init__.py             # Точка входа: класс Plugin(PluginBase)
        ├── plugin.json             # Манифест (имя, версия, зависимости)
        ├── stt_service.py          # Транскрибация: загрузка модели, распознавание
        ├── vosk_shim.py            # FFI-обёртка libvosk.dll (cffi)
        ├── settings.py             # Настройки пути к модели (QSettings)
        ├── build.py                # Сборка дистрибутива плагина
        ├── build.bat               # Запуск сборки
        ├── requirements.txt        # Зависимости плагина (vosk)
        └── vosk/                   # Модели Vosk (в .gitignore)
            ├── model/              # Полная модель (ru, ~3 ГБ)
            ├── small-model/        # Урезанная модель (~60 МБ)
            └── recasepunc/         # Модель восстановления пунктуации
```

## Слои архитектуры

### 1. Database (client/desktop/database/)

**DatabaseManager** (`db_manager.py`) — Singleton-обёртка над SQLite:
- Управляет единственным соединением
- Включает WAL-режим и foreign keys
- Выполняет миграции (добавление `parent_id`, `deleted_parent_name`, индексов)
- Схема: таблицы `notes`, `categories`, `tags`, `note_tags`

**Repository** (`repository.py`) — паттерн Repository:
- CRUD-операции над заметками, категориями, тегами
- Фильтрация: по типу, категории, тегу, тексту, дате, родительской папке
- Мягкое удаление / восстановление / перманентное удаление
- Папки: `move_note_to_folder`, `remove_note_from_folder`, `get_folder_child_count`, `get_all_folders`
- Дублирование: `duplicate_note` — копия с суффиксом «(копия)», без шифрования/напоминаний
- Запросы ожидающих напоминаний
- Подсчёт заметок по тегам (`get_tag_note_counts`)
- Даты с заметками и напоминаниями

**Models** (`models.py`) — dataclass-модели:
- `Note` — основная сущность (title, type, content, category_id, is_pinned, is_deleted, is_encrypted, password_hash, reminder_at, reminder_repeat, sort_order, parent_id, tags)
- `Category` — категория с цветом
- `Tag` — тег

### 2. Plugin System (client/desktop/plugins/)

**PluginBase** (`plugin_base.py`) — абстрактный базовый класс:
- `name` (str) — идентификатор плагина
- `description` (str) — описание
- `is_available()` — проверка доступности (по умолчанию `True`)
- `on_load()` — вызывается при загрузке плагина
- `on_unload()` — вызывается при выгрузке
- `get_settings_widget(parent)` — возвращает QWidget с настройками (опционально)

**PluginManager** (`plugin_manager.py`) — обнаружение и управление:
- Обнаружение: сканирует `client/desktop/plugins/` и `plugins/` (корень проекта) на наличие `plugin.json`
- Загрузка: `importlib.util` для динамического импорта, изоляция через `sys.path` и `__package__`
- Реестр: словарь `_plugins: dict[str, object]`, загруженные плагины по имени
- Расширение редакторов: `register_editor_action(editor_type, label, handler)` / `get_editor_actions(editor_type)` — плагины могут добавлять кнопки в редакторы
- API: `discover_plugins()`, `load_plugin()`, `load_all_plugins()`, `get_plugin()`, `loaded_plugins()`, `plugin_info()`

**Жизненный цикл плагина**:
1. `MainWindow.__init__()` → `_load_plugins()` → `load_all_plugins()`
2. `plugin_manager` сканирует директории, находит папки с `plugin.json`
3. Для каждого плагина: `importlib` загружает `__init__.py`, создаёт экземпляр `Plugin`
4. Вызывается `plugin.on_load()` — плагин регистрирует действия через `register_editor_action()`
5. Редакторы при инициализации вызывают `get_editor_actions(type)` и создают кнопки
6. `SettingsDialog` отображает список плагинов и их настройки

**Манифест плагина** (`plugin.json`):
```json
{
    "name": "plugin-name",
    "version": "1.0.0",
    "description": "Описание",
    "requires": ["vosk"],
    "optional": ["torch", "transformers"]
}
```

### 3. Services (client/desktop/services/)

**CryptoService** (`crypto_service.py`):
- Хеширование паролей: Argon2
- Шифрование: AES-256-GCM с ключом, полученным через PBKDF2-HMAC-SHA256 (200000 итераций)
- Формат зашифрованных данных: `salt(16) + nonce(12) + ciphertext`

**ExportService** (`export_service.py`):
- Экспорт одной заметки в файл (txt, md, html, csv, wav, png/jpg)
- Массовый экспорт в ZIP-архив с `index.json`
- Импорт из ZIP-архива

**ReminderService** (`reminder_service.py`):
- QTimer с интервалом 10 секунд
- Проверка заметок с наступившими напоминаниями
- Показ всплывающего уведомления (NotificationPopup) с `winsound` сигналом
- Повторяющиеся напоминания: daily, weekly, monthly, yearly
- Автоматический сдвиг `reminder_at` при повторяющихся напоминаниях

### 4. UI (client/desktop/ui/)

**MainWindow** (`main_window.py`) — главное окно:
- Верхнее меню: Файл, Правка, Заметки, Вид, Помощь
- Боковая панель (Sidebar), поиск (SearchBar), FlowLayout с карточками или QTableWidget (табличный вид)
- Переключение режима отображения: карточный (grid) / табличный (table) через кнопку в тулбаре или меню «Вид»
- Выбор режима сохраняется в QSettings (ключ `view_mode`)
- Навигация по папкам (breadcrumb, стек навигации)
- Выделение карточек: клик (одиночное), Ctrl+клик (множественное)
- Контекстное меню с учётом выделения (открыть, закрепить, удалить, убрать из папки)
- Единая логика удаления `_delete_items`: папки — перманентно (дети → корзина с путём), заметки — мягкое удаление
- Горячие клавиши: Ctrl+N, Ctrl+F, Ctrl+H, Ctrl+D, Ctrl+A, Ctrl+R, Delete, Escape, Alt+F4
- Применение темы заголовка окна через DWM API (`_apply_titlebar`, `_exec_dialog`)
- Загрузка плагинов при инициализации (`_load_plugins` → `load_all_plugins`)
- Закрытие окна скрывает в трей (`closeEvent` → `hide`)

**Sidebar** (`sidebar.py`) — боковая панель:
- Список категорий (QTreeWidget) с цветами
- Список тегов (QTreeWidget) с количеством заметок
- Контекстные меню: создание, переименование, удаление

**NoteCard** (`note_card.py`) — карточка заметки:
- Отображает заголовок, дату, тип, превью
- Поддержка drag-and-drop для перемещения в папки (защита от циклических вложений)
- Сигналы: `clicked` (выделение), `double_clicked` (открытие), `context_menu_requested`
- Визуальное выделение через `paintEvent` (синяя рамка + полупрозрачная заливка)

**NotesTable** (`notes_table.py`) — табличный вид заметок:
- QTableWidget со столбцами: 📌, Тип, Название, Категория, Превью, Дата, Теги
- Сортировка по столбцам (`setSortingEnabled`)
- Маппинг `note_id → row` для быстрого доступа к данным строки
- Те же сигналы что у NoteCard: `note_double_clicked`, `note_clicked`, `context_menu_requested`, `remove_from_folder`, `rename_folder`, `delete_folder`
- Выделение строк с визуальной подсветкой (полупрозрачная заливка)
- Хранение метаданных `note_type` и `in_folder` для контекстного меню

**DetailDialog** (`detail_dialog.py`) — диалог редактирования:
- Выбор редактора по типу заметки через `_EDITOR_MAP`
- Метаданные: заголовок, категория, теги, напоминание
- Закрепление, шифрование, мягкое удаление

**TrashView** (`trash_view.py`) — корзина:
- Список удалённых заметок с путём исходной папки (`deleted_parent_name`)
- Восстановление: заметки возвращаются, папки воссоздаются автоматически (`_ensure_folder_path`)
- Перманентное удаление выбранных или всех заметок

**CalendarWidget** (`calendar_widget.py`) — календарь:
- Подсветка дат: синий — заметки, красный — напоминания

**ExportDialog** (`export_dialog.py`) — экспорт/импорт:
- Выбор заметок с чекбоксами
- Экспорт в отдельные файлы или ZIP, импорт из ZIP

**NotificationPopup** (`notification_popup.py`) — всплывающее уведомление:
- Frameless-окно с анимацией исчезновения (6 секунд, fade-out)
- Позиционирование в правом нижнем углу экрана
- Рендеринг emoji через Segoe UI Emoji

**FolderPickerDialog** (`folder_picker_dialog.py`) — выбор папки:
- Иерархическое дерево папок (QTreeWidget) с корневым узлом «/»
- Исключение папок из списка (для предотвращения перемещения папки в саму себя)

**FindReplaceDialog** (`find_replace_dialog.py`) — поиск и замена:
- Работает с text/markdown/richtext заметками
- Подсчёт заменённых вхождений

**SettingsDialog** (`settings_dialog.py`) — настройки приложения:
- Вкладка «Плагины»: список обнаруженных плагинов с состоянием (загружен/не доступен)
- Динамические вкладки: каждый плагин с `get_settings_widget()` получает свою вкладку
- Использует `discover_plugins()`, `plugin_info()`, `loaded_plugins()` из `plugin_manager`

**Редакторы** (`ui/editors/`):
- `BaseEditor` — абстрактный класс с методами `get_content()`, `set_content()`, `clear()`
- Каждый редактор реализует свой интерфейс для конкретного типа данных
- Редакторы могут расширяться плагинами через `get_editor_actions(type)` — кнопки добавляются в интерфейс редактора

### 5. Plugins (plugins/)

#### speech2text — распознавание речи

**Plugin** (`__init__.py`) — реализация `PluginBase`:
- При загрузке (`on_load`) регистрирует действие `register_editor_action("audio", "📝 В текст", ...)` для аудиоредактора
- Обработчик `_on_transcribe`: получает WAV из редактора, вызывает `transcribe()`, создаёт текстовую заметку
- Предоставляет виджет настроек (`_STTSettingsWidget`): выбор папки с моделями, выбор модели, отображение размера

**stt_service.py** — сервис транскрибации:
- `ensure_model()` — автоматическая загрузка модели vosk-model-small-ru (если отсутствует)
- `transcribe(wav_path)` — распознавание речи: загрузка модели, чтение WAV, ресемплинг (audioop), поблочное распознавание
- `_restore_punctuation(text)` — восстановление пунктуации через recasepunc (опционально, требует torch)

**vosk_shim.py** — FFI-обёртка поверх `libvosk.dll`:
- Использует `cffi` для прямого вызова C-API Vosk
- Загружает DLL из подпапки `lib/` плагина
- Классы: `Model`, `KaldiRecognizer`, `SpkModel`
- Обёрнуты все основные методы: `AcceptWaveform`, `Result`, `PartialResult`, `FinalResult`, `SetWords`, `SetGrammar` и др.

**settings.py** — управление настройками:
- Использует `QSettings("MNotes", "MNotes")` для хранения путей
- `stt_model_path()` — путь к текущей модели (QSettings → fallback: `vosk/small-model`)
- `stt_vosk_dir()` — папка с моделями (QSettings → fallback: `vosk/`)
- `available_models()` — список моделей (папки с подпапкой `am/`)
- Поддержка frozen-режима (PyInstaller EXE)

**build.py** — сборка дистрибутива:
- Компилирует `.py` → `.pyc`, копирует `plugin.json`
- Копирует `libvosk.dll` и зависимости из pip-пакета vosk
- Результат: `dist/plugins/speech2text/`

## Схема базы данных

```
categories          tags                notes
┌─────────────┐    ┌─────────────┐    ┌──────────────────────┐
│ id (PK)     │    │ id (PK)     │    │ id (PK)              │
│ name        │    │ name        │    │ title                │
│ color       │    └─────────────┘    │ type                 │
└─────────────┘                       │ content (BLOB)       │
                                       │ category_id (FK)     │
          note_tags                    │ is_pinned            │
     ┌──────────────────┐              │ is_deleted           │
     │ note_id (FK, PK) │◄─────────────│ is_encrypted         │
     │ tag_id  (FK, PK) │──►tags       │ password_hash        │
     └──────────────────┘              │ created_at           │
                                       │ updated_at           │
                                       │ reminder_at          │
                                       │ reminder_repeat      │
                                       │ sort_order           │
                                       │ parent_id (FK)──────►│ (self-ref)
                                       │ deleted_parent_name  │
                                       └──────────────────────┘

Индексы: idx_notes_type, idx_notes_deleted, idx_notes_reminder,
         idx_notes_category, idx_notes_updated, idx_notes_parent
```

## Типы заметок

| Тип       | Редактор         | Хранение контента          |
|-----------|------------------|----------------------------|
| text      | TextEditor       | UTF-8 текст                |
| markdown  | MarkdownEditor   | Markdown-текст             |
| richtext  | RichTextEditor   | HTML                       |
| list      | ListEditor       | JSON `[{text, checked}]`   |
| table     | TableEditor      | JSON `{headers, rows}`     |
| audio     | AudioEditor      | WAV-байты                  |
| image     | ImageEditor      | PNG/JPEG-байты             |
| folder    | FolderEditor     | — (контейнер, parent_id)   |

## Система тем

- **Тёмная тема** (`style.qss`) — Catppuccin Mocha, активна по умолчанию
- **Светлая тема** (`style_light.qss`) — Catppuccin Latte, переключается через меню Вид
- Выбор темы сохраняется в `QSettings("MNotes", "MNotes")`
- Заголовки окон: Windows DWM API (`DwmSetWindowAttribute`, `DWMWA_USE_IMMERSIVE_DARK_MODE=20`)
- Применяется ко всем диалогам через `_exec_dialog()` и к главному окну через `_apply_titlebar()`

## Верхнее меню и горячие клавиши

### Файл
| Пункт                 | Горячая клавиша | Описание                    |
|-----------------------|-----------------|-----------------------------|
| Импорт...             | —               | Импорт из ZIP               |
| Экспорт...            | —               | Экспорт заметок             |
| Создать резервную копию | —             | Копия БД (WAL checkpoint + shutil) |
| Выход                 | Alt+F4          | Полное завершение приложения |

### Правка
| Пункт              | Горячая клавиша | Описание                              |
|--------------------|-----------------|---------------------------------------|
| Выделить все       | Ctrl+A          | Выделить все карточки                 |
| Снять выделение    | Escape          | Снять выделение                       |
| Найти и заменить   | Ctrl+H          | Замена текста в текстовых заметках    |

### Заметки
| Пункт                | Горячая клавиша | Описание                              |
|----------------------|-----------------|---------------------------------------|
| Добавить → (8 типов) | —               | Создание заметки заданного типа       |
| Открыть              | —               | Открыть выделенные заметки            |
| Закрепить / Открепить| —               | Переключение is_pinned                |
| Дублировать          | Ctrl+D          | Копия выделенных заметок              |
| Переместить в папку  | —               | Выбор папки из дерева                 |
| В корзину            | Delete          | Мягкое удаление (папки — перманентно) |
| Все заметки          | —               | Сброс фильтров и навигации            |
| Корзина...           | —               | Открыть корзину                       |

### Вид
| Пункт          | Горячая клавиша | Описание                        |
|----------------|-----------------|---------------------------------|
| Табличный вид  | —               | Переключение карточный/табличный |
| Календарь...   | —               | Фильтр по дате                  |
| Обновить       | Ctrl+R          | Перезагрузка карточек           |
| Светлая тема   | —               | Переключение тёмная/светлая     |
| Боковая панель | —               | Показ/скрытие боковой панели    |

### Дополнительно
| Горячая клавиша | Описание                     |
|-----------------|-------------------------------|
| Ctrl+N          | Новая текстовая заметка       |
| Ctrl+F          | Фокус на строку поиска        |

## Ключевые паттерны

- **Singleton** — DatabaseManager гарантирует одно соединение
- **Repository** — инкапсуляция SQL-запросов
- **Strategy** — выбор редактора через `_EDITOR_MAP` по типу заметки
- **Plugin** — расширение через `PluginBase` + `plugin_manager`, динамическая загрузка через `importlib`
- **Observer (Signal/Slot)** — связь между UI-компонентами через PyQt6 signals
- **Soft Delete** — заметки помечаются `is_deleted=1`, а не удаляются физически
- **Папки** — self-referencing FK (`parent_id → notes.id`), рекурсивное удаление с сохранением пути

## Безопасность

- Пароли шифрованных заметок хешируются Argon2
- Контент шифруется AES-256-GCM
- Ключ шифрования выводится из пароля через PBKDF2 (200000 итераций, SHA-256, 32 байта)
- Случайные salt (16 байт) и nonce (12 байт) для каждой шифровки

## Singleton (один экземпляр приложения)

Приложение работает в режиме одного экземпляра. Повторный запуск не создаёт новое окно, а раскрывает уже запущенное.

### Механизм

1. **Named Mutex** (`"MNotes_SingleInstance_Mutex"`) — проверяется **до** создания `QApplication`:
   - `CreateMutexW` — если мьютекс уже существует (`GetLastError() == 183` / `ERROR_ALREADY_EXISTS`), значит первый экземпляр запущен
2. **Named Event** (`"MNotes_Activate_Event"`) — межпроцессное взаимодействие:
   - Первый экземпляр создаёт event через `CreateEventW` и опрашивает его через `QTimer` каждые 200 мс (`WaitForSingleObject` с timeout=0)
   - Второй экземпляр открывает event через `OpenEventW` и сигнализирует через `SetEvent()`, затем завершается
   - Первый экземпляр ловит сигнал и вызывает `window._restore()` — `showNormal()` + `activateWindow()` + `raise_()`
3. Преимущество перед `ShowWindow` из чужого процесса: окно восстанавливается через собственный Qt event loop, что гарантирует корректную перерисовку

### Код (`client/desktop/main.py`)

```
main():
  ├── CreateMutexW("MNotes_SingleInstance_Mutex")
  ├── if already_running:
  │     OpenEventW("MNotes_Activate_Event") → SetEvent → exit
  ├── QApplication(...)
  ├── CreateEventW("MNotes_Activate_Event")
  ├── QTimer(200ms) → WaitForSingleObject → window._restore()
  └── ...
```

## Системный трей

- `setQuitOnLastWindowClosed(False)` — приложение не закрывается при закрытии окна
- `closeEvent` → `hide()` — окно скрывается в трей
- Меню трея: Показать, Новая заметка, Выход
- Двойной клик по иконке → восстановление окна

## Сборка и дистрибуция

### Основное приложение (PyInstaller)

```batch
cd client/desktop
build.bat
```

Результат: `client/desktop/dist/MNotes.exe` — автономный EXE со встроенными ресурсами и плагинами.

### Плагин speech2text

```batch
cd plugins/speech2text
build.bat
```

Результат: `plugins/speech2text/dist/plugins/speech2text/` — скомпилированный плагин с DLL, копируется в `dist/plugins/` рядом с EXE.

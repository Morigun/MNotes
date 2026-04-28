# MNotes — Архитектура проекта

## Обзор

MNotes — десктопное приложение для управления заметками, написанное на Python с использованием фреймворка PyQt6. Поддерживает различные типы заметок, шифрование, напоминания, папки, экспорт/импорт и системный трей.

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

## Структура каталогов

```
MNotes/
├── main.py                  # Точка входа
├── requirements.txt         # Зависимости
├── run.bat                  # Скрипт запуска (Windows)
├── app.ico                  # Иконка приложения
├── mnotes.db                # База данных SQLite
├── resources/
│   └── style.qss            # Стили Catppuccin Mocha
├── database/
│   ├── db_manager.py        # Подключение к БД, миграции
│   ├── repository.py        # Data-access слой (CRUD)
│   └── models.py            # Data-модели (Note, Category, Tag)
├── services/
│   ├── crypto_service.py    # Шифрование и хеширование
│   ├── export_service.py    # Экспорт/импорт заметок
│   └── reminder_service.py  # Сервис напоминаний (QTimer)
└── ui/
    ├── main_window.py       # Главное окно
    ├── sidebar.py           # Боковая панель (категории, теги)
    ├── search_bar.py        # Поиск с фильтром по типу
    ├── notes_grid.py        # FlowLayout для карточек
    ├── note_card.py         # Карточка заметки (drag-and-drop)
    ├── detail_dialog.py     # Диалог редактирования заметки
    ├── trash_view.py        # Корзина
    ├── calendar_widget.py   # Календарь
    ├── export_dialog.py     # Диалог экспорта/импорта
    ├── notification_popup.py# Всплывающее уведомление
    └── editors/
        ├── base_editor.py   # Абстрактный класс редактора
        ├── text_editor.py   # Текстовый редактор
        ├── markdown_editor.py # Markdown с превью
        ├── richtext_editor.py # WYSIWYG-редактор (HTML)
        ├── list_editor.py   # Список задач (чекбоксы)
        ├── table_editor.py  # Таблица (QTableWidget)
        ├── audio_editor.py  # Запись/воспроизведение аудио
        ├── image_editor.py  # Загрузка/поворот изображений
        └── folder_editor.py # Папка (контейнер)
```

## Слои архитектуры

### 1. Database (database/)

**DatabaseManager** (`db_manager.py`) — Singleton-обёртка над SQLite:
- Управляет единственным соединением
- Включает WAL-режим и foreign keys
- Выполняет миграции (добавление `parent_id`, `deleted_parent_name`)
- Схема: таблицы `notes`, `categories`, `tags`, `note_tags`

**Repository** (`repository.py`) — паттерн Repository:
- CRUD-операции над заметками, категориями, тегами
- Фильтрация: по типу, категории, тегу, тексту, дате, родительской папке
- Мягкое удаление / восстановление / перманентное удаление
- Запросы ожидающих напоминаний

**Models** (`models.py`) — dataclass-модели:
- `Note` — основная сущность (title, type, content, category_id, is_pinned, is_deleted, is_encrypted, reminder_at, parent_id, tags)
- `Category` — категория с цветом
- `Tag` — тег

### 2. Services (services/)

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
- Показ всплывающего уведомления (NotificationPopup)
- Повторяющиеся напоминания: daily, weekly, monthly, yearly

### 3. UI (ui/)

**MainWindow** (`main_window.py`) — главное окно:
- Содержит Sidebar, SearchBar, FlowLayout с карточками
- Навигация по папкам (breadcrumb, стек навигации)
- Создание заметок через выпадающее меню (8 типов)
- Системный трей (сворачивание, быстрое создание)

**Sidebar** (`sidebar.py`) — боковая панель:
- Список категорий (QTreeWidget) с цветами
- Список тегов (QTreeWidget) с количеством заметок
- Контекстные меню: создание, переименование, удаление

**NoteCard** (`note_card.py`) — карточка заметки:
- Отображает заголовок, дату, тип, превью
- Поддержка drag-and-drop для перемещения в папки
- Контекстное меню для папок

**DetailDialog** (`detail_dialog.py`) — диалог редактирования:
- Выбор редактора по типу заметки через `_EDITOR_MAP`
- Метаданные: заголовок, категория, теги, напоминание
- Закрепление, шифрование, мягкое удаление

**Редакторы** (`ui/editors/`):
- `BaseEditor` — абстрактный класс с методами `get_content()`, `set_content()`, `clear()`
- Каждый редактор реализует свой интерфейс для конкретного типа данных

## Схема базы данных

```
categories          tags                notes
┌─────────────┐    ┌─────────────┐    ┌──────────────────┐
│ id (PK)     │    │ id (PK)     │    │ id (PK)          │
│ name        │    │ name        │    │ title            │
│ color       │    └─────────────┘    │ type             │
└─────────────┘                       │ content (BLOB)   │
                                      │ category_id (FK) │
         note_tags                    │ is_pinned        │
    ┌──────────────────┐              │ is_deleted       │
    │ note_id (FK, PK) │◄─────────────│ is_encrypted     │
    │ tag_id  (FK, PK) │──►tags       │ password_hash    │
    └──────────────────┘              │ created_at       │
                                      │ updated_at       │
                                      │ reminder_at      │
                                      │ reminder_repeat  │
                                      │ sort_order       │
                                      │ parent_id (FK)──►│ (self-ref)
                                      └──────────────────┘
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

## Ключевые паттерны

- **Singleton** — DatabaseManager гарантирует одно соединение
- **Repository** — инкапсуляция SQL-запросов
- **Strategy** — выбор редактора через `_EDITOR_MAP` по типу заметки
- **Observer (Signal/Slot)** — связь между UI-компонентами через PyQt6 signals
- **Soft Delete** — заметки помечаются `is_deleted=1`, а не удаляются физически

## Безопасность

- Пароли шифрованных заметок хешируются Argon2
- Контент шифруется AES-256-GCM
- Ключ шифрования выводится из пароля через PBKDF2 (200000 итераций, SHA-256, 32 байта)
- Случайные salt (16 байт) и nonce (12 байт) для каждой шифровки

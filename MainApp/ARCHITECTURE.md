# MNotes — Архитектура проекта

## Обзор

MNotes — десктопное приложение для управления заметками, написанное на Python с использованием фреймворка PyQt6. Поддерживает 8 типов заметок, шифрование AES-256-GCM, напоминания, папки с drag-and-drop навигацией, корзину с восстановлением, экспорт/импорт, тёмную и светлую темы, системный трей.

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
├── main.py                  # Точка входа, темы, заголовки окон
├── requirements.txt         # Зависимости
├── run.bat                  # Скрипт запуска (Windows)
├── app.ico                  # Иконка приложения
├── mnotes.db                # База данных SQLite
├── resources/
│   ├── style.qss            # Тёмная тема (Catppuccin Mocha)
│   └── style_light.qss      # Светлая тема (Catppuccin Latte)
├── database/
│   ├── db_manager.py        # Подключение к БД, миграции
│   ├── repository.py        # Data-access слой (CRUD)
│   └── models.py            # Data-модели (Note, Category, Tag)
├── services/
│   ├── crypto_service.py    # Шифрование и хеширование
│   ├── export_service.py    # Экспорт/импорт заметок
│   └── reminder_service.py  # Сервис напоминаний (QTimer)
└── ui/
    ├── main_window.py       # Главное окно с меню, выделением, навигацией
    ├── sidebar.py           # Боковая панель (категории, теги)
    ├── search_bar.py        # Поиск с фильтром по типу
    ├── notes_grid.py        # FlowLayout для карточек
    ├── note_card.py         # Карточка заметки (drag-and-drop, выделение)
    ├── detail_dialog.py     # Диалог редактирования заметки
    ├── trash_view.py        # Корзина с восстановлением папок
    ├── calendar_widget.py   # Календарь с подсветкой дат
    ├── export_dialog.py     # Диалог экспорта/импорта
    ├── notification_popup.py# Всплывающее уведомление с анимацией
    ├── folder_picker_dialog.py # Диалог выбора папки (дерево)
    ├── find_replace_dialog.py  # Поиск и замена в текстовых заметках
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
- Показ всплывающего уведомления (NotificationPopup) с `winsound` сигналом
- Повторяющиеся напоминания: daily, weekly, monthly, yearly
- Автоматический сдвиг `reminder_at` при повторяющихся напоминаниях

### 3. UI (ui/)

**MainWindow** (`main_window.py`) — главное окно:
- Верхнее меню: Файл, Правка, Заметки, Вид, Помощь
- Боковая панель (Sidebar), поиск (SearchBar), FlowLayout с карточками
- Навигация по папкам (breadcrumb, стек навигации)
- Выделение карточек: клик (одиночное), Ctrl+клик (множественное)
- Контекстное меню с учётом выделения (открыть, закрепить, удалить, убрать из папки)
- Единая логика удаления `_delete_items`: папки — перманентно (дети → корзина с путём), заметки — мягкое удаление
- Горячие клавиши: Ctrl+N, Ctrl+F, Ctrl+H, Ctrl+D, Ctrl+A, Ctrl+R, Delete, Escape, Alt+F4
- Применение темы заголовка окна через DWM API (`_apply_titlebar`, `_exec_dialog`)
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

**Редакторы** (`ui/editors/`):
- `BaseEditor` — абстрактный класс с методами `get_content()`, `set_content()`, `clear()`
- Каждый редактор реализует свой интерфейс для конкретного типа данных

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
- **Observer (Signal/Slot)** — связь между UI-компонентами через PyQt6 signals
- **Soft Delete** — заметки помечаются `is_deleted=1`, а не удаляются физически
- **Папки** — self-referencing FK (`parent_id → notes.id`), рекурсивное удаление с сохранением пути

## Безопасность

- Пароли шифрованных заметок хешируются Argon2
- Контент шифруется AES-256-GCM
- Ключ шифрования выводится из пароля через PBKDF2 (200000 итераций, SHA-256, 32 байта)
- Случайные salt (16 байт) и nonce (12 байт) для каждой шифровки

## Системный трей

- `setQuitOnLastWindowClosed(False)` — приложение не закрывается при закрытии окна
- `closeEvent` → `hide()` — окно скрывается в трей
- Меню трея: Показать, Новая заметка, Выход
- Двойной клик по иконке → восстановление окна

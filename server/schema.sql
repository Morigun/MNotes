CREATE TABLE IF NOT EXISTS {PFX}categories (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    sync_uuid   CHAR(36) NOT NULL UNIQUE,
    name        VARCHAR(255) NOT NULL UNIQUE,
    color       VARCHAR(7) DEFAULT '#ffffff',
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS {PFX}tags (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    sync_uuid   CHAR(36) NOT NULL UNIQUE,
    name        VARCHAR(255) NOT NULL UNIQUE,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS {PFX}notes (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    sync_uuid       CHAR(36) NOT NULL UNIQUE,
    title           VARCHAR(500) NOT NULL DEFAULT '',
    type            VARCHAR(50) NOT NULL,
    content         LONGBLOB,
    category_uuid   CHAR(36),
    is_pinned       TINYINT(1) DEFAULT 0,
    is_deleted      TINYINT(1) DEFAULT 0,
    is_encrypted    TINYINT(1) DEFAULT 0,
    password_hash   VARCHAR(255),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    reminder_at     DATETIME,
    reminder_repeat VARCHAR(50),
    sort_order      INT DEFAULT 0,
    parent_uuid     CHAR(36),
    deleted_parent_name VARCHAR(500)
);

CREATE TABLE IF NOT EXISTS {PFX}note_tags (
    note_uuid CHAR(36) NOT NULL,
    tag_uuid  CHAR(36) NOT NULL,
    PRIMARY KEY (note_uuid, tag_uuid)
);

CREATE TABLE IF NOT EXISTS {PFX}sessions (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    token      CHAR(64) NOT NULL UNIQUE,
    expires_at DATETIME NOT NULL,
    INDEX idx_sessions_token (token),
    INDEX idx_sessions_expires (expires_at)
);

CREATE INDEX idx_notes_type ON {PFX}notes(type);
CREATE INDEX idx_notes_deleted ON {PFX}notes(is_deleted);
CREATE INDEX idx_notes_updated ON {PFX}notes(updated_at);
CREATE INDEX idx_notes_category ON {PFX}notes(category_uuid);
CREATE INDEX idx_notes_parent ON {PFX}notes(parent_uuid);

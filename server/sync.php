<?php
require_once __DIR__ . '/config.php';

header('Content-Type: application/json; charset=utf-8');

function check_auth(): bool {
    $token = $_SERVER['HTTP_X_AUTH_TOKEN'] ?? '';
    if (!$token) {
        return false;
    }
    $pdo = get_pdo();
    $stmt = $pdo->prepare("SELECT expires_at FROM " . t('sessions') . " WHERE token = ?");
    $stmt->execute([$token]);
    $row = $stmt->fetch();
    if (!$row) {
        return false;
    }
    return strtotime($row['expires_at']) > time();
}

function json_response(array $data, int $code = 200): void {
    http_response_code($code);
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
    exit;
}

$action = $_GET['sub'] ?? ($_GET['action'] ?? '');

if ($action === 'file') {
    if (!check_auth()) {
        json_response(['error' => 'Unauthorized'], 401);
    }
    $uuid = $_GET['uuid'] ?? '';
    if (!$uuid) {
        json_response(['error' => 'uuid required'], 400);
    }
    $pdo = get_pdo();
    $stmt = $pdo->prepare("SELECT content, type FROM " . t('notes') . " WHERE sync_uuid = ?");
    $stmt->execute([$uuid]);
    $row = $stmt->fetch();
    if (!$row || $row['content'] === null) {
        json_response(['error' => 'Not found'], 404);
    }
    header('Content-Type: application/octet-stream');
    header('Content-Disposition: attachment; filename="' . $uuid . '.bin"');
    echo $row['content'];
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'GET' && $action === 'pull') {
    if (!check_auth()) {
        json_response(['error' => 'Unauthorized'], 401);
    }
    $since = $_GET['since'] ?? '1970-01-01 00:00:00';
    $pdo = get_pdo();

    $notes = $pdo->prepare(
        "SELECT sync_uuid, title, type, category_uuid, is_pinned, is_deleted,
                is_encrypted, password_hash, created_at, updated_at, reminder_at,
                reminder_repeat, sort_order, parent_uuid, deleted_parent_name,
                CASE WHEN content IS NOT NULL THEN 1 ELSE 0 END AS has_file
         FROM " . t('notes') . " WHERE updated_at > ?"
    );
    $notes->execute([$since]);
    $notes_list = $notes->fetchAll();

    $cats = $pdo->prepare("SELECT sync_uuid, name, color, updated_at FROM " . t('categories') . " WHERE updated_at > ?");
    $cats->execute([$since]);
    $categories = $cats->fetchAll();

    $tags = $pdo->prepare("SELECT sync_uuid, name, updated_at FROM " . t('tags') . " WHERE updated_at > ?");
    $tags->execute([$since]);
    $tags_list = $tags->fetchAll();

    $nt = $pdo->prepare(
        "SELECT nt.note_uuid, nt.tag_uuid FROM " . t('note_tags') . " nt
         INNER JOIN " . t('notes') . " n ON n.sync_uuid = nt.note_uuid
         WHERE n.updated_at > ?"
    );
    $nt->execute([$since]);
    $note_tags = $nt->fetchAll();

    $deleted = $pdo->prepare("SELECT sync_uuid FROM " . t('notes') . " WHERE is_deleted = 1 AND updated_at > ?");
    $deleted->execute([$since]);
    $deleted_ids = array_column($deleted->fetchAll(), 'sync_uuid');

    json_response([
        'notes' => $notes_list,
        'categories' => $categories,
        'tags' => $tags_list,
        'note_tags' => $note_tags,
        'deleted_ids' => $deleted_ids,
    ]);
}

if ($_SERVER['REQUEST_METHOD'] === 'POST' && $action === 'push') {
    if (!check_auth()) {
        json_response(['error' => 'Unauthorized'], 401);
    }
    $pdo = get_pdo();
    $data_json = $_POST['data'] ?? '';
    if (!$data_json) {
        json_response(['error' => 'data field required'], 400);
    }
    $data = json_decode($data_json, true);
    if (!$data) {
        json_response(['error' => 'Invalid JSON in data'], 400);
    }

    $uploaded_files = [];
    if (!empty($_FILES['files'])) {
        $file_list = $_FILES['files'];
        $count = is_array($file_list['name']) ? count($file_list['name']) : 0;
        for ($i = 0; $i < $count; $i++) {
            $name = $file_list['name'][$i];
            if (preg_match('/^file_(.+)$/', $name, $m)) {
                $uploaded_files[$m[1]] = file_get_contents($file_list['tmp_name'][$i]);
            }
        }
    }

    $pushed = 0;
    $conflicts = [];

    if (!empty($data['categories'])) {
        $stmt = $pdo->prepare(
            "INSERT INTO " . t('categories') . " (sync_uuid, name, color, updated_at)
             VALUES (?, ?, ?, ?)
             ON DUPLICATE KEY UPDATE name = VALUES(name), color = VALUES(color), updated_at = VALUES(updated_at)"
        );
        foreach ($data['categories'] as $cat) {
            $stmt->execute([
                $cat['sync_uuid'],
                $cat['name'],
                $cat['color'] ?? '#ffffff',
                $cat['updated_at'] ?? gmdate('Y-m-d H:i:s'),
            ]);
            $pushed++;
        }
    }

    if (!empty($data['tags'])) {
        $stmt = $pdo->prepare(
            "INSERT INTO " . t('tags') . " (sync_uuid, name, updated_at)
             VALUES (?, ?, ?)
             ON DUPLICATE KEY UPDATE name = VALUES(name), updated_at = VALUES(updated_at)"
        );
        foreach ($data['tags'] as $tag) {
            $stmt->execute([
                $tag['sync_uuid'],
                $tag['name'],
                $tag['updated_at'] ?? gmdate('Y-m-d H:i:s'),
            ]);
            $pushed++;
        }
    }

    if (!empty($data['notes'])) {
        $stmt = $pdo->prepare(
            "INSERT INTO " . t('notes') . " (sync_uuid, title, type, content, category_uuid, is_pinned,
                is_deleted, is_encrypted, password_hash, created_at, updated_at, reminder_at,
                reminder_repeat, sort_order, parent_uuid, deleted_parent_name)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
             ON DUPLICATE KEY UPDATE
                title = VALUES(title), type = VALUES(type), content = COALESCE(VALUES(content), content),
                category_uuid = VALUES(category_uuid), is_pinned = VALUES(is_pinned),
                is_deleted = VALUES(is_deleted), is_encrypted = VALUES(is_encrypted),
                password_hash = VALUES(password_hash), updated_at = VALUES(updated_at),
                reminder_at = VALUES(reminder_at), reminder_repeat = VALUES(reminder_repeat),
                sort_order = VALUES(sort_order), parent_uuid = VALUES(parent_uuid),
                deleted_parent_name = VALUES(deleted_parent_name)"
        );
        foreach ($data['notes'] as $note) {
            $uuid = $note['sync_uuid'];
            $content = array_key_exists("file_{$uuid}", $uploaded_files)
                ? $uploaded_files["file_{$uuid}"]
                : null;

            $existing = $pdo->prepare("SELECT updated_at FROM " . t('notes') . " WHERE sync_uuid = ?");
            $existing->execute([$uuid]);
            $row = $existing->fetch();
            if ($row && isset($note['updated_at'])) {
                $server_ts = strtotime($row['updated_at']);
                $client_ts = strtotime($note['updated_at']);
                if ($server_ts > $client_ts) {
                    $conflicts[] = ['sync_uuid' => $uuid, 'reason' => 'server_newer'];
                    continue;
                }
            }

            $stmt->execute([
                $uuid,
                $note['title'] ?? '',
                $note['type'] ?? 'text',
                $content,
                $note['category_uuid'] ?? null,
                $note['is_pinned'] ?? 0,
                $note['is_deleted'] ?? 0,
                $note['is_encrypted'] ?? 0,
                $note['password_hash'] ?? null,
                $note['created_at'] ?? gmdate('Y-m-d H:i:s'),
                $note['updated_at'] ?? gmdate('Y-m-d H:i:s'),
                $note['reminder_at'] ?? null,
                $note['reminder_repeat'] ?? null,
                $note['sort_order'] ?? 0,
                $note['parent_uuid'] ?? null,
                $note['deleted_parent_name'] ?? null,
            ]);
            $pushed++;
        }
    }

    if (!empty($data['note_tags'])) {
        $stmt = $pdo->prepare(
            "INSERT IGNORE INTO " . t('note_tags') . " (note_uuid, tag_uuid) VALUES (?, ?)"
        );
        foreach ($data['note_tags'] as $nt) {
            $stmt->execute([$nt['note_uuid'], $nt['tag_uuid']]);
            $pushed++;
        }
    }

    if (!empty($data['deleted'])) {
        $stmt = $pdo->prepare("UPDATE " . t('notes') . " SET is_deleted = 1, updated_at = NOW() WHERE sync_uuid = ?");
        foreach ($data['deleted'] as $uuid) {
            $stmt->execute([$uuid]);
            $pushed++;
        }
    }

    json_response(['pushed' => $pushed, 'conflicts' => $conflicts]);
}

if ($_SERVER['REQUEST_METHOD'] === 'POST' && $action === 'delete') {
    if (!check_auth()) {
        json_response(['error' => 'Unauthorized'], 401);
    }
    $input = json_decode(file_get_contents('php://input'), true);
    if (!$input || empty($input['uuids'])) {
        json_response(['error' => 'uuids required'], 400);
    }
    $pdo = get_pdo();
    $stmt = $pdo->prepare("UPDATE " . t('notes') . " SET is_deleted = 1, updated_at = NOW() WHERE sync_uuid = ?");
    $deleted = 0;
    foreach ($input['uuids'] as $uuid) {
        $stmt->execute([$uuid]);
        $deleted += $stmt->rowCount();
    }
    json_response(['deleted' => $deleted]);
}

json_response(['error' => 'Unknown action'], 400);

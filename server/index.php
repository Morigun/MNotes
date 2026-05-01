<?php
chdir(__DIR__);
$action = $_GET['action'] ?? '';

if ($action === 'auth') {
    require __DIR__ . '/auth.php';
} elseif ($action === 'sync' || $action === 'file') {
    require __DIR__ . '/sync.php';
} elseif ($action === 'setup') {
    require __DIR__ . '/setup_db.php';
} else {
    header('Content-Type: application/json; charset=utf-8');
    http_response_code(400);
    echo json_encode(['error' => 'Unknown action']);
}

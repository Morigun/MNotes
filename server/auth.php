<?php
require_once __DIR__ . '/config.php';

header('Content-Type: application/json; charset=utf-8');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

$input = json_decode(file_get_contents('php://input'), true);
if (!$input || !isset($input['login'], $input['password'])) {
    http_response_code(400);
    echo json_encode(['error' => 'login and password required']);
    exit;
}

$login = $input['login'];
$password = $input['password'];

if ($login !== API_LOGIN || !password_verify($password, API_PASS_HASH)) {
    http_response_code(401);
    echo json_encode(['error' => 'Invalid credentials']);
    exit;
}

$timestamp = time();
$token = hash('sha256', $login . API_PASS_HASH . $timestamp);
$expires = gmdate('Y-m-d H:i:s', $timestamp + 86400);

$pdo = get_pdo();
$stmt = $pdo->prepare(
    "INSERT INTO " . t('sessions') . " (token, expires_at) VALUES (?, ?)
     ON DUPLICATE KEY UPDATE token = VALUES(token), expires_at = VALUES(expires_at)"
);
$stmt->execute([$token, $expires]);

echo json_encode(['token' => $token, 'expires' => $expires]);

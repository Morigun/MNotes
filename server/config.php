<?php
define('DB_HOST', 'localhost');
define('DB_NAME', 'mnotes_cloud');
define('DB_USER', 'root');
define('DB_PASS', '');
define('DB_PREFIX', 'mn_');

define('API_LOGIN', 'admin');
define('API_PASS_HASH', '');

function t(string $table): string {
    return DB_PREFIX . $table;
}

function get_pdo(): PDO {
    static $pdo = null;
    if ($pdo === null) {
        $pdo = new PDO(
            "mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=utf8mb4",
            DB_USER,
            DB_PASS,
            [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES => false,
            ]
        );
    }
    return $pdo;
}

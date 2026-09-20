<?php
/**
 * api.php
 * -------
 * Avukat Müvekkil Ön Kayıt PHP Uç Noktası (cPanel / Apache / Nginx uyumlu).
 * Verileri 'hukuk_dosyalar.json' dosyasında saklar.
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

$dataFile = __DIR__ . '/hukuk_dosyalar.json';

if (!file_exists($dataFile)) {
    file_put_contents($dataFile, json_encode([], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
}

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    $content = file_get_contents($dataFile);
    echo $content ?: '[]';
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = json_decode(file_get_contents('php://input'), true);
    if (!$input) {
        http_response_code(400);
        echo json_encode(['error' => 'Geçersiz veri.']);
        exit;
    }

    $currentData = json_decode(file_get_contents($dataFile), true) ?: [];
    $intakeCode = 'DOSYA-2026-' . rand(1000, 9999);

    $entry = [
        'id' => count($currentData) + 1,
        'intake_code' => $intakeCode,
        'client_type' => htmlspecialchars($input['client_type'] ?? ''),
        'full_name' => htmlspecialchars($input['full_name'] ?? ''),
        'id_number' => htmlspecialchars($input['id_number'] ?? ''),
        'phone' => htmlspecialchars($input['phone'] ?? ''),
        'email' => htmlspecialchars($input['email'] ?? ''),
        'city' => htmlspecialchars($input['city'] ?? ''),
        'legal_category' => htmlspecialchars($input['legal_category'] ?? ''),
        'opponent_name' => htmlspecialchars($input['opponent_name'] ?? ''),
        'opponent_vkn' => htmlspecialchars($input['opponent_vkn'] ?? ''),
        'existing_case' => htmlspecialchars($input['existing_case'] ?? ''),
        'case_summary' => htmlspecialchars($input['case_summary'] ?? ''),
        'evidences' => $input['evidences'] ?? [],
        'consultation_type' => htmlspecialchars($input['consultation_type'] ?? ''),
        'preferred_time' => htmlspecialchars($input['preferred_time'] ?? ''),
        'status' => 'Ön İncelemede',
        'created_at' => date('c')
    ];

    $currentData[] = $entry;
    file_put_contents($dataFile, json_encode($currentData, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));

    echo json_encode([
        'success' => true,
        'intake_code' => $intakeCode,
        'message' => 'Ön görüşme kaydınız başarıyla kaydedildi.'
    ], JSON_UNESCAPED_UNICODE);
    exit;
}
?>

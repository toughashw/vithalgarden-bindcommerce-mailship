<?php

// Configurazione SFTP
$sftp_host = "ws.italagro.bindcommerce.biz";
$sftp_port = 22;
$sftp_user = "wsitalagro";
$sftp_pass = "LA_TUA_PASSWORD"; // Usa variabili d'ambiente per sicurezza

// Percorsi locali
$local_json_dir = "json_orders/"; // Cartella locale JSON
$local_csv_dir = "csv_orders/";   // Cartella temporanea per CSV

// Percorsi remoti
$remote_orders_dir = "/home/wsitalagro/webapps/ws-italagro/orders/";
$remote_done_dir = "/home/wsitalagro/webapps/ws-italagro/orders/done/";

// Creazione cartella locale per CSV se non esiste
if (!is_dir($local_csv_dir)) {
    mkdir($local_csv_dir, 0777, true);
}

// Funzione per convertire JSON in CSV
function convertJsonToCsv($json_file) {
    global $local_csv_dir;

    // Legge il JSON
    $json_data = file_get_contents($json_file);
    $data = json_decode($json_data, true);

    if (!$data) {
        echo "❌ Errore nella lettura del JSON: $json_file\n";
        return false;
    }

    // Genera il nome del CSV
    $csv_filename = "ordini_" . date("Ymd_His") . ".csv";
    $csv_path = $local_csv_dir . $csv_filename;

    // Scrive i dati nel CSV
    $fp = fopen($csv_path, 'w');
    if (!$fp) {
        echo "❌ Errore nella creazione del file CSV\n";
        return false;
    }

    // Intestazione CSV
    fputcsv($fp, array_keys($data[0]), ";");

    // Scrittura righe CSV
    foreach ($data as $row) {
        fputcsv($fp, $row, ";");
    }

    fclose($fp);
    return $csv_path;
}

// Funzione per caricare file su SFTP
function uploadToSftp($local_file, $remote_path) {
    global $sftp_host, $sftp_port, $sftp_user, $sftp_pass;

    $connection = ssh2_connect($sftp_host, $sftp_port);
    if (!$connection) {
        echo "❌ Errore di connessione a SFTP\n";
        return false;
    }

    ssh2_auth_password($connection, $sftp_user, $

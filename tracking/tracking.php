<?php

// Funzione per scaricare il file JSON da SFTP
function download_json_from_sftp($sftp_host, $sftp_port, $sftp_username, $sftp_password, $remote_path) {
    $connection = ssh2_connect($sftp_host, $sftp_port);
    
    if (!$connection) {
        die('Impossibile connettersi al server SFTP');
    }

    // Autenticazione con nome utente e password
    if (!ssh2_auth_password($connection, $sftp_username, $sftp_password)) {
        die('Autenticazione fallita');
    }

    // Inizializzazione del client SFTP
    $sftp = ssh2_sftp($connection);

    if (!$sftp) {
        die('Impossibile inizializzare il client SFTP');
    }

    // Lettura del file JSON dal server SFTP
    $remote_file = "ssh2.sftp://$sftp$remote_path";
    $json_data = file_get_contents($remote_file);
    
    if ($json_data === false) {
        die('Errore nel leggere il file JSON dal server SFTP');
    }

    return $json_data;
}

// Funzione per convertire JSON in CSV
function json_to_csv($json_data, $csv_file) {
    // Decodifica il JSON in un array PHP
    $data = json_decode($json_data, true);

    if (json_last_error() !== JSON_ERROR_NONE) {
        die('Errore nel decodificare il file JSON');
    }

    // Apertura del file CSV per scrivere
    $csv = fopen($csv_file, 'w');
    
    // Scrittura dell'intestazione CSV
    fputcsv($csv, ['order_reference', 'tracking_number', 'carrier', 'shipping_date']);
    
    // Scrittura dei dati nel file CSV
    foreach ($data as $item) {
        $row = [
            'order_reference' => isset($item['order_reference']) ? $item['order_reference'] : '',
            'tracking_number' => isset($item['tracking_number']) ? $item['tracking_number'] : '',
            'carrier' => isset($item['carrier']) ? $item['carrier'] : '',
            'shipping_date' => isset($item['shipping_date']) ? $item['shipping_date'] : ''
        ];
        fputcsv($csv, $row);
    }

    // Chiusura del file CSV
    fclose($csv);

    echo "Tracciato CSV dei tracking generato con successo: $csv_file\n";
}

// Parametri di connessione SFTP
$sftp_host = 'ws.italagro.bindcommerce.biz';
$sftp_port = 22;  // Porta predefinita per SFTP
$sftp_username = 'wsitalagro';
$sftp_password = 'your_password';  // Sostituire con la tua password SFTP

// Percorso del file JSON remoto sul server SFTP
$remote_path = '/home/wsitalagro/webapps/ws-italagro/tracking_data.json';  // Modifica con il percorso del file JSON

// Percorso di destinazione del file CSV
$csv_file = '/home/wsitalagro/webapps/ws-italagro/tracking/update_tracking.csv';  // Percorso del CSV da generare

// Scarica il file JSON dal server SFTP
$json_data = download_json_from_sftp($sftp_host, $sftp_port, $sftp_username, $sftp_password, $remote_path);

// Se il download è riuscito, procedi con la conversione
json_to_csv($json_data, $csv_file);

?>

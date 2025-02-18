<?php

// Dettagli del server SFTP
$hostname = 'ws.italagro.bindcommerce.biz';  
$port = 22;  
$username = 'wsitalagro';  
$password = 'Q0W80q8oeuKWztztdTd2QL5JphA7lWgP';  

// Percorsi dei file
$remote_file_path = '/home/wsitalagro/webapps/ws-italagro/orders/export_orders.csv';  // File remoto da leggere
$output_file_path = '/home/wsitalagro/webapps/ws-italagro/tracking/export_expedition.csv';  // File CSV da salvare

// Creazione della connessione SFTP
$connection = ssh2_connect($hostname, $port);

if (!$connection) {
    die('Impossibile connettersi al server SFTP.');
}

// Autenticazione con nome utente e password
if (!ssh2_auth_password($connection, $username, $password)) {
    die('Autenticazione fallita.');
}

// Apertura della connessione SFTP
$sftp = ssh2_sftp($connection);

// Verifica se il file remoto esiste
$remote_file = "ssh2.sftp://$sftp$remote_file_path";
if (!file_exists($remote_file)) {
    die("Il file remoto non esiste: $remote_file_path");
}

// Leggi il contenuto del file CSV remoto
$file_content = file_get_contents($remote_file);

// Carica il contenuto CSV in un array
$lines = explode("\n", $file_content);
$header = str_getcsv(array_shift($lines));  // Estrai l'header

// Trova gli indici delle colonne richieste 
$columns_to_select = ['Order Number', 'Tracking Number', 'Carrier', 'OrderDate'];
$selected_columns_indices = [];
foreach ($header as $index => $column_name) {
    if (in_array($column_name, $columns_to_select)) {
        $selected_columns_indices[] = $index;
    }
}

// Seleziona i dati delle colonne desiderate
$selected_data = [];
foreach ($lines as $line) {
    $data = str_getcsv($line);
    if ($data) {
        $selected_data[] = [
            $data[$selected_columns_indices[0]],
            $data[$selected_columns_indices[1]],
            $data[$selected_columns_indices[2]],
            $data[$selected_columns_indices[3]],  
        ];
    }
}

// Crea il contenuto del nuovo file CSV
$new_csv_content = implode(",", $columns_to_select) . "\n";
foreach ($selected_data as $row) {
    $new_csv_content .= implode(",", $row) . "\n";
}

// Salva il nuovo file CSV nella cartella remota
$remote_output_file = "ssh2.sftp://$sftp$output_file_path";
file_put_contents($remote_output_file, $new_csv_content);

echo "File CSV selezionato salvato con successo in: $output_file_path";

// Chiudi la connessione SFTP
ssh2_disconnect($connection);

?>
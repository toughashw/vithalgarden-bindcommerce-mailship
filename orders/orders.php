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
        die('Errore n

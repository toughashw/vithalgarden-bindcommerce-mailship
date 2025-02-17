import json
import csv
import paramiko

# Funzione per scaricare il file JSON da SFTP e convertirlo in CSV
def download_json_from_sftp(sftp_host, sftp_port, sftp_username, sftp_password, remote_path):
    try:
        # Creazione della connessione SFTP
        transport = paramiko.Transport((sftp_host, sftp_port))
        transport.connect(username=sftp_username, password=sftp_password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        # Scarica il file JSON dal server SFTP
        with sftp.open(remote_path, 'r') as remote_file:
            file_data = remote_file.read().decode('utf-8')
        
        # Chiudi la connessione SFTP
        sftp.close()
        transport.close()

        return file_data

    except Exception as e:
        print(f"Errore nel download del file da SFTP: {e}")
        return None

# Funzione per convertire JSON in CSV
def json_to_csv(json_data, csv_file):
    # Carica il file JSON
    data = json.loads(json_data)

    # Verifica se i dati sono una lista di oggetti
    if isinstance(data, list) and all(isinstance(item, dict) for item in data):
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["sku", "ean", "stock"])
            writer.writeheader()

            # Scrivi ogni prodotto nel CSV
            for item in data:
                row = {
                    "sku": item.get("sku", ""),
                    "ean": item.get("ean", ""),
                    "stock": item.get("stock", 0)
                }
                writer.writerow(row)

        print(f"Tracciato CSV generato con successo: {csv_file}")
    else:
        print("Errore: Il file JSON non contiene una lista di oggetti.")

# Parametri di connessione SFTP
sftp_host = 'ws.italagro.bindcommerce.biz'  
sftp_port = 22                            
sftp_username = 'wsitalagro'               
sftp_password = 'your_password'            

# Percorso del file JSON sul server SFTP
remote_path = '/home/wsitalagro/webapps/ws-italagro/input.json'  # Percorso del file JSON sul server SFTP

# Percorso del file CSV di destinazione
csv_file = '/home/wsitalagro/webapps/ws-italagro/products/update_stock.csv'  # Percorso del CSV da generare

# Scarica il file JSON dal server SFTP
json_data = download_json_from_sftp(sftp_host, sftp_port, sftp_username, sftp_password, remote_path)

# Se il download è stato effettuato correttamente, procedi con la conversione
if json_data:
    json_to_csv(json_data, csv_file)

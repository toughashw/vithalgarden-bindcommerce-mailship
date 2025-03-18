import paramiko
import requests
import time
import json
import csv
from io import StringIO
from datetime import datetime
import schedule

# Dati di login
login_url = "https://app.mailship.eu/api/login/user"
refresh_url = "https://app.mailship.eu/api/refresh-token"
expedition_list_url = "https://app.mailship.eu/api/expedition/list"  # Nuovo URL per ottenere la lista delle spedizioni

email = "alessandrocarucci.ac@gmail.com"  # L'email da usare per il login
password = "Alex260981"  # La password

# Dettagli del server SFTP
hostname = 'ws.italagro.bindcommerce.biz'
port = 22
sftp_username = 'wsitalagro'
sftp_password = 'Q0W80q8oeuKWztztdTd2QL5JphA7lWgP'

# Funzione per effettuare il login e ottenere il token
def login():
    headers = {'Content-Type': 'application/json'}
    payload = {
        'login': email,  # Usa l'email come valore per il campo 'login'
        'password': password
    }
    print("Effettuo il Login...")
    response = requests.post(login_url, json=payload, headers=headers)
    
    if response.status_code == 200:
        token_data = response.json()
        token = token_data.get('token')
        expires_in = token_data.get('expires_in')

        if expires_in is None:
            expires_in = 3600  # Impostiamo un valore di default per la durata del token (1 ora)

        return token, expires_in
    else:
        print("Errore durante il login:", response.status_code, response.text)
        return None, None

# Funzione per fare il refresh del token
def refresh_token(refresh_token):
    headers = {'Content-Type': 'application/json'}
    payload = {'refresh_token': refresh_token}
    response = requests.post(refresh_url, json=payload, headers=headers)
    
    if response.status_code == 200:
        token_data = response.json()
        return token_data.get('token'), token_data.get('expires_in')
    else:
        print("Errore durante il refresh del token:", response.status_code, response.text)
        return None, None

# Funzione per fare una richiesta POST a /expedition/list e ottenere le spedizioni
def get_expedition_list(token):
    headers = {
        'Authorization': f'Bearer {token}',  # Includi il token nell'header di autorizzazione
        'Content-Type': 'application/json'
    }
    
    response = requests.post(expedition_list_url, headers=headers)

    if response.status_code == 200:
        # Ottieni la risposta JSON
        expedition_data = response.json()
        print("Scarico la lista spedizioni in formato JSON")

        # Salva la risposta JSON in un file
        with open('expedition_list.json', 'w') as f:
            json.dump(expedition_data, f, indent=4)
        print("Contenuto salvato in 'expedition_list.json'")

        return expedition_data.get('results', [])
    else:
        print("Errore durante la richiesta a /expedition/list:", response.status_code, response.text)
        return []

# Funzione per generare il CSV e caricarlo su SFTP
def generate_csv_and_upload_to_sftp(expedition_list):
    # Aggiungi il timestamp al nome del file di output
    timestamp = datetime.now().strftime('%d-%m-%Y_%H:%M:%S')  # Formato del timestamp (giorno-mese-anno_ora:minuti:secondi)
    remote_file_path = f'/home/wsitalagro/webapps/ws-italagro/products/export_products_api_{timestamp}.csv'  # File CSV da salvare con il timestamp

    # Crea un buffer di memoria (StringIO) per generare il CSV in memoria
    csv_buffer = StringIO()
    fieldnames = ['Order Number', 'Tracking Number', 'Carrier', 'Order Date']
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)

    # Scrive l'intestazione
    writer.writeheader()

    # Scrive i dati per ogni spedizione
    for expedition in expedition_list:
        # Prepara i dati per la nuova struttura
        new_row = {
            'Order Number': expedition.get('orderNumber', ''),
            'Tracking Number': expedition.get('trackingNumber', ''),
            'Carrier': expedition.get('carrier', ''),
            'Order Date': expedition.get('eshopOrderDate', ''),
        }
        writer.writerow(new_row)

    # Dopo aver scritto il CSV nel buffer, procedi a caricarlo su SFTP
    csv_buffer.seek(0)  # Torna all'inizio del buffer per la lettura

    try:
        # Connessione al server SFTP
        transport = paramiko.Transport((hostname, port))
        transport.connect(username=sftp_username, password=sftp_password)
        
        # Crea il client SFTP
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        # Scrive il CSV sul server SFTP
        with sftp.open(remote_file_path, 'w') as remote_file:
            remote_file.write(csv_buffer.getvalue())

        # Aggiungi il timestamp al nome del file di output
        timestamp = datetime.now().strftime('%d-%m-%Y_%H:%M:%S')  # Formato del timestamp (giorno-mese-anno_ora:minuti:secondi)
        remote_file_path = f'/home/wsitalagro/webapps/ws-italagro/tracking/export_tracking_api_{timestamp}.csv'  # File CSV da salvare con il timestamp

        print(f"CSV caricato con successo su SFTP: {remote_file_path}")

    except Exception as e:
        print(f"Errore durante il caricamento del file CSV su SFTP: {e}")
    finally:
        # Chiudi la connessione SFTP
        transport.close()

# Funzione principale per gestire l'autenticazione e il refresh del token
def authenticate():
    token, expires_in = login()
    
    if token:
        print("Login effettuato con successo!")
        print(f"Token ricevuto: {token}")  # Stampa il token dopo il login
        
        # Imposta il tempo di scadenza del token
        expiry_time = time.time() + expires_in
        
        # Usare il token per fare richieste finché non scade
        while True:
            current_time = time.time()
            if current_time >= expiry_time:
                print("Il token è scaduto, rinnovando...")
                token, expires_in = refresh_token(token)
                if token:
                    expiry_time = time.time() + expires_in
                    print("Token rinnovato con successo!")
                else:
                    print("Errore nel rinnovo del token.")
                    break
            else:
                # Chiama la funzione per ottenere le spedizioni se il token è ancora valido
                print("Token valido, faccio la richiesta per le spedizioni...")
                expedition_list = get_expedition_list(token)

                # Genera il CSV con i dati delle spedizioni
                print("Genero il CSV con i dati delle spedizioni...")
                generate_csv_and_upload_to_sftp(expedition_list)
                break  # Esci dal ciclo dopo aver generato il CSV

# Schedula il salvataggio ogni 5 minuti
schedule.every(1).minutes.do(authenticate)

# Loop per eseguire la schedulazione
while True:
    schedule.run_pending()
    time.sleep(30)  # Attendi un minuto prima di controllare di nuovo


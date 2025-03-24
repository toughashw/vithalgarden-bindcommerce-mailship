import paramiko
import requests
import time
import json
import csv
from io import StringIO
from datetime import datetime
import schedule

# API Call - Login & Token
login_url = "https://app.mailship.eu/api/login/user"
refresh_url = "https://app.mailship.eu/api/refresh-token"

# API Call - Reservations
reservations_list_url = "https://app.mailship.eu/api/reservation/list"  

# Login Credentials
email = "alessandrocarucci.ac@gmail.com"
password = "Alex260981"  

# SFTP 
hostname = 'ws.italagro.bindcommerce.biz'
port = 22
sftp_username = 'wsitalagro'
sftp_password = 'Q0W80q8oeuKWztztdTd2QL5JphA7lWgP'

# Login & Token Function
print("Effettuo il login ed ottengo un token valido....")
def login():
    headers = {'Content-Type': 'application/json'}
    payload = {
        'login': email,  
        'password': password
    }

    response = requests.post(login_url, json=payload, headers=headers)

    if response.status_code == 200:
        token_data = response.json()
        token = token_data.get('token')         
        expires_in = token_data.get('expires_in')

        if expires_in is None:
            expires_in = 3600  # durata del token (1 ora)

        return token, expires_in
    else:
        print("Errore durante il login:", response.status_code, response.text)
        return None, None

token = login()
print(f"Token ricevuto con successo: {token}")
print("Login effettuato con successo!\n")

# Refresh Token Function
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

# Funzione per fare una richiesta POST a /reservation/list e ottenere i prodotti
def get_product_list(token):
    headers = {
        'Authorization': f'Bearer {token}',  
        'Content-Type': 'application/json'
    }
    
    response = requests.post(reservation_list_url, headers=headers)

    if response.status_code == 200:
        # Ottieni la risposta JSON
        product_data = response.json()
        print("Scarico la lista prodotti in formato JSON")

        # Salva la risposta JSON in un file
        with open('reservation_list.json', 'w') as f:
            json.dump(product_data, f, indent=4)
        print("Contenuto salvato in 'reservation_list.json'\n")

        return product_data.get('results', [])
    else:
        print("Errore durante la richiesta a /reservation/list:", response.status_code, response.text)
        return []

# Funzione per generare il CSV e caricarlo su SFTP
def generate_csv_and_upload_to_sftp(product_list, product_stock):
    timestamp = datetime.now().strftime('%d-%m-%Y_%H:%M:%S')  
    remote_file_path = f'/home/wsitalagro/webapps/ws-italagro/orders/export_orders_api_{timestamp}.csv'  
    
    print("Genero il CSV aggiornato...")
    csv_buffer = StringIO()
    fieldnames = ['Internal SKU', 'Primary EAN', 'Name', 'Quantity']
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)

    writer.writeheader()

        new_row = {
            'Internal SKU': product.get('internalSku', ''),
            'Primary EAN': product.get('productSku', ''),
            'Name': product.get('name', ''),
            'Quantity': product_quantity
            }
        writer.writerow(new_row)

    csv_buffer.seek(0)

    try:
        # Connessione al server SFTP
        transport = paramiko.Transport((hostname, port))
        transport.connect(username=sftp_username, password=sftp_password)
        
        # Crea il client SFTP
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        # Scrive il CSV sul server SFTP
        with sftp.open(remote_file_path, 'w') as remote_file:
            remote_file.write(csv_buffer.getvalue())

        print(f"CSV caricato con successo su SFTP: {remote_file_path}")
        print("Attendo 5 minuti prima di un nuovo aggiornamento....\n")

    except Exception as e:
        print(f"Errore durante il caricamento del file CSV su SFTP: {e}")
    finally:
        # Chiudi la connessione SFTP
        transport.close()

# Funzione principale per gestire l'autenticazione e il refresh del token
def authenticate():
    token, expires_in = login()
    
    if token:  
        expiry_time = time.time() + expires_in
        
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

                reservation_list = get_reservation_list(token)    
                generate_csv_and_upload_to_sftp(reservation_list)
                break 

# Schedulazione salvataggio CSV ogni 5 minuti
schedule.every(5).minutes.do(authenticate)

# Loop per eseguire la schedulazione
while True:
    schedule.run_pending()
    time.sleep(10)  

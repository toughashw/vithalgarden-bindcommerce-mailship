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

# API Call - Expedition & Carrier | Moviment & Product
expedition_list_url = "https://app.mailship.eu/api/expedition/list"
carrier_list_url = "https://app.mailship.eu/api/carrier/list"
moviment_list_url = "https://app.mailship.eu/api/stock-movement/list"
product_list_url = "https://app.mailship.eu/api/product/list"  

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
        print("Errore durante il login:", response.status_code, response.text)
        return None, None

token = login()
print(f"Token ricevuto con successo: {token}")
print("Login effettuato con successo!\n")

# Refresh Token
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
        'Authorization': f'Bearer {token}',  
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
        print("Contenuto salvato in 'expedition_list.json'\n")

        return expedition_data.get('results', [])
    else:
        print("Errore durante la richiesta a /expedition/list:", response.status_code, response.text)
        return []

# Funzione per fare una richiesta POST a /carrier/list e ottenere la lista dei corrieri
def get_carrier_list(token):
    headers = {
        'Authorization': f'Bearer {token}',  
        'Content-Type': 'application/json'
    }
    
    response = requests.post(carrier_list_url, headers=headers)

    if response.status_code == 200:
        # Ottieni la risposta JSON
        carrier_data = response.json()
        print("Scarico la lista corrieri in formato JSON")

        # Salva la risposta JSON in un file
        with open('carrier_list.json', 'w') as f:
            json.dump(carrier_data, f, indent=4)
        print("Contenuto salvato in 'carrier_list.json'\n")

        return carrier_data.get('results', [])
    else:
        print("Errore durante la richiesta a /carrier/list:", response.status_code, response.text)
        return []

# Funzione per fare una richiesta POST a /moviment/list e ottenere la lista spedizioni assegnate ai corrieri
def get_moviment_list(token):
    headers = {
        'Authorization': f'Bearer {token}',  
        'Content-Type': 'application/json'
    }
    
    response = requests.post(moviment_list_url, headers=headers)

    if response.status_code == 200:
        # Ottieni la risposta JSON
        moviment_data = response.json()
        print("Scarico la lista corrieri in formato JSON")

        # Salva la risposta JSON in un file
        with open('moviment_list.json', 'w') as f:
            json.dump(moviment_data, f, indent=4)
        print("Contenuto salvato in 'moviment_list.json'\n")

        return moviment_data.get('results', [])
    else:
        print("Errore durante la richiesta a /moviment/list:", response.status_code, response.text)
        return []

# Funzione per fare una richiesta POST a /product/list e ottenere i prodotti
def get_product_list(token):
    headers = {
        'Authorization': f'Bearer {token}',  
        'Content-Type': 'application/json'
    }
    
    response = requests.post(product_list_url, headers=headers)

    if response.status_code == 200:
        # Ottieni la risposta JSON
        product_data = response.json()
        print("Scarico la lista prodotti in formato JSON")

        # Salva la risposta JSON in un file
        with open('product_list.json', 'w') as f:
            json.dump(product_data, f, indent=4)
        print("Contenuto salvato in 'product_list.json'\n")

        return product_data.get('results', [])
    else:
        print("Errore durante la richiesta a /product/list:", response.status_code, response.text)
        return []

# Funzione per generare il CSV e caricarlo su SFTP
def generate_csv_and_upload_to_sftp(expedition_list, carrier_list, moviment_list, product_list):
    timestamp = datetime.now().strftime('%d-%m-%Y_%H:%M:%S')  
    remote_file_path = f'/home/wsitalagro/webapps/ws-italagro/orders/export_orders_api_{timestamp}.csv'  
    
    print("Genero il CSV aggiornato...")
    csv_buffer = StringIO()
    fieldnames = ['Order Number', 'Order Date', 'Carrier', 'Status', 'Tracking Number', 'Tracking Url', 'Delivery Date', 'Delivery Firstname', 'Delivery Lastname', 
                  'Delivery Street', 'Delivery House nr', 'Delivery Zip', 'Delivery City', 'Delivery Country', 'Delivery Email', 'Delivery Phone', 'Packages Count', 'SKU Total', 'Piece Total', 'Value', 'Currency']
    
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)

    writer.writeheader()

 # Filtra solo le spedizioni con stato 'delivered'
    delivered_expeditions = [expedition for expedition in expedition_list if expedition.get('status') == 'delivered']

# Cicla sulle spedizioni "delivered"
    for expedition in delivered_expeditions:
         # Trova il movimento corrispondente alla spedizione

        # Trova il nome del corriere associato alla spedizione
        carrier_name = ""
        for carrier in carrier_list:
            if carrier.get('id') == expedition.get('carrier'):  
                carrier_name = carrier.get('name', '')
                break  # Esci dal ciclo non appena trovi il corriere   

        # Scrivi una riga nel CSV
        new_row = {
            'Order Number': expedition.get('orderNumber', ''),
            'Order Date': expedition.get('eshopOrderDate', ''),
            'Carrier': carrier_name,
            'Status': expedition.get('status', ''),
            'Tracking Number': expedition.get('trackingNumber', ''),
            'Tracking Url': expedition.get('trackingUrl', ''),
            'Delivery Date': expedition.get('deliveredAt', ''),
            'Delivery Firstname': expedition.get('deliveryFirstName', ''),
            'Delivery Lastname': expedition.get('deliveryLastName', ''),
            'Delivery Street': expedition.get('deliveryStreet', ''),
            'Delivery House nr': expedition.get('deliveryHouseNr', ''),
            'Delivery Zip': expedition.get('deliveryZip', ''),
            'Delivery City': expedition.get('deliveryCity', ''),
            'Delivery Country': expedition.get('deliveryCountry', ''),
            'Delivery Email': expedition.get('deliveryEmail', ''),
            'Delivery Phone': expedition.get('deliveryPhone', ''),
            'Packages Count': expedition.get('packagesCount', ''),
            'SKU Total': expedition.get('countOfSku', ''),
            'Piece Total': expedition.get('sumOfQuantity', ''),
            'Value': expedition.get('value', ''),
            'Currency': expedition.get('currency', ''),
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

                expedition_list = get_expedition_list(token)
                carrier_list = get_carrier_list(token)
                moviment_list = get_moviment_list(token)
                product_list = get_product_list(token)

                if expedition_list and carrier_list and moviment_list and product_list:
                    generate_csv_and_upload_to_sftp(expedition_list, carrier_list, moviment_list, product_list)
                break 

# Schedulazione salvataggio CSV ogni 5 minuti
schedule.every(1).minutes.do(authenticate)

# Loop per eseguire la schedulazione
while True:
    schedule.run_pending()
    time.sleep(10)  





























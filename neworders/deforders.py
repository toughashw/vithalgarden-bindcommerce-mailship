import paramiko
import re
import os
import io
import csv
import json
import requests
import time
import pandas as pd
from datetime import datetime

# API URL
login_url = "https://app.mailship.eu/api/login/user"
refresh_url = "https://app.mailship.eu/api/refresh-token"
EXPEDITION_URL = "https://app.mailship.eu/api/expedition"
product_list_url = "https://app.mailship.eu/api/product/list"  

# Login Credentials
email = "alessandrocarucci.ac@gmail.com"
password = "Alex260981"

# SFTP
hostname = 'ws.italagro.bindcommerce.biz'
port = 22
sftp_username = 'wsitalagro'
sftp_password = 'Q0W80q8oeuKWztztdTd2QL5JphA7lWgP'
remote_path = '/home/wsitalagro/webapps/ws-italagro/orders/'

# Crea la cartella di output per i file JSON se non esiste
local_output_folder = 'json_orders'
os.makedirs(local_output_folder, exist_ok=True)

# Regex per riconoscere il formato dei file
pattern = re.compile(r'ExportOrders_2-(\d{4}-\d{2}-\d{2})_\d+\.csv')

# Ottieni la data odierna in formato YYYY-MM-DD
today_str = datetime.now().strftime('%Y-%m-%d')

# Connessione SFTP
transport = paramiko.Transport((hostname, port))
transport.connect(username=sftp_username, password=sftp_password)
sftp = paramiko.SFTPClient.from_transport(transport)

# Elenca tutti i file nella directory remota
file_list = sftp.listdir(remote_path)

# Filtra solo i file CSV che rispettano il formato e appartengono al giorno corrente
today_files = [f for f in file_list if pattern.match(f) and today_str in f]

print(f"File trovati per il giorno {today_str}:")
for file in today_files:
    print(" -", file)

# Per ogni file CSV di oggi...
for filename in today_files:
    filepath = remote_path + filename
    with sftp.open(filepath, 'r') as file_handle:
        csv_bytes = file_handle.read()
        csv_content = csv_bytes.decode('utf-8')
        
        try:
            dialect = csv.Sniffer().sniff(csv_content[:1024])
            delimiter = dialect.delimiter
        except Exception:
            delimiter = ','
        
        df = pd.read_csv(io.StringIO(csv_content), delimiter=delimiter)
        
        if "General_bindCommerceNumber" not in df.columns:
            print(f"⚠️  Il file {filename} non contiene la colonna 'General_bindCommerceNumber'.")
            continue

        bind_values = df["General_bindCommerceNumber"].unique()
        for bind_value in bind_values:
            df_group = df[df["General_bindCommerceNumber"] == bind_value]
            json_data = df_group.to_dict(orient='records')
            
            json_filename = filename.replace('.csv', f'_{bind_value}.json')
            json_path = os.path.join(local_output_folder, json_filename)
            
            with open(json_path, 'w', encoding='utf-8') as json_file:
                json.dump(json_data, json_file, indent=2, ensure_ascii=False)
            
            print(f"✅ Salvato: {json_path}")

# Chiude la connessione SFTP
sftp.close()
transport.close()

# Login & Token
print("Effettuo il login ed ottengo un token valido....")
def login():
    headers = {'Content-Type': 'application/json'}
    payload = {'login': email, 'password': password}
    response = requests.post(login_url, json=payload, headers=headers)

    if response.status_code == 200:
        token_data = response.json()
        token = token_data.get('token')
        expires_in = token_data.get('expires_in', 3600)
        return token, expires_in
    else:
        print("Errore durante il login:", response.status_code, response.text)
        return None, None

token, expires_in = login()
if not token:
    exit("❌ Login fallito.")

print(f"Token ricevuto con successo: {token}")
print("Login effettuato con successo!\n")

# Refresh Token
def refresh_token(current_refresh_token):
    headers = {'Content-Type': 'application/json'}
    payload = {'refresh_token': current_refresh_token}
    response = requests.post(refresh_url, json=payload, headers=headers)
    
    if response.status_code == 200:
        token_data = response.json()
        return token_data.get('token'), token_data.get('expires_in', 3600)
    else:
        print("Errore durante il refresh del token:", response.status_code, response.text)
        return None, None

# Scarica lista prodotti
def get_product_list(token):
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    response = requests.post(product_list_url, headers=headers)

    if response.status_code == 200:
        product_data = response.json()
        print("Scarico la lista prodotti in formato JSON")

        os.makedirs('JSON', exist_ok=True)
        with open('JSON/product_list.json', 'w') as f:
            json.dump(product_data, f, indent=4)
        print("Contenuto salvato in 'product_list.json'\n")

        return product_data.get('results', [])
    else:
        print("Errore durante la richiesta a /product/list:", response.status_code, response.text)
        return []

product_list = get_product_list(token)

# Funzione per inviare il payload
def send_payload(payload, token):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.post(EXPEDITION_URL, json=payload, headers=headers)
    
    if response.status_code == 201:
        print("✅ Payload inviato correttamente!")
        print(response.json())
    else:
        print(f"❌ Errore durante l'invio del payload: {response.status_code}")
        print(response.text)

# Funzione principale
def authenticate_and_send_payload(token, expires_in):
    expiry_time = time.time() + expires_in

    
       


def authenticate_and_send_payload():
    for filename in os.listdir(local_output_folder):
        if filename.endswith('.json'):
            json_path = os.path.join(local_output_folder, filename)
            with open(json_path, 'r', encoding='utf-8') as f:
                orders = json.load(f)

            for json_data in orders:
                # Mappa product_id
                for product in product_list:
                    if json_data.get("Row_Barcode") == product.get('productSku'):
                        product_id = product.get('id')
                        break  

                payload = {
                    "eshop": "0fd92368-cf43-431b-a44e-ba773ed246fa",
                    "warehouse": "2d9dd1ec-680f-4cbb-8793-c65cd7ff75bb",
                    "wms": "a3de5778-809e-4fd3-bd22-ffd6db3476fd",
                    "orderNumber": json_data.get("General_Number", ""),
                    "billingFirstName": json_data.get("Customer_Name", ""),
                    "billingLastName": json_data.get("Customer_Surname", ""),
                    "billingStreet": json_data.get("Customer_Address", ""),
                    "billingZip": str(json_data.get("Customer_PostCode", "")),
                    "billingCity": json_data.get("Customer_City", ""),
                    "billingCountry": json_data.get("Customer_CountryCode", ""),
                    "billingEmail": json_data.get("Customer_Email", ""),
                    "billingPhone": str(json_data.get("Customer_Phone", "")),
                    "carrier": "55588c11-769d-4911-924a-c9ff3bd00cca",
                    "value": json_data.get("Amounts_Total", ""),
                    "currency": "EUR",
                    "items": [
                        {
                            "product": product_id,
                            "quantity": json_data.get("Row_Qty", ""),
                            "book": 0,
                            "lifo": "false",
                            "bookStockAdvices": []
                        }
                    ]
                }

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
                send_payload(payload, token)
                time.sleep(300)  # Aspetta 5 minuti prima del prossimo invio

# Esegui la funzione principale
authenticate_and_send_payload()
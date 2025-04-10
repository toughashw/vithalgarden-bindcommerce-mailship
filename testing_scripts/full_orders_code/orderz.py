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

login_url = "https://app.mailship.eu/api/login/user"
refresh_url = "https://app.mailship.eu/api/refresh-token"

EXPEDITION_URL = "https://app.mailship.eu/api/expedition"
product_list_url = "https://app.mailship.eu/api/product/list"  

# Credenziali Login
email = "alessandrocarucci.ac@gmail.com"
password = "Alex260981"

# SFTP
hostname = 'ws.italagro.bindcommerce.biz'
port = 22
sftp_username = 'wsitalagro'
sftp_password = 'Q0W80q8oeuKWztztdTd2QL5JphA7lWgP'
remote_path = '/home/wsitalagro/webapps/ws-italagro/orders/'

# Cartella locale per file JSON
local_output_folder = 'json_orders'
os.makedirs(local_output_folder, exist_ok=True)

# Pattern per file CSV
csv_pattern = re.compile(r'ExportOrders_2-(\d{4}-\d{2}-\d{2})_\d+\.csv')
today_str = datetime.now().strftime('%Y-%m-%d')


def sftp_download_and_convert():
    print("Connessione al server SFTP....\n")
    transport = paramiko.Transport((hostname, port))
    transport.connect(username=sftp_username, password=sftp_password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    
    print("Scarico la lista dei CSV dalla /home/wsitalagro/webapps/ws-italagro/orders/\n")
    file_list = sftp.listdir(remote_path)
    today_files = [f for f in file_list if csv_pattern.match(f) and today_str in f]
    
    print(f"{len(today_files)} files CSV trovati per il giorno {today_str}:\n")
    for file in today_files:
        print("✅ Elenco dei file CSV trovati in Orders", file)
    
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
                print(f"✅ Salvo ordini in formato JSON: {json_filename}")
    
    sftp.close()
    transport.close()

print("Effettuo il login ed ottengo un token valido....")
def login():
    headers = {'Content-Type': 'application/json'}
    payload = {'login': email, 'password': password}
    response = requests.post(login_url, json=payload, headers=headers)
    if response.status_code == 200:
        token_data = response.json()
        return token_data.get('token'), token_data.get('expires_in', 3600)
    else:
        print("❌ Errore durante il login:", response.status_code, response.text)
        return None, None

def refresh_token(current_refresh_token):
    headers = {'Content-Type': 'application/json'}
    payload = {'refresh_token': current_refresh_token}
    response = requests.post(refresh_url, json=payload, headers=headers)
    if response.status_code == 200:
        token_data = response.json()
        return token_data.get('token'), token_data.get('expires_in', 3600)
    else:
        print("❌ Errore durante il refresh del token:", response.status_code, response.text)
        return None, None

print("Login effettuato con successo!\n")

def get_product_list(token):
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    response = requests.post(product_list_url, headers=headers)
    if response.status_code == 200:
        product_data = response.json()
  
        os.makedirs('JSON', exist_ok=True)
        with open('JSON/product_list.json', 'w') as f:
            json.dump(product_data, f, indent=4)

        return product_data.get('results', [])
    else:
        print("❌ Errore durante la richiesta a /product/list:", response.status_code, response.text)
        return []

def send_payload(payload, token):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.post(EXPEDITION_URL, json=payload, headers=headers)
    if response.status_code == 201:
        print("✅ Payload inviato correttamente!")
        print(response.json())
    else:
        print(f"❌ Errore durante l'invio del payload: {response.status_code}")
        print(response.text)

# ========================
# FUNZIONE PRINCIPALE DI INVIO
# ========================

def authenticate_and_send_payload():
    sftp_download_and_convert()

    token, expires_in = login()
    if not token:
        exit("❌ Login fallito.")
    print(f"Token ricevuto con successo: {token}\n")
    
    product_list = get_product_list(token)
    payloads = []

    for filename in os.listdir(local_output_folder):
        if filename.endswith('.json'):
            json_path = os.path.join(local_output_folder, filename)
            with open(json_path, 'r', encoding='utf-8') as f:
                orders = json.load(f)

            for json_data in orders:
                product_id = None
                row_barcode = str(json_data.get("Row_Barcode", "")).strip().lower()
                for product in product_list:
                    if row_barcode == str(product.get('productSku', '')).strip().lower():
                        product_id = product.get('id')
                        break

                if not product_id:
                    print(f"⚠️  Prodotto non trovato per l'ordine {json_data.get('General_Number', 'Sconosciuto')} - SKU: {row_barcode}")
                    continue
                
                payload = {
                    "eshop": "0fd92368-cf43-431b-a44e-ba773ed246fa",
                    "warehouse": "2d9dd1ec-680f-4cbb-8793-c65cd7ff75bb",
                    "wms": "a3de5778-809e-4fd3-bd22-ffd6db3476fd",
                    "orderNumber": str(json_data.get("General_Number", "")),
                    "billingFirstName": json_data.get("Customer_Name", ""),
                    "billingLastName": json_data.get("Customer_Surname", ""),
                    "billingStreet": json_data.get("Customer_Address", ""),
                    "billingZip": str(json_data.get("Customer_Postcode", "")),
                    "billingCity": json_data.get("Customer_City", ""),
                    "billingCountry": json_data.get("Customer_CountryCode", ""),
                    "billingState": json_data.get("Customer_Province", ""),
                    "billingEmail": json_data.get("Customer_Email", ""),
                    "billingPhone": str(json_data.get("Customer_Phone", "")),
                    "carrier": "e6e83624-3d39-413d-a60e-ec8425c41b95",
                    "carrierService": "9c21c5df-464c-444b-841f-f3f7dec7d8e8",
                    "status": order_status,
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
                payloads.append(payload)

    print(f"Numero totale di payloads (orders) da inviare: {len(payloads)}\n")

    expiry_time = time.time() + expires_in
    for payload in payloads:
        current_time = time.time()
        if current_time >= expiry_time:
            print("Il token è scaduto, rinnovando...")
            token, expires_in = refresh_token(token)
            if not token:
                print("❌ Errore nel rinnovo del token. Interrompo l'invio.")
                break
            expiry_time = time.time() + expires_in
            print("Token rinnovato con successo!")
        
        send_payload(payload, token)
        time.sleep(5)

# ========================
# ESECUZIONE DELLO SCRIPT
# ========================
authenticate_and_send_payload()


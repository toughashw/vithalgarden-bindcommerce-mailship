import paramiko
import re
import os
import io
import csv
import json
import requests
import time
import schedule
import shutil
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

# API Call - Login & Token
login_url = "https://app.mailship.eu/api/login/user"
refresh_url = "https://app.mailship.eu/api/refresh-token"

# API Call - Expedition & Product
expedition_url = "https://app.mailship.eu/api/expedition"
product_list_url = "https://app.mailship.eu/api/product/list"

# MailShip Login Credentials
email = "vithalgarden@deliverydaily.org"
password = "APIcall2025!"

#email = "alessandrocarucci.ac@gmail.com"
#password = "Alex260981"

# SFTP
hostname = 'ws.italagro.bindcommerce.biz'
port = 22
sftp_username = 'wsitalagro'
sftp_password = 'Q0W80q8oeuKWztztdTd2QL5JphA7lWgP'
remote_path = '/home/wsitalagro/webapps/ws-italagro/orders/'

# Direttive JSON
local_output_folder = 'json_orders'
processed_folder = os.path.join(local_output_folder, 'processed')
os.makedirs(local_output_folder, exist_ok=True)
os.makedirs(processed_folder, exist_ok=True)

#Funzione lettura solo data di oggi
#csv_pattern = re.compile(r'ExportOrders_2-(\d{4}-\d{2}-\d{2})_\d+\.csv')
#today_str = datetime.now().strftime('%Y-%m-%d')
#today_files = [f for f in file_list if csv_pattern.match(f) and today_str in f]

#Controllo CSV ieri, oggi e domani
#matching_files = [f for f in file_list if date_pattern.match(f)]
#if not matching_files:
     #print("⏸️ Nessun file CSV corrispondente trovato nella directory.")
     #sftp.close()
     #transport.close()
     #return False

# Connessione SFTP e Conversione CSV2JSON
def sftp_download_and_convert():
    print("🔌 Connessione al server SFTP....\n")
    transport = paramiko.Transport((hostname, port))
    transport.connect(username=sftp_username, password=sftp_password)
    sftp = paramiko.SFTPClient.from_transport(transport)

    print("📄 Scarico la lista dei CSV dalla directory /home/wsitalagro/webapps/ws-italagro/orders/ dell'SFTP...\n")
    file_list = sftp.listdir(remote_path)

    # Compila il pattern per estrarre la data dal nome del file
    date_pattern = re.compile(r'ExportOrders_2-(\d{4}-\d{2}-\d{2})_\d+\.csv')
    # Ottieni la data odierna
    today = datetime.now().date()
    yesterday2 = today - timedelta(days=2)
    yesterday3 = today - timedelta(days=3)
    tomorrow = today + timedelta(days=1)

    # Filtra i file con data uguale o successiva a oggi
    #future_files = []
    #for f in file_list:
        #match = date_pattern.match(f)
        #if match:
            #file_date_str = match.group(1)
            #file_date = datetime.strptime(file_date_str, '%Y-%m-%d').date()
            #if file_date >= today:
                #future_files.append(f)
                
    for f in file_list:
         match = date_pattern.match(f)
         if match:
             file_date_str = match.group(1)
             file_date = datetime.strptime(file_date_str, '%Y-%m-%d').date()
             if file_date in [yesterday, yesterday2, yesterday3, today, tomorrow]:
                matching_files.append(f)

    if not matching_files:
        print(f"⏸️ Nessun nuovo file CSV trovato per il giorno {today}.")
        sftp.close()
        transport.close()
        return False

    processed_json_names = set(os.path.splitext(f)[0] for f in os.listdir(processed_folder))
    file_processed = False

    for filename in matching_files:
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
                json_filename = filename.replace('.csv', f'_{bind_value}.json')
                json_base = os.path.splitext(json_filename)[0]
                if json_base in processed_json_names or os.path.exists(os.path.join(local_output_folder, json_filename)):
                        #print(f"⏭️  JSON già presente o già processato: {json_filename}")#
                        continue

                df_group = df[df["General_bindCommerceNumber"] == bind_value]
                json_data = df_group.to_dict(orient='records')
                json_path = os.path.join(local_output_folder, json_filename)
                with open(json_path, 'w', encoding='utf-8') as json_file:
                    json.dump(json_data, json_file, indent=2, ensure_ascii=False)


                print(f"✅ Salvo ordini estratti in formato JSON: {json_filename}")
                file_processed = True

    sftp.close()
    transport.close()
    return file_processed

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
    response = requests.post(expedition_url, json=payload, headers=headers)
    if response.status_code == 201:
        print("✅ Payload inviato correttamente!\n")
        try:
            expedition_id = response.json().get("id")
            if expedition_id:
                send_url = f"{expedition_url}/{expedition_id}/send"
                send_response = requests.put(send_url, headers=headers)

                if send_response.status_code in (200, 201):
                    print(f"📦 Spedizione confermata per ID: {expedition_id}")
                    return True
                else:
                    print(f"⚠️ Errore nella conferma spedizione (PUT): {send_response.status_code}")
                    print(send_response.text)
                    return True
            else:
                print("⚠️ ID spedizione non trovato nella risposta.")
                return False
        except Exception as e:
            print(f"❌ Errore nell'elaborazione della risposta JSON: {str(e)}")
            return False
    elif response.status_code == 400:
        print("⚠️ Payload già inviato (400) o errore lato client, verrà comunque spostato.")
        return True
    else:
        print(f"❌ Errore durante l'invio del payload: {response.status_code}")
        print(response.text)
        return False

def authenticate_and_send_payload():
    file_processed = sftp_download_and_convert()
    if not file_processed:
        print("✅ Nessun nuovo file da processare...\n")
        return

    token, expires_in = login()
    if not token:
        exit("❌ Login fallito.")
    print("\nEffettuo il login ed ottengo un token valido....\n")
    print(f"🔑 Token ricevuto con successo: {token}\n")

    product_list = get_product_list(token)
    expiry_time = time.time() + expires_in

    for filename in os.listdir(local_output_folder):
        if filename.endswith('.json'):
            json_path = os.path.join(local_output_folder, filename)
            with open(json_path, 'r', encoding='utf-8') as f:
                orders = json.load(f)
            
            # Creiamo un dizionario per raggruppare gli articoli per ogni ordine
            orders_dict = {}

            for json_data in orders:
                json_data = {k: ("" if pd.isna(v) else v) for k, v in json_data.items()}
                order_number = str(json_data.get("General_Number", ""))
                row_barcode = str(json_data.get("Row_Barcode", "")).strip().lower()
                row_code = str(json_data.get("Row_Code", "")).strip().lower()
                
                try:
                    barcode = str(int(float(row_barcode))).strip().lower() if row_barcode else ""
                except ValueError:
                    print(f"⚠️ Errore nella conversione del barcode: {row_barcode}")
                    continue

                if not row_barcode or row_barcode == "nan":
        
                    product_id = next((p['id'] for p in product_list if row_code == str(p.get('internalSku', '')).strip().lower()), None)

                else:
  
                    product_id = next((p['id'] for p in product_list if barcode == str(p.get('productSku', '')).strip().lower()), None)

                if not product_id:
                    print(f"⚠️  Prodotto non trovato per l'ordine {json_data.get('General_Number', 'Sconosciuto')} - EAN: {row_barcode} | SKU: {row_code}")
                    continue

                # Raggruppiamo gli articoli per ordine
                if order_number not in orders_dict:
                    orders_dict[order_number] = []
                
                orders_dict[order_number].append({
                    "product": product_id,
                    "quantity": json_data.get("Row_Qty", 0),
                    "book": 0,
                    "lifo": "false",
                    "bookStockAdvices": []
                })
                
            # Creiamo i payload per ogni ordine
            payloads = []  
            for order_number, items in orders_dict.items():  
                payload = {
                    "eshop": "0fd92368-cf43-431b-a44e-ba773ed246fa",
                    "warehouse": "2d9dd1ec-680f-4cbb-8793-c65cd7ff75bb",
                    "wms": "a3de5778-809e-4fd3-bd22-ffd6db3476fd",
                    "orderNumber": order_number,
                    "billingFirstName": json_data.get("Customer_Name", ""),
                    "billingLastName": json_data.get("Customer_Surname", ""),
                    "billingStreet": json_data.get("Customer_Address", ""),
                    "billingZip": str(json_data.get("Customer_Postcode", "")).zfill(5),
                    "billingCity": json_data.get("Customer_City", ""),
                    "billingCountry": json_data.get("Customer_CountryCode", ""),
                    "billingState": json_data.get("Customer_Province", ""),
                    "billingEmail": json_data.get("Customer_Email", ""),
                    "billingPhone": str(json_data.get("Customer_Phone", "")),
                    "carrier": "e6e83624-3d39-413d-a60e-ec8425c41b95",
                    "carrierService": "9c21c5df-464c-444b-841f-f3f7dec7d8e8",
                    "value": json_data.get("Amounts_Total", 0),
                    "currency": "EUR",
                    "items": items
                }
                payloads.append(payload)

            print(f"\n📦 Processo file: {filename} con {len(payloads)} payload...\n")
            all_sent = True

            for payload in payloads:
                if time.time() >= expiry_time:
                    print("🔄 Token scaduto, rinnovo in corso...")
                    token, expires_in = refresh_token(token)
                    if not token:
                        print("❌ Errore nel rinnovo del token.")
                        all_sent = False
                        break
                    expiry_time = time.time() + expires_in
                    print("🔑 Token rinnovato con successo!\n")

                if not send_payload(payload, token):
                    all_sent = False
                    break
                time.sleep(5)

            if all_sent:
                dest_path = os.path.join(processed_folder, filename)
                shutil.move(json_path, dest_path)
                print(f"\n📁 Sposto file: {filename} nella cartella 'json_orders/processed'\n")

def job():
    now = datetime.now(ZoneInfo("Europe/Rome"))
    print(f"🕘 Avvio del job programmato alle {now.strftime('%H:%M')}\n")
    authenticate_and_send_payload()

schedule.every(5).minutes.do(job)

print("⏳ Scheduling avviato. In ascolto per arrivo ordini ogni ora per 24h...\n")

while True:
    schedule.run_pending()
    time.sleep(1)


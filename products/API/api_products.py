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

# API Call - Product & Stock
product_list_url = "https://app.mailship.eu/api/product/list"  
stock_url = "https://app.mailship.eu/api/product-stock/list"  

# Login Credentials
email = "vithalgarden@deliverydaily.org"
password = "APIcall2025!"

#email = "alessandrocarucci.ac@gmail.com"
#password = "Alex260981"

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

# Funzione per fare una richiesta POST a /product/list e ottenere i prodotti
def get_product_list(token):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    all_products = []
    offset = 0
    limit = 1000

    while True:
        payload = {
            "from": offset,
            "limit": limit
        }

        response = requests.post(product_list_url, headers=headers, json=payload)

        if response.status_code != 200:
            print("Errore durante la richiesta a /product/list:", response.status_code, response.text)
            break

        data = response.json()
        products = data.get('results', [])
        all_products.extend(products)

        returned = data.get('paging', {}).get('returned', 0)
        total = data.get('paging', {}).get('total', 0)

        print(f"Scaricati {len(all_products)}/{total} risultati...")

        if offset + returned >= total:
            break  # Tutto scaricato

        offset += returned

    # Crea la cartella JSON se non esiste
    import os
    os.makedirs('JSON', exist_ok=True)

    with open('JSON/product_list.json', 'w') as f:
        json.dump(all_products, f, indent=4)

    print("Tutte le spedizioni salvate in 'product_list.json'\n")
    return all_products

# Funzione per fare una richiesta POST a /stock/list e ottenere ed ottenere quantità prodotti
def get_stock_list(token):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    all_stocks = []
    offset = 0
    limit = 1000

    while True:
        payload = {
            "from": offset,
            "limit": limit
        }

        response = requests.post(stock_list_url, headers=headers, json=payload)

        if response.status_code != 200:
            print("Errore durante la richiesta a /stock/list:", response.status_code, response.text)
            break

        data = response.json()
        stocks = data.get('results', [])
        all_stocks.extend(stocks)

        returned = data.get('paging', {}).get('returned', 0)
        total = data.get('paging', {}).get('total', 0)

        print(f"Scaricati {len(all_stocks)}/{total} risultati...")

        if offset + returned >= total:
            break  # Tutto scaricato

        offset += returned

    # Crea la cartella JSON se non esiste
    import os
    os.makedirs('JSON', exist_ok=True)

    with open('JSON/stock_list.json', 'w') as f:
        json.dump(all_stocks, f, indent=4)

    print("Tutte le spedizioni salvate in 'stock_list.json'\n")
    return all_stocks

# Funzione per generare il CSV e caricarlo su SFTP
def generate_csv_and_upload_to_sftp(product_list, product_stock):
    timestamp = datetime.now().strftime('%d-%m-%Y_%H:%M:%S')  
    remote_file_path = f'/home/wsitalagro/webapps/ws-italagro/products/export_products_api_{timestamp}.csv'  
    
    print("Genero il CSV aggiornato...")
    csv_buffer = StringIO()
    fieldnames = ['Internal SKU', 'Primary EAN', 'Name', 'Quantity']
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)

    writer.writeheader()

    for product in product_list:
        product_quantity = 0  
        for stock in product_stock:
            if product.get('id') == stock.get('product'):
                product_quantity = stock.get('quantity', 0) 
                break  

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

                product_list = get_product_list(token)
                product_stock = get_product_stock(token)

                if product_list and product_stock:
                    generate_csv_and_upload_to_sftp(product_list, product_stock)
                break 

# Schedulazione salvataggio CSV ogni 5 minuti
schedule.every(5).minutes.do(authenticate)

# Loop per eseguire la schedulazione
while True:
    schedule.run_pending()
    time.sleep(5)  

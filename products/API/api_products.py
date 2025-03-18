import requests
import time
import json
import csv

# Dati di login
login_url = "https://app.mailship.eu/api/login/user"
refresh_url = "https://app.mailship.eu/api/refresh-token"
product_list_url = "https://app.mailship.eu/api/product/list"  # URL per ottenere la lista dei prodotti
stock_url = "https://app.mailship.eu/api/product-stock/list"  # URL per ottenere la lista delle quantità

email = "alessandrocarucci.ac@gmail.com"  # L'email da usare per il login
password = "Alex260981"  # La password

# Funzione per effettuare il login e ottenere il token
def login():
    headers = {'Content-Type': 'application/json'}
    payload = {
        'login': email,  # Usa l'email come valore per il campo 'login'
        'password': password
    }

    print("Payload per login:", payload)
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

# Funzione per fare una richiesta POST a /product/list e ottenere i prodotti
def get_product_list(token):
    headers = {
        'Authorization': f'Bearer {token}',  # Includi il token nell'header di autorizzazione
        'Content-Type': 'application/json'
    }
    
    response = requests.post(product_list_url, headers=headers)

    if response.status_code == 200:
        # Ottieni la risposta JSON
        product_data = response.json()
        
         # Salva la risposta JSON in un file
        with open('product_list.json', 'w') as f:
            json.dump(product_data, f, indent=4)
        print("Contenuto salvato in 'product_list.json'")

        # Restituisce la lista dei prodotti
        if isinstance(product_data, dict) and 'results' in product_data:
            product_list = product_data['results']
            return product_list
        else:
            print("La risposta non contiene una lista valida di prodotti.")
            return []
    else:
        print("Errore durante la richiesta a /product/list:", response.status_code, response.text)
        return []

# Funzione per ottenere la quantità di stock per i prodotti
def get_product_stock(token):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    response = requests.post(stock_url, headers=headers)
    
    if response.status_code == 200:
        # Ottieni la risposta JSON
        stock_data = response.json()

         # Salva la risposta JSON in un file
        with open('stock_list.json', 'w') as f:
            json.dump(stock_data, f, indent=4)
        print("Contenuto salvato in 'stock_list.json'")

        # Restituisce un dizionario con id prodotto e quantità
        if isinstance(stock_data, dict) and 'results' in stock_data:
            product_stock = {}
            for item in stock_data['results']:
                # Usa 'product' per l'ID del prodotto
                product_id = item.get('id')  # L'ID del prodotto
                quantity = item.get('quantity')  # La quantità disponibile
                if product_id:
                    product_stock[product_id] = quantity
            return product_stock
        else:
            print("La risposta non contiene una lista valida di stock.")
            return {}
    else:
        print("Errore durante la richiesta a /product-stock/list:", response.status_code, response.text)
        return {}

# Funzione per generare un unico CSV con i dati dei prodotti e le quantità
def generate_csv(product_list, product_stock):
    with open('export_products.csv', mode='w', newline='', encoding='utf-8') as outfile:
        fieldnames = ['Internal SKU', 'Primary EAN', 'Name', 'Quantity']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)

        # Scrive l'intestazione
        writer.writeheader()

        # Scrive i dati per ogni prodotto
        for product in product_list:
            product_id = product.get('id')  # Usa 'internalSku' per identificare il prodotto

            # Aggiungi la quantità al prodotto, se disponibile
            quantity = product_stock.get(product_id, 0)  # Se la quantità non è trovata, metti 0

            # Prepara i dati per la nuova struttura
            new_row = {
                'Internal SKU': product.get('internalSku', ''),
                'Primary EAN': product.get('productSku', ''),
                'Name': product.get('name', ''),
                'Quantity': quantity  # Inseriamo la quantità nel CSV
            }
            writer.writerow(new_row)

    print(f"CSV generato con successo: 'export_product.csv'")

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
                # Chiama la funzione per ottenere i prodotti se il token è ancora valido
                print("Token valido, faccio la richiesta per i prodotti...")
                product_list = get_product_list(token)

                # Ottieni le quantità di stock per ogni prodotto
                print("Recuperando la quantità di stock per ogni prodotto...")
                product_stock = get_product_stock(token)

                # Genera il CSV combinato con i dati dei prodotti e le quantità
                print("Generando il CSV con i dati dei prodotti e le quantità...")
                generate_csv(product_list, product_stock)
                break  # Esci dal ciclo dopo aver generato il CSV

# Esegui lo script di autenticazione
authenticate()

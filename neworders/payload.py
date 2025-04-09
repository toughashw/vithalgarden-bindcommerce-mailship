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
EXPEDITION_URL = "https://app.mailship.eu/api/expedition"

# Login Credentials
email = "alessandrocarucci.ac@gmail.com"
password = "Alex260981"

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
    headers = {'Authorization': f'Bearer {tøoken}','Content-Type': 'application/json'}
    payload = {'refresh_token': refresh_token}
    response = requests.post(refresh_url, json=payload, headers=headers)

    if response.status_code == 200:
        token_data = response.json()
        return token_data.get('token'), token_data.get('expires_in')
    else:
        print("Errore durante il login:", response.status_code, response.text)
        return None, None

token = login()
print(f"Token ricevuto con successo: {token}")
print("Login effettuato con successo!\n")

# Refresh Token Function
def refresh_token(refresh_token):
    headers = {'Authorization': f'Bearer {tøoken}','Content-Type': 'application/json'}
    payload = {'refresh_token': refresh_token}
    response = requests.post(refresh_url, json=payload, headers=headers)

    if response.status_code == 200:
        token_data = response.json()
        return token_data.get('token'), token_data.get('expires_in')
    else:
        print("Errore durante il refresh del token:", response.status_code, response.text)
        return None, None

# Payload di esempio
payload = { 
  "eshop": "0fd92368-cf43-431b-a44e-ba773ed246fa",
  "warehouse": "2d9dd1ec-680f-4cbb-8793-c65cd7ff75bb",
  "wms": "a3de5778-809e-4fd3-bd22-ffd6db3476fd",
  "orderNumber": "test_api",
  "billingFirstName": "Francesco",
  "billingLastName": "Da Lio",
  "billingCompany": "Mailship",
  "billingStreet": "Via Sandro Pertini",
  "billingHouseNr": "3",
  "billingZip": "20074",
  "billingCity": "Carpiano",
  "billingCountry": "IT",
  "billingEmail": "francesco.dalio@mailship.com",
  "billingPhone": "3331686862",
  "carrier": "e6e83624-3d39-413d-a60e-ec8425c41b95",
  "carrierService": "9c21c5df-464c-444b-841f-f3f7dec7d8e8",
  "carrierPickupPlace": null,
  "externalCarrierPickupPlace": null,
  "partner": null,
  "value": "12.3",
  "currency": "EUR",
  "codValue": null,
  "codCurrency": null,
  "codVariableSymbol": null,
  "items": [
    {
      "product": "17fad670-8a1f-4a83-9c86-aec4c0553efa",
      "quantity": 1,
      "book": 0,
      "lot": null,
      "lifo": false,
      "bookStockAdvices": []
    }
  ]
  }  
# Funzione di invio payload
def send_payload(payload, token):
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    response = requests.post(EXPEDITION_URL, json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print("Risposta:", response.json() if response.status_code == 200 else response.text)

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
                send_payload(payload, token)
                time.sleep(5)  # Aspetta 5 minuti prima del prossimo invio

# Schedulazione salvataggio CSV ogni 5 minuti
schedule.every(1).minutes.do(authenticate)

# Loop per eseguire la schedulazione
while True:
    schedule.run_pending()
    time.sleep(5)


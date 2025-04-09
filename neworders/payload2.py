import requests
import time

# API URL
login_url = "https://app.mailship.eu/api/login/user"
refresh_url = "https://app.mailship.eu/api/refresh-token"
EXPEDITION_URL = "https://app.mailship.eu/api/expedition"

# Credenziali di login
email = "alessandrocarucci.ac@gmail.com"
password = "Alex260981"

# Funzione per ottenere il token
def login():
    headers = {'Content-Type': 'application/json'}
    payload = {'login': email, 'password': password}

    response = requests.post(login_url, json=payload, headers=headers)
    if response.status_code == 200:
        token_data = response.json()
        token = token_data.get('token')
        expires_in = token_data.get('expires_in')
        if expires_in is None:
            expires_in = 3600  # 1 ora
        return token, expires_in
    else:
        print("Errore durante il login:", response.status_code, response.text)
        return None, None

# Funzione per rinnovare il token
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

# Payload di esempio per l'API
payload = { 
  "eshop": "0fd92368-cf43-431b-a44e-ba773ed246fa",
  "warehouse": "2d9dd1ec-680f-4cbb-8793-c65cd7ff75bb",
  "wms": "a3de5778-809e-4fd3-bd22-ffd6db3476fd",
  "orderNumber": "test_api_6",
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
  "value": "12.3",
  "currency": "EUR",
  "items": [
    {
      "product": "17fad670-8a1f-4a83-9c86-aec4c0553efa",
      "quantity": 1,
      "book": 0,
      "lifo": "false",
      "bookStockAdvices": []
    }
  ]
}

# Funzione per inviare il payload
def send_payload(payload, token):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.post(EXPEDITION_URL, json=payload, headers=headers)
    
    if response.status_code == 201:
        print("Payload inviato correttamente!")
        data = response.json()
    else:
        print(f"Errore durante l'invio del payload: {response.status_code}")
        print(response.text)

# Funzione principale per la gestione dell'autenticazione e invio del payload
def authenticate_and_send_payload():
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

import requests
import time

# Dati di login
login_url = "https://app.mailship.eu/api/login/user"
refresh_url = "https://app.mailship.eu/api/refresh-token"
email = "alessandrocarucci.ac@gmail.com"  # L'email da usare per il login
password = "Alex260981"

# Funzione per effettuare il login e ottenere il token
def login():
    headers = {'Content-Type': 'application/json'}
    payload = {
        'login': email,  # Usa l'email come valore per il campo 'login'
        'password': password
    }

    # Aggiungi un print per visualizzare il payload
    print("Payload per login:", payload)

    response = requests.post(login_url, json=payload, headers=headers)  # Usa json=payload invece di data=payload
    
    if response.status_code == 200:
        token_data = response.json()
        token = token_data.get('token')
        expires_in = token_data.get('expires_in')

        # Se expires_in è None, imposta un valore di default (ad esempio 3600 secondi, 1 ora)
        if expires_in is None:
            expires_in = 3600  # Impostiamo un valore di default per la durata del token (1 ora)

        return token, expires_in
    else:
        print("Errore durante il login:", response.status_code, response.text)  # Aggiungi il corpo della risposta per maggiore chiarezza
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
                # Qui puoi aggiungere codice per fare richieste protette con il token
                print("Token valido, puoi fare richieste.")
                time.sleep(60)  # Pausa di 60 secondi prima di ricontrollare

# Esegui lo script di autenticazione
authenticate()
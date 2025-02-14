import os
import json
import pandas as pd
import paramiko
from datetime import datetime

# Configurazione SFTP
SFTP_HOST = "ws.italagro.bindcommerce.biz"
SFTP_PORT = 22
SFTP_USER = "wsitalagro"
SFTP_PASS = "LA_TUA_PASSWORD"  


LOCAL_JSON_DIR = "json_orders/"  
LOCAL_CSV_DIR = "csv_orders/"  

# Percorsi remoti
REMOTE_ORDERS_DIR = "/home/wsitalagro/webapps/ws-italagro/orders/"
REMOTE_DONE_DIR = "/home/wsitalagro/webapps/ws-italagro/orders/done/"

# Creazione cartelle locali se non esistono
os.makedirs(LOCAL_CSV_DIR, exist_ok=True)

def convert_json_to_csv(json_file):
    """Converte un file JSON in CSV e lo salva"""
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Adatta il JSON al formato CSV corretto
    df = pd.DataFrame(data)

    # Nome del CSV basato sulla data
    csv_filename = f"ordini_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    csv_path = os.path.join(LOCAL_CSV_DIR, csv_filename)

    # Salva il CSV
    df.to_csv(csv_path, index=False, sep=";")  
    return csv_path, csv_filename

def upload_to_sftp(local_file, remote_path):
    """Carica un file su SFTP"""
    try:
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.connect(username=SFTP_USER, password=SFTP_PASS)

        sftp = transport.open_sftp()
        sftp.put(local_file, remote_path)

        sftp.close()
        transport.close()
        print(f"✅ Upload completato: {remote_path}")
    except Exception as e:
        print(f"❌ Errore SFTP: {e}")

def move_file_on_sftp(remote_file, destination_dir):
    """Sposta un file su SFTP nella cartella 'done/'"""
    try:
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.connect(username=SFTP_USER, password=SFTP_PASS)

        sftp = transport.open_sftp()
        new_remote_path = os.path.join(destination_dir, os.path.basename(remote_file))
        sftp.rename(remote_file, new_remote_path)

        sftp.close()
        transport.close()
        print(f"✅ File spostato in 'done/': {new_remote_path}")
    except Exception as e:
        print(f"❌ Errore nel movimento del file: {e}")

def process_orders():
    """Processa tutti i file JSON nella cartella locale"""
    for file in os.listdir(LOCAL_JSON_DIR):
        if file.endswith(".json"):
            json_path = os.path.join(LOCAL_JSON_DIR, file)

            # Converte JSON in CSV
            csv_path, csv_filename = convert_json_to_csv(json_path)

            # Percorso remoto del file CSV
            remote_csv_path = os.path.join(REMOTE_ORDERS_DIR, csv_filename)

            # Carica su SFTP
            upload_to_sftp(csv_path, remote_csv_path)

            # Sposta il CSV su SFTP nella cartella "done"
            move_file_on_sftp(remote_csv_path, REMOTE_DONE_DIR)

if __name__ == "__main__":
    process_orders()

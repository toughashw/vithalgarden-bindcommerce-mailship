import paramiko
import re
import os
import io
import csv
import json
import pandas as pd
from datetime import datetime

# Parametri di connessione SFTP
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

# Filtra solo i file che rispettano il formato e appartengono al giorno corrente
today_files = [f for f in file_list if pattern.match(f) and today_str in f]

print(f"File trovati per il giorno {today_str}:")
for file in today_files:
    print(" -", file)

# Conversione dei file CSV in JSON
for filename in today_files:
    filepath = remote_path + filename
    with sftp.open(filepath, 'r') as file_handle:
        csv_bytes = file_handle.read()
        csv_content = csv_bytes.decode('utf-8')
        
        # Rileva automaticamente il delimitatore del CSV
        try:
            dialect = csv.Sniffer().sniff(csv_content[:1024])
            delimiter = dialect.delimiter
        except Exception as e:
            # Se il rilevamento fallisce, usa la virgola come default
            delimiter = ','
        
        # Legge il CSV in un DataFrame con il delimitatore individuato
        df = pd.read_csv(io.StringIO(csv_content), delimiter=delimiter)
        json_data = df.to_dict(orient='records')
        
        # Costruisce il percorso locale del file JSON
        json_filename = filename.replace('.csv', '.json')
        json_path = os.path.join(local_output_folder, json_filename)
        
        # Salva il JSON su file locale
        with open(json_path, 'w', encoding='utf-8') as json_file:
            json.dump(json_data, json_file, indent=2, ensure_ascii=False)
        
        print(f"✅ Salvato: {json_path}")

# Chiude la connessione SFTP
sftp.close()
transport.close()

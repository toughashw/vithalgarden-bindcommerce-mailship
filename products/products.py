import paramiko
import pandas as pd
from io import StringIO

# Dettagli del server SFTP
hostname = 'ws.italagro.bindcommerce.biz'  
port = 22  
username = 'wsitalagro'  
password = 'Q0W80q8oeuKWztztdTd2QL5JphA7lWgP'  

# Percorsi dei file
remote_file_path = '/home/wsitalagro/webapps/ws-italagro/orders/export_orders.csv'  # File remoto da leggere
output_file_path = '/home/wsitalagro/webapps/ws-italagro/products/export_product.csv'  # File CSV da salvare

# Connessione al server SFTP
try:
    transport = paramiko.Transport((hostname, port))
    transport.connect(username=username, password=password)
    print("Connessione al server SFTP in corso....")

    # Crea il client SFTP
    sftp = paramiko.SFTPClient.from_transport(transport)
    
    # Leggi il contenuto del file remoto
    print("Leggo il CSV degli Ordini...")
    with sftp.open(remote_file_path, 'r') as remote_file:
        file_content = remote_file.read().decode('utf-8')
    
    # Crea un DataFrame Pandas dal contenuto CSV
    df = pd.read_csv(StringIO(file_content))
    
    # Seleziona solo le colonne richieste 
    print("Genero il nuovo CSV....")    
    colonne_da_selezionare = ['Primary EAN', 'Internal SKU', 'In Stock']
    df_selezionato = df[colonne_da_selezionare]
    
    # Crea un buffer di StringIO per salvare il CSV
    output_buffer = StringIO()
    df_selezionato.to_csv(output_buffer, index=False)
    output_buffer.seek(0)  # Torna all'inizio del buffer
    
    # Salva il nuovo file CSV nella cartella di destinazione
    with sftp.open(output_file_path, 'w') as remote_output_file:
        remote_output_file.write(output_buffer.getvalue())
    
    print(f"File CSV selezionato salvato con successo in: {output_file_path}")
    
except paramiko.AuthenticationException:
    print("Errore di autenticazione. Verifica il nome utente e la password.")
except FileNotFoundError as e:
    print(f"Errore: il file o la cartella non esiste: {e}")
except Exception as e:
    print(f"Errore durante la connessione o l'elaborazione: {e}")
finally:
    # Chiudi la connessione SFTP
    if transport:
        transport.close()


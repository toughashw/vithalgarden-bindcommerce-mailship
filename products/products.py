import paramiko
import pandas as pd
from io import StringIO
import schedule
import time
from datetime import datetime  # Importa datetime per il timestamp

# Funzione per eseguire il salvataggio del CSV
def salva_csv():
    # Dettagli del server SFTP
    hostname = 'ws.italagro.bindcommerce.biz'  
    port = 22  
    username = 'wsitalagro'  
    password = 'Q0W80q8oeuKWztztdTd2QL5JphA7lWgP'  

    # Percorsi dei file
    remote_file_path = '/home/wsitalagro/webapps/ws-italagro/products/products_vg.csv'  # File remoto da leggere
    
    # Aggiungi il timestamp al nome del file di output
    timestamp = datetime.now().strftime('%d-%m-%Y_%H:%M:%S')  # Formato del timestamp (giorno-mese-anno_ora:minuti:secondi)
    output_file_path = f'/home/wsitalagro/webapps/ws-italagro/products/export_products_vg_{timestamp}.csv'  # File CSV da salvare con il timestamp

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
        colonne_da_selezionare = ['Internal SKU', 'Primary EAN', 'Name', 'Quantity']
        df_selezionato = df[colonne_da_selezionare]
        
        # Crea un buffer di StringIO per salvare il CSV
        output_buffer = StringIO()
        df_selezionato.to_csv(output_buffer, index=False)
        output_buffer.seek(0)  # Torna all'inizio del buffer
        
        # Salva il nuovo file CSV nella cartella di destinazione
        with sftp.open(output_file_path, 'w') as remote_output_file:
            remote_output_file.write(output_buffer.getvalue())
        
        print(f"File CSV selezionato salvato con successo in: {output_file_path}")

        # Seleziona solo le colonne richieste 
        print("Attendo 5 minuti per nuovo aggiornamento....") 
        
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

# Schedula il salvataggio ogni 5 minuti
schedule.every(5).minutes.do(salva_csv)

# Loop per eseguire la schedulazione
while True:
    schedule.run_pending()
    time.sleep(60)  # Attendi un minuto prima di controllare di nuovo




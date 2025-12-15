from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
import json
import io
import os

# Name des Ordners im Google Drive (optional, sonst Root)
# Wir werfen es einfach ins Hauptverzeichnis, aber mit spezifischen Namen
FILES = {
    'tasks': 'kairos_tasks.json',
    'schedule': 'kairos_schedule.json'
}

def get_drive_service(creds):
    return build('drive', 'v3', credentials=creds)

def find_file_id(service, filename):
    """Sucht, ob die Datei schon im Drive existiert"""
    results = service.files().list(
        q=f"name = '{filename}' and trashed = false",
        pageSize=1, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])
    if not items:
        return None
    return items[0]['id']

def load_from_drive(creds, file_type, default_data):
    """Lädt JSON aus Drive. Wenn nicht da, nimmt es default_data"""
    try:
        service = get_drive_service(creds)
        filename = FILES[file_type]
        file_id = find_file_id(service, filename)
        
        if not file_id:
            return default_data
            
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            
        fh.seek(0)
        return json.load(fh)
    except Exception as e:
        print(f"Fehler beim Laden von Drive: {e}")
        return default_data

def save_to_drive(creds, file_type, data):
    """Speichert JSON in Drive (überschreibt oder erstellt neu)"""
    try:
        service = get_drive_service(creds)
        filename = FILES[file_type]
        file_id = find_file_id(service, filename)
        
        # Daten in Speicher-Objekt umwandeln
        fh = io.BytesIO(json.dumps(data).encode('utf-8'))
        media = MediaIoBaseUpload(fh, mimetype='application/json')
        
        if file_id:
            # Update existierende Datei
            service.files().update(fileId=file_id, media_body=media).execute()
        else:
            # Erstelle neue Datei
            file_metadata = {'name': filename}
            service.files().create(body=file_metadata, media_body=media).execute()
            
    except Exception as e:
        print(f"Fehler beim Speichern in Drive: {e}")
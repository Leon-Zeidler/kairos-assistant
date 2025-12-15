import os
import json
import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/calendar', 
    'https://www.googleapis.com/auth/gmail.readonly', 
    'https://www.googleapis.com/auth/drive.file'
]

def get_service(service_name='calendar', version='v3'):
    creds = None
    
    # Pfade relativ zum Hauptverzeichnis finden
    base_path = os.getcwd()
    token_path = os.path.join(base_path, 'token.json')
    creds_path = os.path.join(base_path, 'credentials.json')

    # 1. Lokal: Datei
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # 2. Render: Umgebungsvariable
    elif os.getenv("GOOGLE_TOKEN_JSON"):
        token_info = json.loads(os.getenv("GOOGLE_TOKEN_JSON"))
        creds = Credentials.from_authorized_user_info(token_info, SCOPES)

    # 3. Streamlit Secrets
    else:
        try:
            if st.secrets and "token_json" in st.secrets:
                token_info = json.loads(st.secrets["token_json"])
                creds = Credentials.from_authorized_user_info(token_info, SCOPES)
        except: pass

    # Login / Refresh
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Nur speichern, wenn wir nicht auf Render sind
        if not os.getenv("GOOGLE_TOKEN_JSON"):
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
            
    return build(service_name, version, credentials=creds)

def get_creds():
    service = get_service()
    return service._http.credentials
import os.path
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Importiere unser Gehirn
import brain 

SCOPES = ['https://www.googleapis.com/auth/calendar']

def main():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    # 1. Wir schauen uns den heutigen Tag an
    now = datetime.datetime.now()
    # Google braucht Start (Jetzt) und Ende (Heute Nacht)
    time_min = now.isoformat() + 'Z'
    time_max = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0).isoformat() + 'Z'
    
    print(f"--- ANALYSE FÜR: {now.date()} ---")

    # API Abfrage
    events_result = service.events().list(
        calendarId='primary', 
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime').execute()
    events = events_result.get('items', [])

    # Zeige Termine
    if not events:
        print("-> Keine festen Termine gefunden.")
    else:
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(f"[BELEGT] {start[11:16]} Uhr - {event['summary']}")

    # 2. DAS GEHIRN EINSCHALTEN
    print("\n--- BERECHNE FREIE SLOTS (08:00 - 22:00) ---")
    free_slots = brain.find_free_slots(events, now)

    for slot in free_slots:
        # Nur Slots anzeigen, die länger als 15 Min sind
        duration = (slot['end'] - slot['start']).seconds / 60
        if duration > 15:
            start_str = slot['start'].strftime("%H:%M")
            end_str = slot['end'].strftime("%H:%M")
            print(f"[FREI]   {start_str} bis {end_str} ({int(duration)} Min)")

if __name__ == '__main__':
    main()
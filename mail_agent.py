import os
import base64
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from openai import OpenAI
import json
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_gmail_service(creds):
    """Startet den Gmail Dienst mit den gleichen Credentials wie der Kalender"""
    return build('gmail', 'v1', credentials=creds)

def clean_body(html_content):
    """Macht aus HTML-Salat lesbaren Text"""
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text()

def analyze_email_with_ai(subject, body, sender):
    """Fragt GPT, ob das ein Meeting ist"""
    # Text kürzen, um Geld zu sparen (max 1000 Zeichen reichen meist)
    short_body = body[:1000].replace("\n", " ")
    
    prompt = f"""
    ANALYSIERE DIESE EMAIL:
    Von: {sender}
    Betreff: {subject}
    Inhalt: {short_body}
    
    AUFGABE:
    Handelt es sich hier um eine konkrete Anfrage für ein Meeting, Treffen oder einen Termin?
    Falls ja, extrahiere die Daten. Falls nein (oder Newsletter/Spam), antworte mit found: false.
    
    Antworte NUR als JSON:
    {{
        "is_meeting": true,
        "summary": "Titel für Kalender (z.B. Treffen mit Max)",
        "duration_minutes": 60,
        "date_hint": "Datum/Uhrzeit aus dem Text (z.B. 'Morgen 14 Uhr' oder 'Freitag')",
        "reason": "Warum du glaubst, dass es ein Meeting ist"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except:
        return {"is_meeting": False}

def fetch_unread_emails(creds, limit=5):
    """Holt die ungelesenen Mails"""
    service = get_gmail_service(creds)
    
    # Suche nur im Posteingang nach ungelesenen Mails
    results = service.users().messages().list(userId='me', q='is:unread', maxResults=limit).execute()
    messages = results.get('messages', [])
    
    analyzed_emails = []
    
    if not messages:
        return []

    print(f"Scanne {len(messages)} ungelesene Mails...")
    
    for msg in messages:
        # Details laden
        txt = service.users().messages().get(userId='me', id=msg['id']).execute()
        
        # Header (Betreff & Absender) finden
        headers = txt['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "Ohne Betreff")
        sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unbekannt")
        
        # Body dekodieren (Gmail schickt base64)
        try:
            if 'parts' in txt['payload']:
                data = txt['payload']['parts'][0]['body']['data']
            else:
                data = txt['payload']['body']['data']
                
            byte_code = base64.urlsafe_b64decode(data)
            body_text = clean_body(byte_code.decode("utf-8"))
            
            # KI Analyse
            ai_result = analyze_email_with_ai(subject, body_text, sender)
            
            if ai_result.get('is_meeting'):
                analyzed_emails.append({
                    'sender': sender,
                    'subject': subject,
                    'ai_data': ai_result
                })
                
        except Exception as e:
            print(f"Fehler bei Mail {msg['id']}: {e}")
            continue

    return analyzed_emails
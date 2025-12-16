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
    return build('gmail', 'v1', credentials=creds)

def clean_body(html_content):
    """Dein Code: Macht aus HTML lesbaren Text"""
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text()

def get_email_body(service, msg_id):
    """Lädt den vollen Text einer spezifischen Mail (nur bei Bedarf)"""
    try:
        txt = service.users().messages().get(userId='me', id=msg_id).execute()
        
        # Versuche Body zu finden (Plain oder HTML)
        if 'parts' in txt['payload']:
            # Nimm den ersten Part (meistens Text) oder HTML wenn nötig
            parts = txt['payload']['parts']
            data = None
            for p in parts:
                if p['mimeType'] == 'text/plain':
                    data = p['body']['data']
                    break
            if not data and parts: # Fallback
                data = parts[0]['body'].get('data')
        else:
            data = txt['payload']['body'].get('data')

        if not data: return "(No content)"

        byte_code = base64.urlsafe_b64decode(data)
        # Decoding
        try:
            return clean_body(byte_code.decode("utf-8"))
        except:
            return clean_body(byte_code.decode("latin-1")) # Fallback Encoding
            
    except Exception as e:
        return f"Error loading body: {str(e)}"

def fetch_inbox_previews(creds, limit=10):
    """
    SCHNELL: Lädt nur Header (Sender, Betreff, Snippet).
    Keine KI-Analyse hier, damit die App schnell lädt.
    """
    service = get_gmail_service(creds)
    results = service.users().messages().list(userId='me', q='is:unread in:inbox', maxResults=limit).execute()
    messages = results.get('messages', [])
    
    email_list = []
    if not messages: return []

    for msg in messages:
        # Nur Metadata für Speed
        txt = service.users().messages().get(userId='me', id=msg['id'], format='metadata').execute()
        headers = txt['payload']['headers']
        
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
        sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")
        snippet = txt.get('snippet', '')
        
        email_list.append({
            'id': msg['id'],
            'sender': sender,
            'subject': subject,
            'snippet': snippet
        })
            
    return email_list

def analyze_email_task(creds, email_data):
    """
    Wird erst aufgerufen, wenn User auf "Create Task" klickt.
    Lädt Body nach und fragt GPT.
    """
    service = get_gmail_service(creds)
    full_body = get_email_body(service, email_data['id'])
    
    # Kürzen für Token-Limit
    short_body = full_body[:2000].replace("\n", " ")

    prompt = f"""
    ANALYZE THIS EMAIL AND EXTRACT A TASK.
    
    SENDER: {email_data['sender']}
    SUBJECT: {email_data['subject']}
    CONTENT: {short_body}
    
    INSTRUCTIONS:
    1. Summarize into a short Task Title (English).
    2. Estimate duration in minutes.
    3. Categorize (School, Personal, Coding, Sport).
    4. Estimate energy (low, mid, high).
    5. Output JSON.
    
    JSON FORMAT:
    {{
        "title": "Reply to Project X",
        "duration": 15,
        "category": "School",
        "energy": "mid"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(e)
        return {"title": email_data['subject'], "duration": 15, "category": "Personal", "energy": "mid"}
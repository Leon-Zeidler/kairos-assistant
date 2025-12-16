import streamlit as st
from modules import ui
import datetime
import uuid
from modules import storage, auth, ui
from openai import OpenAI
import os
from dotenv import load_dotenv

st.set_page_config(page_title="The Vault", page_icon="🧠", layout="wide")
ui.render_sidebar("Vault")
ui.load_css()
load_dotenv()

# --- SETUP ---
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None
creds = auth.get_creds()

# Daten laden
notes = storage.load_from_drive(creds, 'vault_notes', [])
# Events laden für Verknüpfung
now = datetime.datetime.now()
t_min = (now - datetime.timedelta(days=7)).isoformat() + 'Z'
t_max = (now + datetime.timedelta(days=14)).isoformat() + 'Z'
service = auth.get_service()
events = service.events().list(calendarId='primary', timeMin=t_min, timeMax=t_max, singleEvents=True, orderBy='startTime').execute().get('items', [])
event_options = {e['id']: f"{e['summary']} ({e['start'].get('dateTime', '')[:10]})" for e in events}

# --- AI SUMMARY FUNKTION ---
def summarize_note(content):
    if not client: return "⚠️ Kein API Key."
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Fasse diese Notizen prägnant in Bulletpoints zusammen. Sprache: Deutsch."},
                {"role": "user", "content": content}
            ]
        )
        return response.choices[0].message.content
    except Exception as e: return str(e)

# --- SIDEBAR: LISTE ---
with st.sidebar:
    st.title("🗂️ Archiv")
    if st.button("➕ Neue Notiz", type="primary"):
        st.session_state.current_note_id = None
        st.rerun()
    
    st.markdown("---")
    
    # Suche
    search = st.text_input("Suchen...", placeholder="Titel oder Tag")
    
    # Liste filtern
    filtered_notes = [n for n in notes if search.lower() in n['title'].lower() or search.lower() in n.get('tags', '').lower()]
    
    for note in filtered_notes:
        label = f"📄 {note['title']}"
        if st.button(label, key=note['id'], use_container_width=True):
            st.session_state.current_note_id = note['id']
            st.rerun()

# --- MAIN EDITOR ---
# Bestimmen, welche Notiz wir bearbeiten (Neu oder Existierend)
current_note = None
if getattr(st.session_state, 'current_note_id', None):
    current_note = next((n for n in notes if n['id'] == st.session_state.current_note_id), None)

if not current_note:
    # Template für neue Notiz
    current_note = {"id": str(uuid.uuid4()), "title": "", "content": "", "tags": "", "linked_event": None, "created_at": datetime.datetime.now().isoformat()}

st.title("The Vault 🧠")

# Editor UI
col_meta, col_editor = st.columns([1, 2], gap="large")

with col_meta:
    with st.container(border=True):
        st.subheader("Metadaten")
        new_title = st.text_input("Titel", value=current_note['title'], placeholder="Bio Referat Notizen")
        new_tags = st.text_input("Tags", value=current_note.get('tags', ''), placeholder="Schule, Bio, Wichtig")
        
        # Event Verknüpfung
        current_event_id = current_note.get('linked_event')
        # Wir müssen sicherstellen, dass die ID noch existiert, sonst Index Fehler
        index = 0
        event_ids = list(event_options.keys())
        if current_event_id in event_ids:
            index = event_ids.index(current_event_id) + 1 # +1 wegen "Keine" Option
            
        selected_event = st.selectbox(
            "Verknüpftes Event", 
            options=["Keine"] + list(event_options.values()),
            index=index if current_event_id else 0
        )
        
        # ID zurückrechnen
        linked_id = None
        if selected_event != "Keine":
            # Reverse lookup (etwas hacky aber funktioniert für UI)
            for eid, label in event_options.items():
                if label == selected_event:
                    linked_id = eid
                    break
        
        st.markdown("---")
        if st.button("💾 Speichern", type="primary", use_container_width=True):
            # Update
            current_note['title'] = new_title
            current_note['tags'] = new_tags
            current_note['linked_event'] = linked_id
            
            # In Liste speichern (Update oder Append)
            existing_idx = next((i for i, n in enumerate(notes) if n['id'] == current_note['id']), -1)
            if existing_idx >= 0:
                notes[existing_idx] = current_note
            else:
                notes.append(current_note)
            
            storage.save_to_drive(creds, 'vault_notes', notes)
            st.session_state.current_note_id = current_note['id']
            st.toast("Notiz gesichert!")
            
        if st.button("🗑️ Löschen", type="secondary", use_container_width=True):
            notes = [n for n in notes if n['id'] != current_note['id']]
            storage.save_to_drive(creds, 'vault_notes', notes)
            st.session_state.current_note_id = None
            st.rerun()

    # AI Actions
    with st.expander("✨ AI Tools", expanded=True):
        if st.button("Zusammenfassen", use_container_width=True):
            if current_note['content']:
                with st.spinner("AI liest..."):
                    summary = summarize_note(current_note['content'])
                    st.info(summary)
            else:
                st.warning("Schreib erst etwas.")

with col_editor:
    # Der eigentliche Text-Bereich
    new_content = st.text_area(
        "Inhalt (Markdown unterstützt)", 
        value=current_note['content'], 
        height=600, 
        label_visibility="collapsed",
        placeholder="# Meine Gedanken...\n- Punkt 1\n- Punkt 2"
    )
    # Live Update im State Objekt (Speichern passiert erst beim Button Klick)
    current_note['content'] = new_content
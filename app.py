import streamlit as st
import datetime
import os.path
import json 
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

import brain
import planner
import mail_agent

# --- KONFIGURATION ---
SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/gmail.readonly']
st.set_page_config(page_title="Kairos", page_icon="⏳", layout="wide")

# State Init
if 'suggested_slot' not in st.session_state: st.session_state.suggested_slot = None
if 'tasks' not in st.session_state: st.session_state.tasks = []

# --- FILES ---
SCHEDULE_FILE = 'schedule.json'
TASKS_FILE = 'tasks.json'

def load_json(f, d): return json.load(open(f)) if os.path.exists(f) else d
def save_json(f, d): json.dump(d, open(f, 'w'))

# --- GOOGLE ---
def get_calendar_service():
    creds = None
    
    # 1. Versuch: Lokale Datei (wie bisher auf deinem Mac)
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # 2. Versuch: Cloud Secrets (für Streamlit Cloud)
    elif "token_json" in st.secrets:
        # Wir laden die Infos aus dem geheimen Tresor der Cloud
        token_info = json.loads(st.secrets["token_json"])
        creds = Credentials.from_authorized_user_info(token_info, SCOPES)

    # Wenn wir immer noch keine gültigen Creds haben -> Login starten
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Achtung: Dieser Flow geht NUR lokal auf deinem Mac!
            # Auf dem Server würde das crashen, deshalb ist der 'elif'-Teil oben wichtig.
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Nur lokal speichern, wenn wir auf dem Mac sind
        if not os.path.exists("token.json") and "token_json" not in st.secrets:
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
            
    return build('calendar', 'v3', credentials=creds)

def create_google_event(service, start_dt, end_dt, summary, desc=""):
    service.events().insert(calendarId='primary', body={
        'summary': summary, 'description': desc,
        'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'Europe/Berlin'},
        'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'Europe/Berlin'}
    }).execute()

def sync_week_to_google(service, schedule, ref_date):
    start = ref_date - datetime.timedelta(days=ref_date.weekday())
    c = 0
    for i in range(5):
        d = start + datetime.timedelta(days=i)
        cfg = schedule.get(str(i))
        if cfg and cfg['active'] and cfg['end'] > cfg['start']:
            s = datetime.datetime.combine(d, datetime.time(cfg['start'],0))
            e = datetime.datetime.combine(d, datetime.time(cfg['end'],0))
            create_google_event(service, s, e, "🏫 Schule [Kairos]", "Sync")
            c += 1
    return c

# --- NEUE FUNKTION: WOCHEN-SCAN ---
def collect_week_slots(service, schedule, start_date, days_to_scan=5):
    """Sammelt freie Slots für heute + X Tage"""
    all_slots = []
    now_real = datetime.datetime.now()
    
    for i in range(days_to_scan):
        current_day = start_date + datetime.timedelta(days=i)
        
        # 1. Google Events für diesen Tag holen
        t_min = current_day.isoformat() + 'Z'
        t_max = (current_day + datetime.timedelta(days=1)).isoformat() + 'Z'
        res = service.events().list(calendarId='primary', timeMin=t_min, timeMax=t_max, singleEvents=True).execute()
        g_events = res.get('items', [])
        
        # 2. Schule & Free Slots berechnen
        # WICHTIG: Wir geben 'now_real' mit, damit brain.py die Vergangenheit abschneidet!
        mixed_events = brain.add_school_blocks(g_events, current_day, schedule)
        day_slots = brain.find_free_slots(mixed_events, current_day, current_now=now_real)
        
        all_slots.extend(day_slots)
        
    return all_slots

# --- MAIN ---
def main():
    schedule = load_json(SCHEDULE_FILE, {str(i): {'start':8,'end':14,'active':True} for i in range(5)})
    tasks = load_json(TASKS_FILE, [])
    service = get_calendar_service()
    
    # --- HEADER MIT UHRZEIT ---
    now = datetime.datetime.now()
    st.title("⏳ Kairos Hub")
    st.caption(f"Aktuelle Zeit: {now.strftime('%H:%M')} Uhr | Standort: Deutschland")

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("Einstellungen")
        with st.expander("🏫 Stundenplan"):
            days = ["Mo", "Di", "Mi", "Do", "Fr"]
            changed = False
            for i, d in enumerate(days):
                k = str(i)
                if k not in schedule: schedule[k] = {'start':8,'end':14,'active':True}
                act = st.checkbox(d, schedule[k]['active'], key=f"a{i}")
                if act:
                    times = st.slider(f"{d} Zeit", 7, 18, (schedule[k]['start'], schedule[k]['end']), key=f"t{i}")
                    if schedule[k]['start'] != times[0] or schedule[k]['end'] != times[1]:
                        schedule[k]['start'], schedule[k]['end'] = times[0], times[1]
                        changed = True
                if schedule[k]['active'] != act:
                    schedule[k]['active'] = act
                    changed = True
            if changed: save_json(SCHEDULE_FILE, schedule)
        
        if st.button("🔄 Sync Woche auf Handy"):
            n = sync_week_to_google(service, schedule, datetime.date.today())
            st.success(f"{n} Termine!")

    # --- VIEW CONTROL ---
    col_d1, col_d2 = st.columns([1,3])
    with col_d1:
        view_date = st.date_input("Ansicht:", datetime.date.today())
    search_dt = datetime.datetime.combine(view_date, datetime.datetime.min.time())

    # --- DATEN FÜR HEUTE HOLEN ---
    # Nur für die Anzeige links (Agenda)
    t_min = search_dt.isoformat() + 'Z'
    t_max = (search_dt + datetime.timedelta(days=1)).isoformat() + 'Z'
    ev_res = service.events().list(calendarId='primary', timeMin=t_min, timeMax=t_max, singleEvents=True, orderBy='startTime').execute()
    today_events = brain.add_school_blocks(ev_res.get('items', []), search_dt, schedule)
    
    # --- LAYOUT ---
    c_left, c_right = st.columns(2)
    
    with c_left:
        st.subheader(f"📅 Agenda ({view_date.strftime('%d.%m.')})")
        if not today_events: st.info("Alles frei.")
        for e in today_events:
            if 'start' not in e: continue
            s = brain.parse_time(e['start'].get('dateTime', e['start'].get('date')))
            end = brain.parse_time(e['end'].get('dateTime', e['end'].get('date')))
            
            # Icon Logik
            icon = "▪️"
            if e.get('is_fake'): icon = "🏫"
            elif "Kairos" in e.get('summary', ''): icon = "🤖"
            
            st.write(f"{icon} **{s.strftime('%H:%M')} - {end.strftime('%H:%M')}** | {e['summary']}")

    with c_right:
        st.subheader("📝 Aufgaben Backlog")
        
        # --- FIX: Das Formular stabiler machen ---
        with st.form("new_task_form", clear_on_submit=True):
            st.write("Neue Aufgabe anlegen:")
            
            # Zeile 1: Name und Dauer
            col_in1, col_in2 = st.columns([2, 1])
            new_name = col_in1.text_input("Titel", placeholder="z.B. Bio Referat")
            new_duration = col_in2.number_input("Minuten", value=45, step=15)
            
            # Zeile 2: Deadline Logik
            st.write("Frist (Optional):")
            col_check, col_date = st.columns([1, 2])
            
            # Wir zeigen beides an, das ist stabiler
            use_deadline = col_check.checkbox("Deadline?")
            deadline_pick = col_date.date_input("Datum", datetime.date.today() + datetime.timedelta(days=2))
            
            # Button
            if st.form_submit_button("➕ Hinzufügen"):
                if new_name:
                    final_deadline = None
                    if use_deadline:
                        final_deadline = deadline_pick.strftime("%Y-%m-%d")
                    
                    tasks.append({"name": new_name, "duration": new_duration, "deadline": final_deadline})
                    save_json(TASKS_FILE, tasks)
                    st.rerun()
                else:
                    st.warning("Bitte einen Namen eingeben.")

        st.markdown("---")
        
        # Task List Anzeige
        if not tasks: 
            st.caption("Keine offenen Aufgaben.")
        
        for i, task in enumerate(tasks):
            # Schöne Anzeige mit Warnsymbol
            deadline_display = f"🚨 {task['deadline']}" if task.get('deadline') else ""
            title = f"{task['name']} ({task['duration']}m) {deadline_display}"
            
            with st.expander(title):
                col_btn1, col_btn2 = st.columns(2)
                
                # PLANEN BUTTON
                if col_btn1.button("✨ Auto-Plan", key=f"plan_{i}"):
                    with st.spinner("Prüfe Kalender & Fristen..."):
                        # Wir scannen 5 Tage in die Zukunft
                        week_slots = collect_week_slots(service, schedule, datetime.datetime.now(), days_to_scan=5)
                        
                        proposal = planner.suggest_slot(
                            f"{task['name']} ({task['duration']} min)", 
                            week_slots,
                            deadline_str=task.get('deadline')
                        )
                        st.session_state.suggested_slot = proposal
                        st.session_state.task_to_remove = i
                        st.rerun()
                
                # LÖSCHEN BUTTON
                if col_btn2.button("🗑️ Löschen", key=f"del_{i}"):
                    tasks.pop(i)
                    save_json(TASKS_FILE, tasks)
                    st.rerun()

    # --- RESULT POPUP ---
    if st.session_state.suggested_slot:
        st.divider()
        prop = st.session_state.suggested_slot
        if prop.get("found"):
            st.success(f"💡 Vorschlag: {prop['reason']}")
            # Zeige Datum & Uhrzeit
            st.info(f"📅 **{prop['new_start_time']}** bis **{prop['new_end_time']}**") # Format: YYYY-MM-DD HH:MM
            
            c_ok, c_no = st.columns(2)
            if c_ok.button("✅ Buchen"):
                # String zu DateTime
                s_dt = datetime.datetime.strptime(prop['new_start_time'], "%Y-%m-%d %H:%M")
                e_dt = datetime.datetime.strptime(prop['new_end_time'], "%Y-%m-%d %H:%M")
                
                create_google_event(service, s_dt, e_dt, prop['summary'], "Auto-Planned by Kairos")
                
                # Task löschen
                if st.session_state.task_to_remove is not None:
                    idx = st.session_state.task_to_remove
                    if idx < len(tasks): tasks.pop(idx)
                    save_json(TASKS_FILE, tasks)
                    st.session_state.task_to_remove = None
                
                st.session_state.suggested_slot = None
                st.balloons()
                st.rerun()
                
            if c_no.button("Abbrechen"):
                st.session_state.suggested_slot = None
                st.rerun()
        else:
            st.error(f"Nicht gefunden: {prop.get('reason')}")
            if st.button("Ok"): 
                st.session_state.suggested_slot = None
                st.rerun()

if __name__ == '__main__':
    main()
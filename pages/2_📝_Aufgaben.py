import streamlit as st
import datetime
from modules import storage, auth, planner, brain, ui

st.set_page_config(page_title="Aufgaben", page_icon="📝", layout="wide")
ui.load_css()

# --- HELPER: KALENDER SCAN ---
def collect_week_slots(service, schedule, start_date, days_to_scan=5):
    all_slots = []
    now_real = datetime.datetime.now()
    for i in range(days_to_scan):
        current_day = start_date + datetime.timedelta(days=i)
        t_min = current_day.isoformat() + 'Z'
        t_max = (current_day + datetime.timedelta(days=1)).isoformat() + 'Z'
        res = service.events().list(calendarId='primary', timeMin=t_min, timeMax=t_max, singleEvents=True).execute()
        g_events = res.get('items', [])
        mixed_events = brain.add_school_blocks(g_events, current_day, schedule)
        day_slots = brain.find_free_slots(mixed_events, current_day, current_now=now_real)
        all_slots.extend(day_slots)
    return all_slots

def create_google_event(service, start_dt, end_dt, summary, desc=""):
    service.events().insert(calendarId='primary', body={
        'summary': summary, 'description': desc,
        'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'Europe/Berlin'},
        'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'Europe/Berlin'}
    }).execute()

# --- MAIN ---
service = auth.get_service()
creds = auth.get_creds()
tasks = storage.load_from_drive(creds, 'tasks', [])
schedule = storage.load_from_drive(creds, 'schedule', {})

st.title("Missions")

# --- NEUE AUFGABE ---
with st.expander("➕ Create New Mission", expanded=False):
    with st.form("new_task"):
        c1, c2 = st.columns([3, 1])
        name = c1.text_input("Title", placeholder="e.g. Study Math")
        # Englische Kategorien
        cat = c2.selectbox("Category", ["School", "Personal", "Coding", "Sport"])
        
        c3, c4, c5 = st.columns(3)
        duration = c3.number_input("Minutes", 15, 240, 45, step=15)
        energy = c4.select_slider("Energy Level", options=["low", "mid", "high"], value="mid")
        
        c_dl1, c_dl2 = c5.columns([1,2])
        has_dl = c_dl1.checkbox("Deadline?")
        dl_date = c_dl2.date_input("Date")
        
        if st.form_submit_button("Create Mission"):
            # ... Save logic ... (status: pending)
            st.success("Mission added!")
            st.rerun()

st.write("")

# --- LISTE ---
if not tasks:
    st.info("All clear. No active missions.")
else:
    # State für aktiven Planungs-Vorschlag
    if 'proposal' not in st.session_state: st.session_state.proposal = None
    if 'proposal_idx' not in st.session_state: st.session_state.proposal_idx = None

    for i, t in enumerate(tasks):
        # Einfache Karte im "Clean Look"
        with st.container(border=True):
            c_main, c_actions = st.columns([4, 1])
            
            with c_main:
                energy_icon = "⚡" if t.get('energy') == 'low' else "⚡⚡" if t.get('energy') == 'mid' else "⚡⚡⚡"
                st.write(f"**{t['name']}**")
                st.caption(f"{t['category']} | {t['duration']} Min | {energy_icon} | Frist: {t.get('deadline', '-')}")
            
            with c_actions:
                # PLANEN BUTTON
                if st.button("Plan AI", key=f"plan_{i}"):
                    with st.spinner("Kairos sucht Slot..."):
                        slots = collect_week_slots(service, schedule, datetime.datetime.now(), 5)
                        # Hier rufen wir die neue Planner-Funktion auf!
                        prop = planner.suggest_slot(
                            f"{t['name']} ({t['duration']}m)", 
                            slots, 
                            t.get('deadline'),
                            energy_level=t.get('energy', 'mid') # Energie übergeben!
                        )
                        st.session_state.proposal = prop
                        st.session_state.proposal_idx = i
                        st.rerun()

                if st.button("Delete", key=f"del_{i}"):
                    tasks.pop(i)
                    storage.save_to_drive(creds, 'tasks', tasks)
                    st.rerun()
        
        # --- VORSCHLAG ANZEIGEN (Inline) ---
        # Wir zeigen den Vorschlag nur direkt unter der betroffenen Task an
        if st.session_state.proposal and st.session_state.proposal_idx == i:
            prop = st.session_state.proposal
            
            if prop.get('found'):
                st.info(f"💡 Suggestion: {prop['reason']}")
                c_ok, c_cancel = st.columns(2)
                
                # Button Label mit Zeit
                label = f"Buchen: {prop['new_start_time'][5:]} Uhr"
                
                if c_ok.button(label, key=f"book_{i}", type="primary"):
                    # 1. Google Event
                    s_dt = datetime.datetime.strptime(prop['new_start_time'], "%Y-%m-%d %H:%M")
                    e_dt = datetime.datetime.strptime(prop['new_end_time'], "%Y-%m-%d %H:%M")
                    desc = f"Kategorie: {t['category']} | Energie: {t.get('energy')} | Auto-Plan"
                    create_google_event(service, s_dt, e_dt, prop['summary'], desc)
                    
                    # 2. Task löschen
                    tasks.pop(i)
                    storage.save_to_drive(creds, 'tasks', tasks)
                    
                    # 3. Reset
                    st.session_state.proposal = None
                    st.session_state.proposal_idx = None
                    st.success("Gebucht!")
                    st.rerun()
                    
                if c_cancel.button("Cancel", key=f"cancel_{i}"):
                    st.session_state.proposal = None
                    st.session_state.proposal_idx = None
                    st.rerun()
            else:
                st.error(f"Kein Slot gefunden: {prop.get('reason')}")
                if st.button("Schließen", key=f"close_{i}"):
                    st.session_state.proposal = None
                    st.session_state.proposal_idx = None
                    st.rerun()
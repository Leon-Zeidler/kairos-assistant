import streamlit as st
import datetime
from modules import storage, auth, planner, brain

st.set_page_config(page_title="Mission Control", page_icon="📝", layout="wide")

# --- AUTH & SETUP ---
service = auth.get_service()
creds = auth.get_creds()

# Helper Funktion für Slot-Suche (Lokal definiert für Stabilität)
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

# Daten laden
tasks = storage.load_from_drive(creds, 'tasks', [])
schedule = storage.load_from_drive(creds, 'schedule', {})

st.title("📝 Mission Control")

# --- INPUT BEREICH ---
with st.expander("➕ Neue Mission anlegen", expanded=True):
    with st.form("new_task"):
        c1, c2 = st.columns([2, 1])
        name = c1.text_input("Missions-Titel", placeholder="z.B. Mathe lernen")
        cat = c2.selectbox("Kategorie", ["📚 Schule", "💻 Coding", "⚽ Sport", "🏠 Haushalt", "✨ Sonstiges"])
        
        c3, c4, c5 = st.columns(3)
        duration = c3.number_input("Dauer (Min)", 15, 180, 45, step=15)
        energy = c4.select_slider("Benötigte Energie", options=["⚡ Low", "⚡⚡ Mid", "⚡⚡⚡ High"], value="⚡⚡ Mid")
        
        c_dl_check, c_dl_date = c5.columns([1,2])
        use_dl = c_dl_check.checkbox("Frist?")
        dl_date = c_dl_date.date_input("Datum", datetime.date.today() + datetime.timedelta(days=2))
        
        if st.form_submit_button("In Backlog speichern"):
            new_task = {
                "name": name,
                "category": cat,
                "duration": duration,
                "energy": energy,
                "deadline": dl_date.strftime("%Y-%m-%d") if use_dl else None,
                "created_at": datetime.datetime.now().isoformat()
            }
            tasks.append(new_task)
            storage.save_to_drive(creds, 'tasks', tasks)
            st.success("Gespeichert!")
            st.rerun()

st.divider()

# --- TASK LISTE ---
if not tasks:
    st.info("Alle Systeme sauber. Keine offenen Aufgaben.")
else:
    # Filter Optionen
    filter_cat = st.multiselect("Filter nach Kategorie", options=["📚 Schule", "💻 Coding", "⚽ Sport", "🏠 Haushalt", "✨ Sonstiges"])
    
    view_tasks = tasks
    if filter_cat:
        view_tasks = [t for t in tasks if t['category'] in filter_cat]

    for i, t in enumerate(view_tasks):
        # Index im Original-Array finden (wichtig fürs Löschen)
        original_index = tasks.index(t)
        
        # Visuals
        prio_icon = "🚨" if t.get('deadline') else "📌"
        energy_icon = t.get('energy', '⚡')
        
        with st.container():
            col_info, col_act = st.columns([3, 1])
            
            with col_info:
                st.markdown(f"**{prio_icon} {t['name']}**")
                st.caption(f"{t['category']} | ⏱️ {t['duration']} Min | {energy_icon}")
            
            with col_act:
                c_a1, c_a2 = st.columns(2)
                if c_a1.button("✨", key=f"plan_{i}", help="Automatisch im Kalender planen"):
                    with st.spinner("Kairos berechnet Zeitlinie..."):
                        week_slots = collect_week_slots(service, schedule, datetime.datetime.now(), 5)
                        proposal = planner.suggest_slot(f"{t['name']} ({t['duration']}m)", week_slots, t.get('deadline'))
                        st.session_state.suggested_slot = proposal
                        st.session_state.task_to_remove = original_index
                        st.switch_page("app.py") # Zurück zum Dashboard für Ergebnis
                
                if c_a2.button("🗑️", key=f"del_{i}"):
                    tasks.pop(original_index)
                    storage.save_to_drive(creds, 'tasks', tasks)
                    st.rerun()
            st.markdown("---")
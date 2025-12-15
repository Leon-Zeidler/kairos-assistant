import streamlit as st
import time
import datetime
from modules import storage, auth, ui

st.set_page_config(page_title="Fokus", page_icon="🔥")
ui.load_css()

# --- STATE MANAGEMENT ---
if 'timer_active' not in st.session_state: st.session_state.timer_active = False
if 'end_time' not in st.session_state: st.session_state.end_time = None
if 'selected_task_name' not in st.session_state: st.session_state.selected_task_name = ""

st.title("Fokus Modus")

# --- SETUP BEREICH (Nur sichtbar wenn Timer AUS ist) ---
if not st.session_state.timer_active:
    creds = auth.get_creds()
    tasks = storage.load_from_drive(creds, 'tasks', [])
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Einstellungen")
        task_opts = ["Freier Fokus"] + [t['name'] for t in tasks]
        task_choice = st.selectbox("Aufgabe wählen", task_opts)
        duration = st.number_input("Dauer (Minuten)", min_value=5, max_value=120, value=25, step=5)
        
        if st.button("Starten", type="primary", use_container_width=True):
            st.session_state.timer_active = True
            st.session_state.selected_task_name = task_choice
            # Wir berechnen den Zeitpunkt, wann es fertig ist
            st.session_state.end_time = datetime.datetime.now() + datetime.timedelta(minutes=duration)
            st.rerun()

    with col2:
        st.info("Tipp: Leg dein Handy weg.")

# --- ACTIVE TIMER BEREICH ---
else:
    # Berechnen wie viel Zeit noch übrig ist
    now = datetime.datetime.now()
    remaining = (st.session_state.end_time - now).total_seconds()
    
    if remaining <= 0:
        # FERTIG
        st.balloons()
        st.success("Session beendet!")
        if st.button("Neue Session"):
            st.session_state.timer_active = False
            st.rerun()
    else:
        # LÄUFT NOCH
        mins, secs = divmod(int(remaining), 60)
        time_str = f"{mins:02d}:{secs:02d}"
        
        st.markdown(f"""
        <div style="text-align: center; padding: 40px;">
            <div style="font-size: 1.5rem; color: gray; margin-bottom: 10px;">{st.session_state.selected_task_name}</div>
            <div style="font-size: 6rem; font-weight: 700; font-variant-numeric: tabular-nums;">
                {time_str}
            </div>
            <div style="margin-top: 20px;">
                 Fokus aktiv bis {st.session_state.end_time.strftime('%H:%M')}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Abbrechen Button
        if st.button("Abbrechen"):
            st.session_state.timer_active = False
            st.rerun()
            
        # Automatischer Refresh (Trick: Sleep kurz, dann Rerun)
        # Das hält den Timer am Laufen
        time.sleep(1)
        st.rerun()
import streamlit as st
from streamlit_option_menu import option_menu
import datetime
from modules import storage, auth, brain, ui

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kairos OS", page_icon="⚡", layout="wide")

# Lade das Beams-Design (Hintergrund & Styles)
ui.load_css()

# --- HELPER: HABIT TRACKER (Monochrome Logic) ---
def load_habits(creds):
    # Standard Habits, falls noch keine existieren
    return storage.load_from_drive(creds, 'habits', {
        "READ_LOGS": {},     # Ehemals Lesen
        "HYDRATION": {},     # Ehemals Wasser
        "PHYSICAL_TRAINING": {} # Ehemals Gym
    })

def render_habit_tracker(creds):
    habits = load_habits(creds)
    today_str = datetime.date.today().isoformat()
    
    st.markdown("### ROUTINE PROTOCOLS")
    
    cols = st.columns(len(habits))
    updated = False
    
    for i, (habit_name, history) in enumerate(habits.items()):
        # Streak Logik
        streak = 0
        check_date = datetime.date.today()
        while check_date.isoformat() in history and history[check_date.isoformat()]:
            streak += 1
            check_date -= datetime.timedelta(days=1)
            
        with cols[i]:
            # Silver / Glass Card Style für Habits
            is_done = history.get(today_str, False)
            
            # Monochrome Farben
            bg_color = "rgba(171, 171, 171, 0.1)" if is_done else "rgba(0,0,0,0.2)"
            border = "rgba(171, 171, 171, 0.8)" if is_done else "rgba(171, 171, 171, 0.1)"
            text_col = "#ffffff" if is_done else "#64748b"
            
            st.markdown(f"""
            <div style="background:{bg_color}; border:1px solid {border}; border-radius:4px; padding:15px; text-align:center; transition:all 0.3s;">
                <div style="font-family: monospace; font-size: 0.8rem; color: #ababab; letter-spacing: 1px;">{habit_name}</div>
                <div style="font-size:1.8rem; color: {text_col}; margin: 5px 0;">{streak}</div>
                <div style="font-size:0.6rem; color:#475569; text-transform:uppercase;">Streak Count</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Checkbox
            if st.checkbox("EXECUTE", value=is_done, key=f"habit_{i}"):
                if not is_done:
                    habits[habit_name][today_str] = True
                    updated = True
            else:
                if is_done:
                    habits[habit_name][today_str] = False
                    updated = True
                    
    if updated:
        storage.save_to_drive(creds, 'habits', habits)
        st.rerun()

# --- NAVIGATION SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3652/3652191.png", width=40)
    st.markdown("<h3 style='margin-top:0;'>KAIROS KERNEL</h3>", unsafe_allow_html=True)
    
    # Menü im technischen Look
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Calendar", "Tasks", "Focus", "Vault", "Chat", "Settings"], 
        icons=["speedometer2", "calendar-week", "list-check", "bullseye", "archive", "chat-dots", "gear"],
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#64748b", "font-size": "14px"}, 
            "nav-link": {
                "font-size": "13px", 
                "text-align": "left", 
                "margin":"5px", 
                "font-family": "monospace",
                "--hover-color": "rgba(255,255,255,0.05)"
            },
            "nav-link-selected": {
                "background-color": "rgba(171, 171, 171, 0.1)", 
                "color": "#fff", 
                "border-left": "2px solid #ababab"
            },
        }
    )
    
    st.markdown("---")
    creds = auth.get_creds()
    tasks = storage.load_from_drive(creds, 'tasks', [])
    open_t = len([t for t in tasks if t.get('status') != 'completed'])
    st.caption(f"🟢 SYSTEM ONLINE | {open_t} TASKS PENDING")

# --- MAIN ROUTING ---
def main():
    service = auth.get_service()

    if selected == "Dashboard":
        show_dashboard(service, tasks)
    elif selected == "Calendar":
        st.switch_page("pages/1_📅_Kalender.py")
    elif selected == "Tasks":
        st.switch_page("pages/2_📝_Tasks.py")
    elif selected == "Focus":
        st.switch_page("pages/3_🔥_Fokus.py")
    elif selected == "Vault":
        st.switch_page("pages/6_🧠_Vault.py")
    elif selected == "Chat":
        st.switch_page("pages/4_💬_Chat.py")
    elif selected == "Settings":
        st.switch_page("pages/5_⚙️_Settings.py")

# --- DASHBOARD VIEW (BEAMS THEME) ---
def show_dashboard(service, tasks):
    # Begrüßung: Sehr technisch / Sci-Fi
    c_head1, c_head2 = st.columns([3, 1])
    with c_head1:
        st.markdown(f"# SYSTEM ACTIVE.")
        st.markdown(f"<p style='color: #ababab; margin-top: -15px; font-family: monospace;'>User ID: {creds.get('client_id', 'UNK')[:8]}... // Operating Environment: Stable.</p>", unsafe_allow_html=True)
    
    st.write("") 

    # Metrics Calculation
    open_tasks = len([t for t in tasks if t.get('status') != 'completed'])
    total_mins = sum([int(t.get('duration', 0)) for t in tasks if t.get('status') != 'completed'])
    
    sorted_tasks = sorted([t for t in tasks if t.get('deadline')], key=lambda x: x['deadline'])
    dl_info = "STANDBY"
    dl_name = "NO TARGETS"
    if sorted_tasks:
        dl_name = sorted_tasks[0]['name']
        d = datetime.datetime.strptime(sorted_tasks[0]['deadline'], "%Y-%m-%d").date()
        diff = (d - datetime.date.today()).days
        dl_info = f"T-MINUS {diff}D" if diff > 0 else "CRITICAL"

    # KPI Cards (Monochrome Icons)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(ui.card("MISSIONS", str(open_tasks), "PENDING EXECUTION", "⚡"), unsafe_allow_html=True)
    with c2: st.markdown(ui.card("LOAD", f"{total_mins}m", "ESTIMATED TIME", "⏳"), unsafe_allow_html=True)
    with c3: st.markdown(ui.card("PRIORITY TARGET", dl_name[:12]+".." if len(dl_name)>12 else dl_name, dl_info, "🎯"), unsafe_allow_html=True)
    with c4: st.markdown(ui.card("KERNEL", "v2.3", "ONLINE", "💾"), unsafe_allow_html=True)

    st.markdown("---")
    
    # Habit Tracker
    render_habit_tracker(creds)
    
    st.markdown("---")
    
    # Timeline & Actions
    col_main, col_side = st.columns([2, 1], gap="large")
    
    with col_main:
        st.subheader("TIMELINE")
        now = datetime.datetime.now()
        t_min = now.replace(hour=0, minute=0).isoformat() + 'Z'
        t_max = now.replace(hour=23, minute=59).isoformat() + 'Z'
        events = service.events().list(calendarId='primary', timeMin=t_min, timeMax=t_max, singleEvents=True, orderBy='startTime').execute().get('items', [])
        
        if not events:
            st.info("NO TIMELINE ENTRIES FOUND.")
        else:
            for e in events:
                start = e['start'].get('dateTime', e['start'].get('date'))
                if not start: continue
                dt = brain.parse_time(start)
                is_past = dt < now
                
                # Visual Logic: Past events are dimmed
                opacity = "0.3" if is_past else "1.0"
                # Silver border for active events, faint for past
                border_color = "rgba(171, 171, 171, 0.6)" if not is_past else "rgba(171, 171, 171, 0.1)"
                time_str = dt.strftime('%H:%M')
                
                # Tech-Look Event Card
                st.markdown(f"""
                <div style="
                    display: flex; gap: 20px; margin-bottom: 8px; opacity: {opacity}; align-items: center;
                    background: rgba(0,0,0,0.3); padding: 12px; border-radius: 4px; 
                    border-left: 2px solid {border_color}; font-family: monospace;
                ">
                    <div style="color: #ababab; font-weight: bold;">{time_str}</div>
                    <div style="color: #fff; letter-spacing: 0.5px;">{e['summary']}</div>
                </div>
                """, unsafe_allow_html=True)

    with col_side:
        st.subheader("COMMANDS")
        # Standard Streamlit Buttons nehmen jetzt das CSS aus ui.py an (Silver Look)
        if st.button("INITIALIZE FOCUS PROTOCOL", use_container_width=True):
            st.switch_page("pages/3_🔥_Fokus.py")
            
        st.write("")
        if st.button("NEW DIRECTIVE (TASK)", use_container_width=True):
            st.switch_page("pages/2_📝_Tasks.py")
            
        st.write("")
        with st.expander("SYSTEM LOG"):
            st.caption('All systems functioning within normal parameters.')

if __name__ == '__main__':
    main()
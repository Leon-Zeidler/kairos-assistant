import streamlit as st
from streamlit_option_menu import option_menu
import datetime
from modules import storage, auth, brain, ui

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kairos OS", page_icon="⚡", layout="wide")
ui.load_css()

# --- NAVIGATION ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3652/3652191.png", width=50)
    st.markdown("### Kairos OS")
    
    # ENGLISH MENU
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Calendar", "Missions", "Focus", "Chat"], # En
        icons=["speedometer2", "calendar-week", "list-check", "bullseye", "chat-dots"],
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#94a3b8", "font-size": "16px"}, 
            "nav-link": {"font-size": "14px", "text-align": "left", "margin":"5px", "--hover-color": "#1e293b"},
            "nav-link-selected": {"background-color": "#2563eb", "color": "white", "font-weight": "600"},
        }
    )
    
    st.markdown("---")
    creds = auth.get_creds()
    tasks = storage.load_from_drive(creds, 'tasks', [])
    open_t = len([t for t in tasks if t.get('status') != 'completed'])
    st.caption(f"🚀 {open_t} Active Missions") # En

# --- ROUTING ---
def main():
    service = auth.get_service()

    if selected == "Dashboard":
        show_dashboard(service, tasks)
    elif selected == "Calendar":
        st.switch_page("pages/1_📅_Kalender.py")
    elif selected == "Missions":
        st.switch_page("pages/2_📝_Aufgaben.py")
    elif selected == "Focus":
        st.switch_page("pages/3_🔥_Fokus.py")
    elif selected == "Chat":
        st.switch_page("pages/4_💬_Chat.py")

# --- DASHBOARD VIEW (ENGLISH) ---
def show_dashboard(service, tasks):
    hour = datetime.datetime.now().hour
    greeting = "Good Morning" if hour < 12 else "Good Afternoon" if hour < 18 else "Good Evening"
    
    c_head1, c_head2 = st.columns([3, 1])
    with c_head1:
        st.markdown(f"# {greeting}, Commander.")
        st.markdown(f"<p style='color: #94a3b8; margin-top: -15px;'>All systems operational. Here is your status report.</p>", unsafe_allow_html=True)
    
    st.write("") 

    # Metrics
    open_tasks = len([t for t in tasks if t.get('status') != 'completed'])
    total_mins = sum([int(t.get('duration', 0)) for t in tasks if t.get('status') != 'completed'])
    
    # Next Deadline
    sorted_tasks = sorted([t for t in tasks if t.get('deadline')], key=lambda x: x['deadline'])
    dl_info = "Clear"
    dl_name = "No deadlines"
    if sorted_tasks:
        dl_name = sorted_tasks[0]['name']
        d = datetime.datetime.strptime(sorted_tasks[0]['deadline'], "%Y-%m-%d").date()
        diff = (d - datetime.date.today()).days
        dl_info = f"in {diff} days" if diff > 1 else "⚠️ Due Tomorrow" if diff == 1 else "🚨 DUE TODAY"

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(ui.card("Active Missions", str(open_tasks), "Pending", "⚡"), unsafe_allow_html=True)
    with c2: st.markdown(ui.card("Workload", f"{total_mins}m", "Scheduled today", "⏱️"), unsafe_allow_html=True)
    with c3: st.markdown(ui.card("Priority", dl_name[:15]+"..." if len(dl_name)>15 else dl_name, dl_info, "🔥"), unsafe_allow_html=True)
    with c4: st.markdown(ui.card("System Status", "Online", "V 2.1 Stable", "🟢"), unsafe_allow_html=True)

    st.markdown("---")
    
    col_main, col_side = st.columns([2, 1], gap="large")
    
    with col_main:
        st.subheader("📅 Timeline")
        now = datetime.datetime.now()
        t_min = now.replace(hour=0, minute=0).isoformat() + 'Z'
        t_max = now.replace(hour=23, minute=59).isoformat() + 'Z'
        events = service.events().list(calendarId='primary', timeMin=t_min, timeMax=t_max, singleEvents=True, orderBy='startTime').execute().get('items', [])
        
        if not events:
            st.info("🎉 Free day! No events scheduled.")
        else:
            for e in events:
                start = e['start'].get('dateTime', e['start'].get('date'))
                if not start: continue
                dt = brain.parse_time(start)
                is_past = dt < now
                opacity = "0.5" if is_past else "1.0"
                border_color = "#3b82f6" if not is_past else "#475569"
                
                # 12h format for English feel
                time_str = dt.strftime('%I:%M %p')
                
                st.markdown(f"""
                <div style="
                    display: flex; gap: 15px; margin-bottom: 12px; opacity: {opacity}; align-items: center;
                    background: rgba(255,255,255,0.03); padding: 12px; border-radius: 12px; border-left: 4px solid {border_color};
                ">
                    <div style="font-weight: 700; color: #fff; font-family: monospace; width: 80px;">{time_str}</div>
                    <div style="color: #cbd5e1;">{e['summary']}</div>
                </div>
                """, unsafe_allow_html=True)

    with col_side:
        st.subheader("Quick Actions")
        if st.button("🔥 Enter Focus Mode", use_container_width=True):
            st.switch_page("pages/3_🔥_Fokus.py")
            
        st.write("")
        if st.button("➕ Add Mission", use_container_width=True):
            st.switch_page("pages/2_📝_Aufgaben.py")
            
        st.write("")
        with st.expander("💡 Daily Quote"):
            st.caption('"The future depends on what you do today."')

if __name__ == '__main__':
    main()
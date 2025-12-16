import streamlit as st
import datetime
from modules import storage, auth, brain, ui, audio

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kairos Command", page_icon="⚡", layout="wide")

# --- 1. GLOBAL COMMAND CENTER CSS ---
st.markdown("""
    <style>
        /* HIDE DEFAULT ELEMENTS */
        header[data-testid="stHeader"], div[data-testid="stDecoration"], footer {display: none;}
        
        /* FULL MONITOR WIDTH & SPACING */
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 100% !important; /* Stretch to full width */
        }

        /* --- GLOBAL THEME --- */
        .stApp {
            background-color: #09090b; /* Deep Black/Zinc */
            color: #e4e4e7;
            font-family: 'Inter', sans-serif;
        }

        /* --- TEXT TYPOGRAPHY --- */
        .sub-text { 
            color: #71717a; 
            font-size: 0.75rem; 
            text-transform: uppercase; 
            letter-spacing: 1.2px; 
            font-weight: 600; 
            margin-bottom: 10px;
            display: block;
        }
        .hero-text { font-size: 3rem; font-weight: 800; color: white; letter-spacing: -1.5px; line-height: 1; }
        .accent-text { color: #3b82f6; } 

        /* --- UI BLOCKS (THE GRID) --- */
        /* Einheits-Look für alle Panels */
        .dashboard-panel {
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 12px;
            padding: 20px;
            height: 100%; /* Füllt die Spalte */
        }

        /* --- 1. STATUS BAR --- */
        .status-bar-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 8px;
            padding: 12px 25px;
            margin-bottom: 20px;
        }
        .status-item { display: flex; align-items: center; gap: 10px; font-size: 0.9rem; color: #a1a1aa; }
        .status-value { color: #e4e4e7; font-weight: 600; font-family: monospace; font-size: 1rem; }
        
        /* --- 2. HERO FOCUS CARD --- */
        .hero-card {
            background: radial-gradient(circle at 50% 100%, rgba(59, 130, 246, 0.1) 0%, rgba(9, 9, 11, 0) 50%), 
                        linear-gradient(180deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0) 100%);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 50px 20px;
            text-align: center;
            margin-bottom: 20px;
            position: relative;
            overflow: hidden;
        }
        
        /* --- 3. HABIT BARS --- */
        .habit-row {
            display: flex; align-items: center; justify-content: space-between;
            background: rgba(0,0,0,0.3);
            margin-bottom: 8px;
            padding: 10px 15px;
            border-radius: 8px;
            border-left: 3px solid #27272a;
            transition: all 0.2s;
        }
        .habit-row.done { border-left-color: #10b981; background: rgba(16, 185, 129, 0.05); }
        .habit-name { font-size: 0.9rem; color: #e4e4e7; font-weight: 500; }
        .habit-streak { font-size: 0.7rem; color: #71717a; font-family: monospace; }

        /* --- 4. TIMELINE --- */
        .timeline-item {
            padding: 12px 0;
            border-bottom: 1px solid rgba(255,255,255,0.04);
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .timeline-item:last-child { border-bottom: none; }
        .timeline-time { 
            font-family: monospace; 
            font-size: 0.9rem; 
            color: #71717a; 
            min-width: 50px;
        }
        .timeline-content { font-size: 0.95rem; color: #d4d4d8; }
        .timeline-active { color: #3b82f6; font-weight: 600; }
        .timeline-past { opacity: 0.4; }

        /* --- BUTTONS --- */
        .stButton button {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            color: #d4d4d8;
            border-radius: 8px;
            height: 45px;
            font-weight: 500;
            transition: all 0.2s;
        }
        .stButton button:hover {
            border-color: #71717a;
            background: rgba(255,255,255,0.1);
            color: white;
        }
        /* Focus CTA */
        .primary-cta button {
            background: #2563eb !important;
            border: 1px solid #3b82f6 !important;
            color: white !important;
            box-shadow: 0 0 20px rgba(37, 99, 235, 0.3);
        }
        .primary-cta button:hover {
            box-shadow: 0 0 30px rgba(37, 99, 235, 0.5);
            transform: scale(1.01);
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. LOGIC & DATA PREP ---
selected_page = ui.render_sidebar(active_page="Dashboard")

if selected_page == "Dashboard":
    # Data Loading
    creds = auth.get_creds()
    service = auth.get_service()
    tasks = storage.load_from_drive(creds, 'tasks', [])
    
    # Calc Metrics
    open_tasks = [t for t in tasks if t.get('status') != 'completed']
    open_count = len(open_tasks)
    total_mins = sum([int(t.get('duration', 0)) for t in open_tasks])
    
    sorted_tasks = sorted([t for t in open_tasks if t.get('deadline')], key=lambda x: x['deadline'])
    next_deadline = sorted_tasks[0]['name'] if sorted_tasks else "NONE"
    
    hour = datetime.datetime.now().hour
    greeting = "GOOD MORNING" if hour < 12 else "GOOD AFTERNOON" if hour < 18 else "GOOD EVENING"
    
    # --- LAYOUT ROW 1: HEADER & ACTIONS ---
    c_head, c_btn = st.columns([3, 1], gap="large")
    with c_head:
        st.markdown(f"""
            <div style="display:flex; align-items:center; gap:15px; margin-bottom: 5px;">
                <span class="sub-text" style="margin:0; color:#10b981;">● SYSTEM ONLINE</span>
                <span class="sub-text" style="margin:0;">V 3.0 STABLE</span>
            </div>
            <div style="font-size:2rem; font-weight:700; color:white; letter-spacing:-0.5px;">{greeting}, COMMANDER.</div>
        """, unsafe_allow_html=True)
    
    with c_btn:
        st.markdown('<div class="primary-cta">', unsafe_allow_html=True)
        if st.button("⚡ ENGAGE FOCUS MODE", use_container_width=True):
            st.switch_page("pages/3_🔥_Focus.py")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True) # Spacer

    # --- LAYOUT ROW 2: STATUS BAR (Full Width) ---
    st.markdown(f"""
    <div class="status-bar-container">
        <div class="status-item"><span>⚡</span> <span>MISSIONS:</span> <span class="status-value">{open_count}</span></div>
        <div class="status-item"><span>⏳</span> <span>LOAD:</span> <span class="status-value">{total_mins}m</span></div>
        <div class="status-item"><span>🎯</span> <span>PRIORITY:</span> <span class="status-value">{next_deadline[:20]}</span></div>
        <div class="status-item"><span>📆</span> <span>DATE:</span> <span class="status-value">{datetime.datetime.now().strftime('%b %d')}</span></div>
    </div>
    """, unsafe_allow_html=True)

    # --- LAYOUT ROW 3: HERO FOCUS CARD (Full Width) ---
    primary_task = sorted_tasks[0] if sorted_tasks else (open_tasks[0] if open_tasks else None)
    
    if primary_task:
        task_name = primary_task['name']
        task_sub = f"{primary_task.get('duration', 30)} MIN • {primary_task.get('category', 'General')}"
    else:
        task_name = "ALL SYSTEMS CLEAR"
        task_sub = "NO ACTIVE OBJECTIVES"

    st.markdown(f"""
    <div class="hero-card">
        <div class="sub-text" style="color:#3b82f6; margin-bottom:15px;">CURRENT OBJECTIVE</div>
        <div class="hero-text">{task_name}</div>
        <div style="color:#71717a; margin-top:15px; font-weight:500; font-family:monospace;">{task_sub}</div>
    </div>
    """, unsafe_allow_html=True)

    # --- LAYOUT ROW 4: MAIN GRID (Timeline Left, Habits Right) ---
    # Hier nutzen wir Grid-Logik für perfektes Alignment
    
    col_timeline, col_right = st.columns([1.5, 1], gap="medium")

    # --- BLOCK 1: TIMELINE PANEL ---
    with col_timeline:
        # Wir starten den visuellen Container
        st.markdown('<div class="dashboard-panel">', unsafe_allow_html=True)
        st.markdown('<span class="sub-text">TIMELINE PROTOCOL</span>', unsafe_allow_html=True)
        
        # Timeline Logic
        now = datetime.datetime.now()
        t_min = now.replace(hour=0, minute=0).isoformat() + 'Z'
        t_max = now.replace(hour=23, minute=59).isoformat() + 'Z'
        events = service.events().list(calendarId='primary', timeMin=t_min, timeMax=t_max, singleEvents=True, orderBy='startTime').execute().get('items', [])

        if not events:
            st.caption("No signals detected on timeline.")
        else:
            for e in events:
                start = e['start'].get('dateTime', e['start'].get('date'))
                if not start: continue
                dt = brain.parse_time(start)
                is_past = dt < now.astimezone()
                
                # Styles calc
                opacity_class = "timeline-past" if is_past else ""
                active_style = "color:white;" if not is_past else ""
                icon = "⚪" if is_past else "🔵"
                
                st.markdown(f"""
                <div class="timeline-item {opacity_class}">
                    <div class="timeline-time">{dt.strftime('%H:%M')}</div>
                    <div class="timeline-content" style="{active_style}">{e['summary']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True) # End Panel

    # --- BLOCK 2: RIGHT PANEL (Habits + Actions) ---
    with col_right:
        # Alles in EINEM Panel für saubere Kanten, oder zwei gestapelte?
        # User wollte "Blocks". Wir machen EINEN großen Block für Habits und Actions zusammen, 
        # damit die Höhe besser zur Timeline passt.
        
        st.markdown('<div class="dashboard-panel">', unsafe_allow_html=True)
        
        # 1. Habits
        st.markdown('<span class="sub-text">DAILY ROUTINES</span>', unsafe_allow_html=True)
        
        def load_habits(creds):
            defaults = {"📖 Reading (10m)": {}, "💧 Water (2L)": {}, "🏋️ Sport / Gym": {}}
            return storage.load_from_drive(creds, 'habits', defaults)
        
        habits = load_habits(creds)
        today_str = datetime.date.today().isoformat()
        updated_habits = False

        for h_name, h_data in habits.items():
            is_done = h_data.get(today_str, False)
            streak = 0
            check_date = datetime.date.today()
            if not is_done: check_date -= datetime.timedelta(days=1)
            while check_date.isoformat() in h_data and h_data[check_date.isoformat()]:
                streak += 1
                check_date -= datetime.timedelta(days=1)

            done_class = "done" if is_done else ""
            
            # Complex Layout inside Markdown via Streamlit Columns hack
            c_h1, c_h2 = st.columns([5, 1])
            with c_h1:
                st.markdown(f"""
                <div class="habit-row {done_class}">
                    <span class="habit-name">{h_name}</span>
                    <span class="habit-streak">🔥 {streak}</span>
                </div>
                """, unsafe_allow_html=True)
            with c_h2:
                # Align checkbox vertically roughly
                st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
                val = st.checkbox("Done", value=is_done, key=f"h_{h_name}", label_visibility="collapsed")
                if val != is_done:
                    habits[h_name][today_str] = val
                    updated_habits = True
        
        if updated_habits:
            storage.save_to_drive(creds, 'habits', habits)
            st.rerun()

        st.markdown("<div style='margin-top:30px; border-top:1px solid rgba(255,255,255,0.05); margin-bottom:20px;'></div>", unsafe_allow_html=True)

        # 2. Quick Actions
        st.markdown('<span class="sub-text">QUICK ACCESS</span>', unsafe_allow_html=True)
        
        qa1, qa2 = st.columns(2)
        with qa1:
            if st.button("➕ NEW TASK", use_container_width=True):
                st.switch_page("pages/2_📝_Tasks.py")
        with qa2:
            if st.button("📥 INBOX", use_container_width=True):
                st.switch_page("pages/7_📧_Inbox.py")
        
        st.markdown('</div>', unsafe_allow_html=True) # End Panel

# --- ROUTING ---
elif selected_page == "Calendar": st.switch_page("pages/1_📅_Calendar.py")
elif selected_page == "Tasks": st.switch_page("pages/2_📝_Tasks.py")
elif selected_page == "Focus": st.switch_page("pages/3_🔥_Focus.py")
elif selected_page == "Inbox": st.switch_page("pages/7_📧_Inbox.py")
elif selected_page == "Vault": st.switch_page("pages/6_🧠_Vault.py")
elif selected_page == "Chat": st.switch_page("pages/4_💬_Chat.py")
elif selected_page == "Settings": st.switch_page("pages/5_⚙️_Settings.py")
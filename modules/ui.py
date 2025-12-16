import streamlit as st
from streamlit_option_menu import option_menu
from modules import auth, storage

def load_css():
    """Lädt das globale CSS"""
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {display: none !important;}
            section[data-testid="stSidebar"] {
                background-color: #0f172a;
                border-right: 1px solid rgba(255,255,255,0.05);
            }
            .nav-link {
                border-radius: 8px !important;
                margin-bottom: 5px !important;
            }
            .nav-link:hover {
                background-color: rgba(255,255,255,0.05) !important;
            }
            .profile-box {
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.05);
                border-radius: 12px;
                padding: 15px;
                margin-bottom: 20px;
                text-align: center;
            }
        </style>
    """, unsafe_allow_html=True)

def card(title, value, desc, icon):
    return f"""
    <div style="background-color: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 20px; height: 100%;">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
            <span style="color: #94a3b8; font-size: 0.85rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">{title}</span>
            <span style="background: rgba(255,255,255,0.05); padding: 6px; border-radius: 8px; font-size: 1.1rem; line-height: 1;">{icon}</span>
        </div>
        <div style="font-size: 1.8rem; font-weight: 700; color: white; margin-bottom: 5px;">{value}</div>
        <div style="color: #64748b; font-size: 0.8rem;">{desc}</div>
    </div>
    """

def render_sidebar(active_page="Dashboard"):
    load_css()
    
    with st.sidebar:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            st.image("https://cdn-icons-png.flaticon.com/512/3652/3652191.png", width=60)
        
        st.markdown("""
            <h3 style='text-align: center; margin-bottom: 0; color: white;'>Kairos OS</h3>
            <p style='text-align: center; color: #64748b; font-size: 0.8rem; margin-top: -5px;'>Personal Intelligence</p>
        """, unsafe_allow_html=True)
        st.markdown("---")

        st.markdown("""
        <div class="profile-box">
            <div style="font-weight: bold; color: white;">Commander</div>
            <div style="font-size: 0.75rem; color: #10b981;">● Systems Online</div>
        </div>
        """, unsafe_allow_html=True)

        # HIER LIEGT DAS GEHEIMNIS: 
        # Die Dateinamen rechts müssen exakt so existieren wie im Ordner pages/
        page_map = {
            "Dashboard": "app.py",
            "Calendar": "pages/1_📅_Calendar.py",   # <--- Geändert zu Calendar (Englisch)
            "Tasks": "pages/2_📝_Tasks.py",         # <--- Geändert zu Tasks
            "Focus": "pages/3_🔥_Focus.py",         # <--- Geändert zu Focus (mit c)
            "Chat": "pages/4_💬_Chat.py",
            "Settings": "pages/5_⚙️_Settings.py",
            "Vault": "pages/6_🧠_Vault.py",
            "Inbox": "pages/7_📧_Inbox.py"
        }

        selected = option_menu(
            menu_title=None,
            options=list(page_map.keys()),
            icons=["speedometer2", "calendar-week", "list-check", "bullseye", "chat-dots", "gear", "archive", "inbox"],
            default_index=list(page_map.keys()).index(active_page),
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#94a3b8", "font-size": "16px"}, 
                "nav-link": {"font-size": "14px", "text-align": "left", "margin":"5px", "--hover-color": "#1e293b"},
                "nav-link-selected": {"background-color": "#2563eb", "color": "white", "font-weight": "600"},
            }
        )
        
        # WEITERLEITUNG
        if selected != active_page:
            st.switch_page(page_map[selected])

        st.markdown("---")
        
        try:
            creds = auth.get_creds()
            tasks = storage.load_from_drive(creds, 'tasks', [])
            open_count = len([t for t in tasks if t.get('status') != 'completed'])
        except:
            open_count = 0
            
        st.markdown(f"""
        <div style='display: flex; justify-content: space-between; align-items: center; color: #94a3b8; font-size: 0.8rem; padding: 0 10px;'>
            <span>Active Missions</span>
            <span style='background: #3b82f6; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.7rem;'>{open_count}</span>
        </div>
        """, unsafe_allow_html=True)
        
        return selected
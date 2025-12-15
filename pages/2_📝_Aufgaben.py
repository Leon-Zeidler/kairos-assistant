import streamlit as st
import datetime
from modules import storage, auth, ui

st.set_page_config(page_title="Mission Control", page_icon="🚀", layout="wide")
ui.load_css()

# Auth & Daten
service = auth.get_service()
creds = auth.get_creds()
tasks = storage.load_from_drive(creds, 'tasks', [])

# HEADER
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown("""
        <h1>Mission Control</h1>
        <p class='text-slate'>Manage and organize your objectives</p>
    """, unsafe_allow_html=True)

# STATS ROW (React Grid)
s1, s2, s3 = st.columns(3)
with s1:
    pending = len([t for t in tasks if t.get('status') == 'pending' or not t.get('status')])
    st.markdown(ui.kpi_card("Pending", pending, "Missions waiting", "Target", "blue"), unsafe_allow_html=True)
with s2:
    wip = len([t for t in tasks if t.get('status') == 'in_progress'])
    st.markdown(ui.kpi_card("In Progress", wip, "Currently active", "Clock", "amber"), unsafe_allow_html=True)
with s3:
    done = len([t for t in tasks if t.get('status') == 'completed'])
    st.markdown(ui.kpi_card("Completed", done, "Mission accomplished", "Wifi", "green"), unsafe_allow_html=True)

st.write("")

# FORMULAR (TaskForm Component)
with st.expander("➕ Add New Mission", expanded=True):
    with st.form("new_task"):
        c_in1, c_in2 = st.columns([3, 1])
        title = c_in1.text_input("Objective", placeholder="Enter mission objective...")
        
        c_sel1, c_sel2, c_sel3 = st.columns(3)
        cat = c_sel1.selectbox("Category", ["personal", "school", "sport", "coding"])
        dur = c_sel2.select_slider("Duration", options=["15", "30", "45", "60", "90", "120"], value="45")
        energy = c_sel3.select_slider("Energy", options=["low", "mid", "high"], value="mid")
        
        if st.form_submit_button("Initialize Mission"):
            new_task = {
                "name": title, "category": cat, "duration": int(dur), "energy": energy,
                "status": "pending", "created_at": datetime.datetime.now().isoformat()
            }
            tasks.append(new_task)
            storage.save_to_drive(creds, 'tasks', tasks)
            st.rerun()

# TASK TABS & CARDS
tab_all, tab_pending, tab_wip, tab_done = st.tabs(["All", "Pending", "In Progress", "Completed"])

def render_task_card(task, idx):
    # CSS für Card Colors
    colors = {
        "school": "border-red-500/40 text-red-400 bg-red-500/10",
        "sport": "border-orange-500/40 text-orange-400 bg-orange-500/10",
        "coding": "border-purple-500/40 text-purple-400 bg-purple-500/10",
        "personal": "border-[#00d4ff]/40 text-[#00d4ff] bg-[#00d4ff]/10"
    }
    cat_style = colors.get(task.get('category', 'personal'))
    energy_bolts = "⚡" * (1 if task.get('energy') == 'low' else 2 if task.get('energy') == 'mid' else 3)
    
    with st.container():
        c_info, c_act = st.columns([4, 1])
        with c_info:
            st.markdown(f"""
            <div class="glass-card" style="padding: 1rem; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="display: flex; gap: 0.5rem; margin-bottom: 0.5rem;">
                        <span class="{cat_style}" style="padding: 2px 8px; border-radius: 99px; font-size: 0.7rem; border: 1px solid;">{task.get('category').upper()}</span>
                        <span style="font-size: 0.7rem; color: #94a3b8;">{energy_bolts}</span>
                    </div>
                    <div style="font-weight: 600; font-size: 1.1rem;">{task['name']}</div>
                    <div style="font-size: 0.8rem; color: #64748b;">⏱️ {task['duration']} min</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with c_act:
            if st.button("▶️", key=f"foc_{idx}"):
                st.switch_page("pages/3_🔥_Focus.py") # Hier Parameterübergabe via SessionState wäre besser
            if st.button("🗑️", key=f"del_{idx}"):
                tasks.pop(idx)
                storage.save_to_drive(creds, 'tasks', tasks)
                st.rerun()

with tab_all:
    for i, t in enumerate(tasks):
        render_task_card(t, i)
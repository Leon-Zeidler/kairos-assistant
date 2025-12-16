import streamlit as st
from modules import ui
from modules import auth, mail_agent, storage, ui
import datetime

st.set_page_config(page_title="Inbox", page_icon="📧", layout="wide")
ui.render_sidebar("Inbox")
ui.load_css()

st.title("Command Center 📧")
st.caption("Incoming signals from Gmail.")

# Auth & Data
creds = auth.get_creds()
tasks = storage.load_from_drive(creds, 'tasks', [])

# --- STATE: Nur laden wenn nötig ---
if 'emails' not in st.session_state:
    with st.spinner("Scanning Inbox..."):
        st.session_state.emails = mail_agent.fetch_inbox_previews(creds, limit=8)

# --- TOOLBAR ---
c1, c2 = st.columns([4, 1])
with c1: st.info(f"📬 {len(st.session_state.emails)} unread emails.")
with c2: 
    if st.button("🔄 Refresh"):
        del st.session_state.emails
        st.rerun()

st.markdown("---")

# --- EMAIL LISTE ---
if not st.session_state.emails:
    st.success("Inbox Zero. Good job.")
else:
    for i, mail in enumerate(st.session_state.emails):
        with st.container(border=True):
            col_info, col_act = st.columns([5, 1])
            
            with col_info:
                st.markdown(f"**{mail['sender']}**")
                st.write(mail['subject'])
                st.caption(f"{mail['snippet']}...")
            
            with col_act:
                # DER BUTTON LÖST DIE ANALYSE AUS
                if st.button("⚡ Task", key=f"e_{i}", use_container_width=True):
                    with st.spinner("Analyzing..."):
                        # Hier holen wir den Body und fragen GPT
                        draft = mail_agent.analyze_email_task(creds, mail)
                        st.session_state.task_draft = draft
                        st.session_state.draft_source = mail['subject']
                        st.rerun()

# --- OVERLAY FÜR TASK ERSTELLUNG ---
if 'task_draft' in st.session_state:
    draft = st.session_state.task_draft
    
    @st.dialog("Create Task from Email")
    def show_draft_modal():
        st.caption(f"Source: {st.session_state.draft_source}")
        
        with st.form("mail_task"):
            name = st.text_input("Title", value=draft['title'])
            c1, c2, c3 = st.columns(3)
            cat = c1.selectbox("Category", ["School", "Personal", "Coding", "Sport"], 
                             index=["School", "Personal", "Coding", "Sport"].index(draft.get('category', 'Personal')))
            dur = c2.number_input("Duration", value=int(draft['duration']))
            nrg = c3.select_slider("Energy", ["low", "mid", "high"], value=draft['energy'])
            
            if st.form_submit_button("Create"):
                tasks.append({
                    "name": name, "category": cat, "duration": dur, "energy": nrg,
                    "status": "pending", "created_at": datetime.datetime.now().isoformat()
                })
                storage.save_to_drive(creds, 'tasks', tasks)
                del st.session_state.task_draft
                st.toast("Task created!")
                st.rerun()
                
    show_draft_modal()
import streamlit as st

def load_css():
    st.markdown("""
        <style>
        /* --- GLOBAL CLEAN STYLE --- */
        .stApp {
            /* Passt sich automatisch an Light/Dark Mode an */
        }
        
        /* --- MINIMALIST CARD --- */
        .simple-card {
            background-color: var(--secondary-background-color);
            border: 1px solid rgba(128, 128, 128, 0.2);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 1rem;
        }
        
        /* --- TYPOGRAPHY --- */
        h1, h2, h3 {
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            letter-spacing: -0.5px;
        }
        
        /* --- METRICS --- */
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            margin: 0;
        }
        .metric-label {
            font-size: 0.85rem;
            color: gray;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }
        
        /* --- REMOVE CLUTTER --- */
        .stDeployButton {display:none;}
        header {visibility: hidden;}
        
        /* --- BUTTONS --- */
        .stButton button {
            border-radius: 8px;
            font-weight: 500;
            border: 1px solid rgba(128, 128, 128, 0.2);
            transition: all 0.2s;
        }
        .stButton button:hover {
            border-color: #777;
            background-color: rgba(128, 128, 128, 0.1);
        }
        </style>
    """, unsafe_allow_html=True)

def card(title, value, subtext="", icon=""):
    # Sauberes HTML ohne Neon-Effekte
    return f"""
    <div class="simple-card">
        <div style="display: flex; justify-content: space-between; align-items: start;">
            <div>
                <div class="metric-label">{title}</div>
                <div class="metric-value">{value}</div>
                <div style="font-size: 0.8rem; color: gray; margin-top: 5px;">{subtext}</div>
            </div>
            <div style="font-size: 1.5rem; opacity: 0.7;">{icon}</div>
        </div>
    </div>
    """
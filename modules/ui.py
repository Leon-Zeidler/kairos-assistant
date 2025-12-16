import streamlit as st

def load_css():
    st.markdown("""
        <style>
        /* --- HINTERGRUND & BASIS --- */
        .stApp {
            background: linear-gradient(to bottom right, #0f172a, #1e1b4b);
            color: #f8fafc;
        }
        
        /* --- SIDEBAR CLEANUP --- */
        section[data-testid="stSidebar"] {
            background-color: #0f172a;
            border-right: 1px solid rgba(255,255,255,0.05);
        }
        
        /* --- MODERN CARDS (Glass Effect) --- */
        div.css-1r6slb0, .modern-card {
            background: rgba(30, 41, 59, 0.6);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            transition: transform 0.2s;
        }
        .modern-card:hover {
            border-color: rgba(255, 255, 255, 0.15);
            transform: translateY(-2px);
        }

        /* --- TYPOGRAPHY --- */
        h1, h2, h3 {
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            background: -webkit-linear-gradient(0deg, #fff, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        /* --- METRICS --- */
        .metric-label {
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: #94a3b8;
            margin-bottom: 8px;
            font-weight: 600;
        }
        .metric-value {
            font-size: 2.2rem;
            font-weight: 800;
            color: white;
            line-height: 1;
        }
        .metric-delta {
            font-size: 0.9rem;
            margin-top: 8px;
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
        }
        
        /* --- BUTTONS --- */
        .stButton button {
            background: linear-gradient(45deg, #3b82f6, #2563eb);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 0.5rem 1rem;
            font-weight: 600;
            box-shadow: 0 4px 14px 0 rgba(37, 99, 235, 0.39);
            transition: all 0.2s ease-in-out;
        }
        .stButton button:hover {
            transform: scale(1.02);
            box-shadow: 0 6px 20px rgba(37, 99, 235, 0.23);
        }
        /* Sekundäre Buttons (Grau) */
        div[data-testid="stHorizontalBlock"] button {
            background: rgba(255,255,255,0.05);
            box-shadow: none;
        }
        
        /* --- KALENDER FIX --- */
        .fc-theme-standard .fc-scrollgrid { border: none !important; }
        .fc-col-header-cell { background: rgba(255,255,255,0.02); color: #fff; padding: 10px 0; }
        .fc-timegrid-slot { border-bottom: 1px solid rgba(255,255,255,0.05) !important; }
        .fc-timegrid-axis { color: #94a3b8; }
        </style>
    """, unsafe_allow_html=True)

def card(title, value, delta="", icon=""):
    # Delta-Farbe berechnen
    delta_style = "background: rgba(16, 185, 129, 0.2); color: #34d399;" # Grün
    if "fällig" in delta or "Keine" in delta: 
        delta_style = "background: rgba(245, 158, 11, 0.2); color: #fbbf24;" # Gelb
    
    return f"""
    <div class="modern-card">
        <div style="display: flex; justify-content: space-between; align-items: start;">
            <div>
                <div class="metric-label">{title}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-delta" style="{delta_style}">{delta}</div>
            </div>
            <div style="font-size: 1.8rem; background: rgba(255,255,255,0.05); width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; border-radius: 12px;">
                {icon}
            </div>
        </div>
    </div>
    """
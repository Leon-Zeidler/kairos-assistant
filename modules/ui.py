import streamlit as st

def load_css():
    st.markdown("""
        <style>
        /* --- GLOBAL SETUP --- */
        .stApp {
            background-color: #0f172a; /* Slate 900 */
            color: white;
        }
        
        /* --- GLASS CARD CLASS --- */
        .glass-card {
            background-color: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 1rem;
            padding: 1.5rem;
            backdrop-filter: blur(12px);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        
        /* --- TYPOGRAPHY & COLORS --- */
        .text-glow-green { color: #00ff88; text-shadow: 0 0 20px rgba(0, 255, 136, 0.3); }
        .text-glow-blue { color: #00d4ff; text-shadow: 0 0 20px rgba(0, 212, 255, 0.3); }
        .text-glow-amber { color: #ffb800; text-shadow: 0 0 20px rgba(255, 184, 0, 0.3); }
        .text-slate { color: #94a3b8; }
        
        /* --- KPI CARDS --- */
        .kpi-metric { font-size: 1.875rem; font-weight: 700; color: white; margin: 0;}
        .kpi-title { font-size: 0.875rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; }
        .kpi-sub { font-size: 0.75rem; color: #64748b; }
        
        /* --- STREAMLIT OVERRIDES --- */
        /* Versteckt Standard-Elemente für Cleaner Look */
        header {visibility: hidden;}
        .stButton button {
            background: rgba(255, 255, 255, 0.05);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 0.75rem;
            transition: all 0.2s;
        }
        .stButton button:hover {
            border-color: #00ff88;
            color: #00ff88;
            transform: scale(1.02);
        }
        
        /* Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {
            background-color: rgba(30, 41, 59, 0.5);
            border-radius: 0.75rem;
            padding: 0.25rem;
        }
        .stTabs [data-baseweb="tab"] {
            color: #94a3b8;
        }
        .stTabs [aria-selected="true"] {
            background-color: rgba(0, 255, 136, 0.1) !important;
            color: #00ff88 !important;
            border-radius: 0.5rem;
        }
        </style>
    """, unsafe_allow_html=True)

# Helper für KPI Cards (HTML Generator)
def kpi_card(title, value, subtitle, icon="Target", color="green"):
    colors = {
        "green": "border-[#00ff88]/30 text-[#00ff88]",
        "blue": "border-[#00d4ff]/30 text-[#00d4ff]",
        "amber": "border-[#ffb800]/30 text-[#ffb800]",
        "red": "border-red-500/30 text-red-500"
    }
    
    # SVG Icons mapping (vereinfacht)
    icons = {
        "Target": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
        "Clock": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
        "Calendar": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/></svg>',
        "Wifi": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/></svg>'
    }

    border_color = f"rgba({0 if color=='red' else (255 if color=='amber' else 0)}, {255 if color in ['green','blue'] else (184 if color=='amber' else 0)}, {136 if color=='green' else (255 if color=='blue' else 0)}, 0.3)"
    text_color = "#00ff88" if color=="green" else "#00d4ff" if color=="blue" else "#ffb800" if color=="amber" else "#ef4444"
    bg_glow = f"rgba({0 if color=='red' else (255 if color=='amber' else 0)}, {255 if color in ['green','blue'] else (184 if color=='amber' else 0)}, {136 if color=='green' else (255 if color=='blue' else 0)}, 0.1)"

    html = f"""
    <div class="glass-card" style="border-color: {border_color}; position: relative; overflow: hidden;">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
            <div style="padding: 0.5rem; border-radius: 0.5rem; background-color: {bg_glow}; color: {text_color};">
                {icons.get(icon, "")}
            </div>
            <div style="width: 8px; height: 8px; border-radius: 50%; background-color: {text_color}; box-shadow: 0 0 10px {text_color};"></div>
        </div>
        <div class="kpi-title">{title}</div>
        <div class="kpi-metric">{value}</div>
        <div class="kpi-sub">{subtitle}</div>
    </div>
    """
    return html
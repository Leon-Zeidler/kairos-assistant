import streamlit as st

def load_css():
    # 1. HTML/JS für den "Beams" Hintergrund (Portierung des React-Effekts)
    beams_html = """
    <div id="beams-container">
        <canvas id="beams-canvas"></canvas>
    </div>
    <script>
        const canvas = document.getElementById('beams-canvas');
        const ctx = canvas.getContext('2d');
        
        let width, height;
        let beams = [];
        
        // Configuration (Matches your React props)
        const config = {
            beamWidth: 2,
            beamColor: 'rgba(171, 171, 171, 0.15)', // #ababab with low opacity
            speed: 0.5,
            count: 20
        };

        function resize() {
            width = window.innerWidth;
            height = window.innerHeight;
            canvas.width = width;
            canvas.height = height;
            initBeams();
        }

        function initBeams() {
            beams = [];
            for (let i = 0; i < config.count; i++) {
                beams.push({
                    x: Math.random() * width,
                    angle: (Math.random() - 0.5) * 0.5, // Slight angle
                    speed: (Math.random() + 0.5) * config.speed,
                    width: Math.random() * config.beamWidth + 1,
                    alpha: Math.random()
                });
            }
        }

        function draw() {
            // Clear with a slight trail effect
            ctx.fillStyle = 'rgba(15, 23, 42, 0.4)'; // Dark Slate Base
            ctx.fillRect(0, 0, width, height);
            
            ctx.fillStyle = config.beamColor;
            
            beams.forEach(beam => {
                ctx.save();
                ctx.translate(beam.x, 0);
                ctx.rotate(beam.angle);
                
                // Draw Beam (Long rectangle)
                ctx.globalAlpha = beam.alpha * 0.5;
                ctx.fillRect(0, -height/2, beam.width, height * 2);
                
                // Move
                beam.x += beam.speed;
                if (beam.x > width + 100) beam.x = -100;
                
                ctx.restore();
            });
            
            requestAnimationFrame(draw);
        }

        window.addEventListener('resize', resize);
        resize();
        draw();
    </script>
    <style>
        #beams-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: -1;
            background-color: #000000; /* Fallback Black */
            overflow: hidden;
            pointer-events: none;
        }
    </style>
    """
    
    # Inject Beams Background
    st.components.v1.html(beams_html, height=0, width=0) # Hack to inject without layout shift
    
    # 2. CSS für das UI (Monochrome Theme)
    st.markdown("""
        <style>
        /* --- GLOBAL & BEAMS FIX --- */
        .stApp {
            background: transparent !important; /* Wichtig damit Canvas sichtbar ist */
        }
        iframe[title="streamlit_components_v1.html"] {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: -1;
        }
        
        /* --- TYPOGRAPHY --- */
        h1, h2, h3 {
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            color: #f8fafc !important;
            text-shadow: 0 0 20px rgba(171, 171, 171, 0.3);
        }
        p, span, div {
            color: #cbd5e1;
        }
        
        /* --- SIDEBAR --- */
        section[data-testid="stSidebar"] {
            background-color: rgba(0, 0, 0, 0.6);
            border-right: 1px solid rgba(255,255,255,0.08);
            backdrop-filter: blur(20px);
        }
        
        /* --- MODERN SILVER CARDS --- */
        div.css-1r6slb0, .modern-card {
            background: rgba(20, 20, 20, 0.6); /* Sehr dunkel */
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(171, 171, 171, 0.15); /* Silver Border */
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
            transition: all 0.3s ease;
        }
        .modern-card:hover {
            border-color: rgba(171, 171, 171, 0.4);
            box-shadow: 0 0 20px rgba(171, 171, 171, 0.1);
            transform: translateY(-2px);
        }

        /* --- METRICS (Monochrome) --- */
        .metric-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: #94a3b8;
            margin-bottom: 8px;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: 300;
            color: #ffffff;
            font-family: monospace;
        }
        .metric-delta {
            font-size: 0.8rem;
            margin-top: 8px;
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            border: 1px solid rgba(255,255,255,0.1);
            background: rgba(255,255,255,0.05);
            color: #ababab;
        }
        
        /* --- BUTTONS (Silver) --- */
        .stButton button {
            background: rgba(255, 255, 255, 0.05);
            color: #fff;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            transition: all 0.2s;
        }
        .stButton button:hover {
            background: #ababab;
            color: #000;
            border-color: #ababab;
            box-shadow: 0 0 15px rgba(171, 171, 171, 0.5);
        }
        
        /* --- INPUTS --- */
        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
            background-color: rgba(0,0,0,0.5) !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)

def card(title, value, delta="", icon=""):
    # Monochrome Design
    return f"""
    <div class="modern-card">
        <div style="display: flex; justify-content: space-between; align-items: start;">
            <div>
                <div class="metric-label">{title}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-delta">{delta}</div>
            </div>
            <div style="font-size: 1.5rem; opacity: 0.5; color: #ababab;">
                {icon}
            </div>
        </div>
    </div>
    """
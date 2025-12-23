import streamlit as st
import json
import plotly.graph_objects as go
import pandas as pd

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="F1 Telemetry Terminal",
    layout="wide",
    page_icon="🏎️",
    initial_sidebar_state="expanded"
)

# --- 2. BACKEND CONNECTIONS ---

# A. Knowledge Base (JSON / Text Analysis)
try:
    # Importing analysis functions
    from f1_explain import explain_driver, compare_drivers, explain_similarity_multi

    explain_status = "ONLINE"
except ImportError:
    # Fallbacks
    def explain_driver(d, q):
        return f"Simulation Data for {d}: {q} \n[Backend Missing]"


    def compare_drivers(d1, d2):
        return f"Comparison {d1} vs {d2} \n[Backend Missing]"


    def explain_similarity_multi(t, m):
        return "Analysis Unavailable"


    explain_status = "OFFLINE"

# B. Vector Engine (Math)
try:
    # Importing vector logic
    from f1_chat import get_similar_drivers

    vector_status = "ONLINE"
except ImportError:
    def get_similar_drivers(t, d):
        return []


    vector_status = "OFFLINE"

# --- 3. LOAD JSON DATA ---
try:
    with open("driver_knowledge.json", "r") as f:
        DRIVER_DATA = json.load(f)
    DRIVER_NAMES = sorted(list({d["surname"] for d in DRIVER_DATA}))
except FileNotFoundError:
    DRIVER_DATA = []
    DRIVER_NAMES = ["Verstappen", "Hamilton", "Leclerc", "Norris", "Alonso"]

# --- 4. ASSETS (COLORS) ---
TEAM_CONFIG = {
    "Red Bull": {"color": "#061D42", "accent": "#3671C6"},
    "Mercedes": {"color": "#27F4D2", "accent": "#00A19B"},
    "Ferrari": {"color": "#FF1801", "accent": "#C30000"},
    "McLaren": {"color": "#FF8700", "accent": "#000000"},
    "Aston Martin": {"color": "#006F62", "accent": "#CEDC00"},
    "Alpine": {"color": "#0090FF", "accent": "#FD4BC7"},
    "Williams": {"color": "#005AFF", "accent": "#00A0DE"},
    "Haas": {"color": "#B6BABD", "accent": "#D0102E"},
    "Sauber": {"color": "#52E252", "accent": "#000000"},
    "RB": {"color": "#6692FF", "accent": "#FFFFFF"},
}


# --- 5. VISUAL ENGINE (CSS) ---
def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Orbitron:wght@500;700;900&display=swap');

        /* MAIN CONTAINER */
        .stApp {
            background-color: #050505;
            background-image: 
                linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
            background-size: 30px 30px;
            color: #E0E0E0;
            font-family: 'Inter', sans-serif;
        }

        /* TYPOGRAPHY */
        h1, h2, h3 { font-family: 'Orbitron', sans-serif; text-transform: uppercase; letter-spacing: 2px; }

        h1 {
            background: linear-gradient(90deg, #FF1801, #FF8700);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 900;
            font-size: 3rem !important;
        }

        /* DIGITAL BADGE */
        .driver-badge {
            background: rgba(20, 20, 25, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-left: 5px solid #444;
            border-radius: 8px;
            padding: 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
            transition: transform 0.2s;
            margin-bottom: 20px;
        }
        .driver-badge:hover { transform: scale(1.02); background: rgba(30, 30, 35, 1); }
        .driver-initials { font-family: 'Orbitron', sans-serif; font-size: 2.5rem; font-weight: 900; color: #fff; width: 80px; text-align: center; }
        .driver-info h4 { margin: 0; font-size: 1.2rem; color: #fff; text-transform: uppercase; }
        .driver-info p { margin: 0; font-size: 0.8rem; color: #888; text-transform: uppercase; }

        /* MATCH CARD (NEW) */
        .match-card {
            background: #111;
            border: 1px solid #3671C6;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            transition: transform 0.2s;
        }
        .match-card:hover { transform: translateY(-5px); box-shadow: 0 0 15px rgba(54, 113, 198, 0.3); }

        /* BUTTONS */
        div.stButton > button {
            background: linear-gradient(90deg, #FF1801 0%, #D00000 100%);
            color: white;
            border: none;
            border-radius: 4px;
            padding: 12px 24px;
            font-family: 'Orbitron', sans-serif;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: all 0.3s ease;
            width: 100%;
        }
        div.stButton > button:hover { box-shadow: 0 0 20px rgba(255, 24, 1, 0.6); transform: translateY(-2px); }

        /* TERMINAL BOX (Chat/Output) */
        .terminal-box {
            background-color: #0D1117;
            border: 1px solid #30363D;
            border-radius: 6px;
            padding: 20px;
            font-family: 'Inter', monospace;
            line-height: 1.6;
            border-left: 3px solid #FF1801;
            overflow-x: auto;
        }
        .terminal-header {
            font-family: 'Orbitron';
            font-size: 0.8rem;
            color: #58A6FF;
            margin-bottom: 10px;
            border-bottom: 1px solid #30363D;
            padding-bottom: 5px;
        }
    </style>
    """, unsafe_allow_html=True)


inject_custom_css()


# --- 6. HELPER FUNCTIONS ---

def get_team_color(team_name):
    if not team_name: return "#444444"
    for key, val in TEAM_CONFIG.items():
        if key.lower() in team_name.lower():
            return val["color"]
    return "#444444"


def render_digital_badge(driver_name, driver_data):
    team = driver_data.get("team_name", "Unknown Team")
    color = get_team_color(team)
    initials = driver_name[:3].upper()
    races = driver_data.get('races', 0)

    html = f"""
    <div class="driver-badge" style="border-left-color: {color}; box-shadow: -5px 0 15px -5px {color}80;">
        <div style="display:flex; align-items:center; gap:15px;">
            <div class="driver-initials" style="text-shadow: 0 0 10px {color};">{initials}</div>
            <div class="driver-info">
                <h4>{driver_name}</h4>
                <p style="color: {color};">{team}</p>
            </div>
        </div>
        <div>
            <span style="background:#1A1A1A; padding:5px 15px; border-radius:20px; font-size:0.8rem; border:1px solid #333; color:#ccc;">
                Races: {races}
            </span>
        </div>
    </div>
    """
    return html


def create_neon_radar(driver_a, driver_b, data_a, data_b):
    # Safety Helper to prevent crashes if data is missing
    def safe_get(d, k, default):
        val = d.get(k)
        return val if val is not None else default

    categories = ['Avg Pos', 'Consistency', 'Team Delta', 'Exp']

    def norm(val, max_v, invert=False):
        if invert: return max(0, (max_v - val) / max_v * 100)
        return min(100, (val / max_v) * 100)

    val_a = [
        norm(safe_get(data_a, 'avg_finish', 20), 22, True),
        norm(safe_get(data_a, 'finish_std', 10), 12, True),
        norm(safe_get(data_a, 'delta_vs_team', 5), 8, True),
        norm(safe_get(data_a, 'races', 0), 150, False)
    ]
    val_b = [
        norm(safe_get(data_b, 'avg_finish', 20), 22, True),
        norm(safe_get(data_b, 'finish_std', 10), 12, True),
        norm(safe_get(data_b, 'delta_vs_team', 5), 8, True),
        norm(safe_get(data_b, 'races', 0), 150, False)
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(r=val_a, theta=categories, fill='toself', name=driver_a, line=dict(color='#FF1801', width=3),
                        fillcolor='rgba(255, 24, 1, 0.2)'))
    fig.add_trace(
        go.Scatterpolar(r=val_b, theta=categories, fill='toself', name=driver_b, line=dict(color='#00F0FF', width=3),
                        fillcolor='rgba(0, 240, 255, 0.2)'))

    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, linecolor='#333'),
                                 bgcolor='rgba(0,0,0,0)'),
                      paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white', family="Inter"),
                      margin=dict(t=20, b=20, l=40, r=40), legend=dict(orientation="h", y=1.1))
    return fig


# --- 7. MAIN LAYOUT ---

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("<h1>F1 TELEMETRY <span style='color:#fff; font-weight:100; font-size:2rem;'>TERMINAL</span></h1>",
                unsafe_allow_html=True)
with col2:
    st.markdown(
        "<div style='text-align:right; font-family:Orbitron; color:#FF1801; font-size:2rem; padding-top:10px;'>LIVE_DATA // ON</div>",
        unsafe_allow_html=True)

st.markdown("---")

# Navigation Sidebar
with st.sidebar:
    st.markdown("### ⚙️ CONTROLS")
    mode = st.radio(
        "Select Module",
        ["Single Analysis", "Comparative Telemetry", "Doppelgänger Engine"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Status Indicators
    c_status_color = "#52E252" if vector_status == "ONLINE" else "#D0102E"
    e_status_color = "#52E252" if explain_status == "ONLINE" else "#D0102E"

    st.markdown(f"""
    <div style='background:#111; padding:15px; border-radius:5px; font-size:0.8rem; color:#666;'>
        <strong>SYSTEM STATUS:</strong><br>
        • LLM Engine: <span style='color:{e_status_color}'>{explain_status}</span><br>
        • Vector Core: <span style='color:{c_status_color}'>{vector_status}</span><br>
        • UI: <span style='color:#52E252'>OPTIMIZED</span>
    </div>
    """, unsafe_allow_html=True)

# --- MODE 1: SINGLE ANALYSIS ---
if mode == "Single Analysis":
    c_left, c_right = st.columns([1, 2])
    with c_left:
        st.markdown("### 01. TARGET DRIVER")
        driver = st.selectbox("Select Driver", DRIVER_NAMES, label_visibility="collapsed")
        d_stats = next((d for d in DRIVER_DATA if d["surname"] == driver), {})
        if d_stats: st.markdown(render_digital_badge(driver, d_stats), unsafe_allow_html=True)

    with c_right:
        st.markdown("### 02. INQUIRY PROTOCOL")
        question = st.selectbox("Select Parameter", [
            "Is this driver winning because of skill or car advantage?",
            "How consistent is this driver under race pressure?",
            "Would this driver still perform well in a weaker car?",
            "What kind of driver profile does this data suggest?"
        ], label_visibility="collapsed")
        st.write("")
        if st.button("INITIATE ANALYSIS"):
            with st.spinner("PROCESSING TELEMETRY STREAM..."):
                result = explain_driver(driver, question)
                st.markdown(
                    f"""<div class="terminal-box"><div class="terminal-header">>> OUTPUT STREAM // {driver.upper()}</div>{result}</div>""",
                    unsafe_allow_html=True)

# --- MODE 2: COMPARATIVE TELEMETRY ---
elif mode == "Comparative Telemetry":
    st.markdown("### ⚔️ DRIVER MATCHUP")
    col_a, col_mid, col_b = st.columns([1, 0.1, 1])
    with col_a:
        d_a = st.selectbox("Driver A", DRIVER_NAMES, index=0)
        stats_a = next((d for d in DRIVER_DATA if d["surname"] == d_a), {})
        if stats_a: st.markdown(render_digital_badge(d_a, stats_a), unsafe_allow_html=True)
    with col_mid:
        st.markdown("<div style='text-align:center; padding-top:50px; color:#555;'>VS</div>", unsafe_allow_html=True)
    with col_b:
        d_b = st.selectbox("Driver B", DRIVER_NAMES, index=1)
        stats_b = next((d for d in DRIVER_DATA if d["surname"] == d_b), {})
        if stats_b: st.markdown(render_digital_badge(d_b, stats_b), unsafe_allow_html=True)

    if stats_a and stats_b:
        st.markdown("### 📊 TELEMETRY VISUALIZATION")
        chart_col, text_col = st.columns([2, 1])
        with chart_col:
            st.plotly_chart(create_neon_radar(d_a, d_b, stats_a, stats_b), use_container_width=True,
                            config={'displayModeBar': False})
        with text_col:
            st.markdown(
                """<div style='margin-top:20px; font-size:0.9rem; color:#888;'><strong>LEGEND:</strong><br><span style='color:#FF1801'>■</span> DRIVER A<br><span style='color:#00F0FF'>■</span> DRIVER B</div>""",
                unsafe_allow_html=True)
            st.write("")
            if st.button("RUN SIMULATION"):
                with st.spinner("CALCULATING DELTAS..."):
                    res = compare_drivers(d_a, d_b)
                    st.markdown(
                        f"""<div class="terminal-box"><div class="terminal-header">>> SIMULATION RESULT</div>{res}</div>""",
                        unsafe_allow_html=True)

# --- MODE 3: DOPPELGÄNGER ENGINE (NEW) ---
elif mode == "Doppelgänger Engine":
    st.markdown("### 🧬 HISTORICAL MATCHING ENGINE")
    st.markdown("""
    <div style='color:#888; font-size:0.9rem; margin-bottom:20px;'>
        // ALGORITHM: Cosine Similarity Vector Scan<br>
        // INPUTS: Average Finish, Consistency, Team Delta, Experience<br>
        // GOAL: Identify statistical performance twins across eras.
    </div>
    """, unsafe_allow_html=True)

    col_search, col_result = st.columns([1, 2])

    with col_search:
        target_twin = st.selectbox("Find match for:", DRIVER_NAMES, key="t2_driver")
        st.write("")
        if st.button("SCAN DATABASE"):
            # Call find_similar_driver from f1_chat.py
            matches = get_similar_drivers(target_twin, DRIVER_DATA)

            if matches:
                st.session_state['matches'] = matches
                st.session_state['vector_target'] = target_twin

                # Call explain_similarity from f1_explain.py
                with st.spinner("CORRELATING STYLES..."):
                    st.session_state['vector_exp'] = explain_similarity_multi(target_twin, matches)
            else:
                st.error("No statistical match found.")

    with col_result:
        if 'matches' in st.session_state:
            matches = st.session_state['matches']

            # Display Top 3 Cards
            cols = st.columns(3)
            for i, col in enumerate(cols):
                if i < len(matches):
                    m = matches[i]
                    pct = int(m['similarity_score'] * 100)
                    with col:
                        st.markdown(f"""
                        <div class='match-card'>
                            <div style='font-size:0.8rem; color:#888;'>MATCH #{i + 1}</div>
                            <h2 style='color:white; margin:5px 0;'>{m['surname']}</h2>
                            <div style='color:#3b82f6; font-family:Orbitron; font-size:1.5rem;'>{pct}%</div>
                            <div style='font-size:0.7rem; color:#666;'>SIMILARITY</div>
                        </div>""", unsafe_allow_html=True)

            # AI Analysis Box
            st.markdown(f"""
            <div class="terminal-box" style="margin-top:20px; border-left-color: #3b82f6;">
                <div class="terminal-header">>> AI CORRELATION ANALYSIS</div>
                <p style="color:#ccc;">{st.session_state.get('vector_exp', 'Processing...')}</p>
            </div>
            """, unsafe_allow_html=True)

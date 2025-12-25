import streamlit as st
import json
import plotly.graph_objects as go
import pandas as pd
import base64

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="F1 Telemetry Terminal",
    layout="wide",
    page_icon="🏎️",
    initial_sidebar_state="expanded"
)

# --- 2. BACKEND CONNECTIONS ---
try:
    from f1_explain import explain_driver, compare_drivers, explain_similarity_multi, narrate_race_story
    from f1_logic import get_similar_drivers, get_years, get_races_for_year, get_drivers_in_race, get_race_story_stats

    backend_status = "ONLINE"
except ImportError:
    st.error("CRITICAL: Backend modules missing.")
    st.stop()

# --- 3. LOAD DATA ---
try:
    with open("driver_knowledge.json", "r") as f:
        DRIVER_DATA = json.load(f)
    DRIVER_NAMES = sorted(list({d["surname"] for d in DRIVER_DATA}))
except:
    DRIVER_NAMES = ["Verstappen", "Hamilton", "Alonso"]

def get_img_as_base64(file_path):
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return None


import base64


# --- HELPER TO LOAD IMAGE ---
def get_img_as_base64(file_path):
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return None


# --- 5. VISUAL ENGINE (CSS) ---
# --- 5. VISUAL ENGINE (CSS) ---
def inject_custom_css():
    # Load images (keep your existing logic)
    main_bg_b64 = get_img_as_base64("background.png")
    sidebar_bg_b64 = get_img_as_base64("sidebar_bg.png")

    # Define Sidebar Background
    if sidebar_bg_b64:
        sidebar_style = f"""
            background-image: linear-gradient(to bottom, rgba(0,0,0,0.95), rgba(10,10,10,0.95)), 
                              url("data:image/jpeg;base64,{sidebar_bg_b64}");
            background-size: cover;
        """
    else:
        sidebar_style = "background: #09090b;"

    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;500;700&display=swap');

        /* --- GLOBAL & MAIN BACKGROUND --- */
        .stApp {{
            background-color: #0e0e0e;
            color: #E0E0E0;
            font-family: 'Rajdhani', sans-serif;
        }}

        /* --- SIDEBAR CONTAINER --- */
        section[data-testid="stSidebar"] {{
            {sidebar_style}
            border-right: 1px solid #333;
        }}

        /* Remove default top padding in sidebar */
        section[data-testid="stSidebar"] .block-container {{
            padding-top: 2rem;
        }}

        /* --- STYLED RADIO BUTTONS (THE MENU) --- */
        /* 1. Hide the default circle radio button */
        div[role="radiogroup"] > label > div:first-child {{
            display: none !important;
        }}

        /* 2. Style the label container to look like a button */
        div[role="radiogroup"] label {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-left: 3px solid #333;
            padding: 12px 15px !important;
            margin-bottom: 8px !important;
            border-radius: 0px 10px 10px 0px; /* Chamfered edge look */
            transition: all 0.3s ease;
            font-family: 'Orbitron', sans-serif;
            font-size: 0.9rem;
            cursor: pointer;
            display: flex;
        }}

        /* 3. HOVER STATE */
        div[role="radiogroup"] label:hover {{
            background: rgba(255, 255, 255, 0.1);
            border-left: 3px solid #00F0FF; /* Cyan glow on hover */
            transform: translateX(5px);
        }}

        /* 4. ACTIVE/SELECTED STATE */
        div[role="radiogroup"] label[data-checked="true"] {{
            background: linear-gradient(90deg, rgba(255, 24, 1, 0.8) 0%, rgba(0,0,0,0) 100%);
            border: 1px solid #FF1801;
            border-left: 5px solid #FFFFFF; /* White heavy bar */
            color: white !important;
            box-shadow: 0 0 15px rgba(255, 24, 1, 0.3);
        }}

        /* 5. TEXT INSIDE MENU */
        div[role="radiogroup"] label p {{
            font-weight: 600;
            letter-spacing: 1px;
            margin: 0;
            color: #ccc;
        }}
        div[role="radiogroup"] label[data-checked="true"] p {{
            color: #fff;
        }}

        /* --- HEADERS --- */
        h1, h2, h3 {{ font-family: 'Orbitron', sans-serif; text-transform: uppercase; }}

        /* --- GLASSMOPHISM CARDS --- */
        .glass-card {{
            background: rgba(20, 20, 25, 0.7);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 15px;
        }}

    </style>
    """, unsafe_allow_html=True)

inject_custom_css()


# --- 5. UI COMPONENT FUNCTIONS ---

def render_driver_badge(name, data):
    """Renders a high-fidelity driver card."""
    team = data.get("team_name", "UNKNOWN TEAM")
    races = data.get("races", 0)

    # Simple color mapping for badges
    team_colors = {"Red Bull": "#061D42", "Ferrari": "#FF1801", "Mercedes": "#00A19B", "McLaren": "#FF8700"}
    accent = "#444"
    for t, c in team_colors.items():
        if t in team: accent = c

    st.markdown(f"""
    <div class="glass-card" style="border-left: 5px solid {accent};">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="font-size:0.8rem; color:#888; letter-spacing:2px; font-family:'Orbitron';">DRIVER PROFILE</div>
                <div style="font-size:2.5rem; font-weight:900; font-family:'Orbitron'; line-height:1;">{name.upper()}</div>
                <div style="font-size:1.2rem; color:{accent}; font-weight:bold;">{team.upper()}</div>
            </div>
            <div style="text-align:right;">
            </div>
        </div>
        <div style="margin-top:15px; display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
            <div style="background:rgba(255,255,255,0.05); padding:10px; border-radius:5px; text-align:center;">
                <div style="font-size:0.7rem; color:#aaa;">RACES</div>
                <div style="font-size:1.2rem; font-weight:bold;">{races}</div>
            </div>
            <div style="background:rgba(255,255,255,0.05); padding:10px; border-radius:5px; text-align:center;">
                <div style="font-size:0.7rem; color:#aaa;">AVG FINISH</div>
                <div style="font-size:1.2rem; font-weight:bold;">{data.get('avg_finish', 0):.1f}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_radar_chart(driver_a, driver_b, data_a, data_b):
    """Renders the Neon Radar Chart."""

    def safe_get(d, k, default): return d.get(k) if d.get(k) is not None else default

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
    fig.add_trace(go.Scatterpolar(r=val_a, theta=['Pace', 'Consistency', 'Skill', 'Exp'], fill='toself', name=driver_a,
                                  line=dict(color='#FF1801', width=3), fillcolor='rgba(255, 24, 1, 0.2)'))
    fig.add_trace(go.Scatterpolar(r=val_b, theta=['Pace', 'Consistency', 'Skill', 'Exp'], fill='toself', name=driver_b,
                                  line=dict(color='#00F0FF', width=3), fillcolor='rgba(0, 240, 255, 0.2)'))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, linecolor='#444'),
                   bgcolor='rgba(0,0,0,0)', gridshape='linear'),
        paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white', family="Rajdhani"),
        margin=dict(t=20, b=20, l=40, r=40), legend=dict(orientation="h", y=1.1)
    )
    return fig


# --- 6. HEADER ---
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown("<h1 class='neon-text'>F1 TELEMETRY TERMINAL</h1>", unsafe_allow_html=True)
    st.markdown(
        "<div style='letter-spacing: 3px; color: #888; font-size: 0.9rem;'>AI-POWERED PERFORMANCE ANALYTICS V1.0</div>",
        unsafe_allow_html=True)
with c2:
    # A blinking live indicator
    st.markdown("""
    <div style='text-align:right; margin-top:20px;'>
        <span style='background:#FF1801; color:white; padding:5px 10px; border-radius:4px; font-weight:bold; font-family:"Orbitron"; box-shadow: 0 0 10px #FF1801;'>LIVE</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 7. NAVIGATION ---
# --- 7. NAVIGATION & SIDEBAR ---
with st.sidebar:
    # -- 1. HEADER / LOGO AREA --
    st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <div style="font-family:'Orbitron'; font-weight:900; font-size:2.5rem; color:#FF1801; line-height:1;">F1</div>
            <div style="font-family:'Rajdhani'; letter-spacing:4px; font-size:0.8rem; color:#aaa;">TELEMETRY HUB</div>
        </div>
    """, unsafe_allow_html=True)

    # -- 2. USER PROFILE (GAME STYLE) --
    st.markdown("""
        <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 6px; display: flex; align-items: center; margin-bottom: 25px; border: 1px solid #333;">
            <div style="width: 35px; height: 35px; background: #333; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 10px; color: #fff;">
                👤
            </div>
            <div>
                <div style="font-size: 0.7rem; color: #888; font-family: 'Orbitron';">CURRENT USER</div>
                <div style="font-size: 0.9rem; color: #fff; font-weight: bold;">RACE_ENGINEER_01</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # -- 3. THE MENU (Radio buttons styled as buttons) --
    st.markdown("<div style='font-size:0.7rem; color:#666; margin-bottom:5px; padding-left:5px;'>OPERATIONS</div>",
                unsafe_allow_html=True)

    # We add icons to the keys so they look like menu items
    mode = st.radio(
        "Navigation",
        [
            "⚡ SINGLE ANALYSIS",
            "⚔️ COMPARATIVE TELEMETRY",
            "🧬 DOPPELGÄNGER ENGINE",
            "📖 RACE REWIND"
        ],
        label_visibility="collapsed"
    )

    # -- 4. SYSTEM FOOTER --
    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.7rem; color:#666; margin-bottom:5px; padding-left:5px;'>SYSTEM DIAGNOSTICS</div>",
        unsafe_allow_html=True)

    # Status Indicators
    st.markdown(f"""
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 5px;">
        <div style="background: #111; padding: 8px; border-radius: 4px; text-align: center; border: 1px solid #222;">
            <div style="font-size: 0.6rem; color: #666;">LATENCY</div>
            <div style="font-size: 0.9rem; color: #00F0FF; font-family: 'Orbitron';">24ms</div>
        </div>
        <div style="background: #111; padding: 8px; border-radius: 4px; text-align: center; border: 1px solid #222;">
            <div style="font-size: 0.6rem; color: #666;">BACKEND</div>
            <div style="font-size: 0.9rem; color: #52E252; font-family: 'Orbitron';">{backend_status}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Decorative bottom lines
    st.markdown("""
        <div style="margin-top: 20px; display: flex; gap: 5px;">
            <div style="height: 4px; width: 30%; background: #FF1801;"></div>
            <div style="height: 4px; width: 10%; background: #ccc;"></div>
            <div style="height: 4px; width: 60%; background: #333;"></div>
        </div>
    """, unsafe_allow_html=True)

# Clean up the mode string because we added icons
if "SINGLE ANALYSIS" in mode:
    mode = "Single Analysis"
elif "COMPARATIVE" in mode:
    mode = "Comparative Telemetry"
elif "DOPPELGÄNGER" in mode:
    mode = "Doppelgänger Engine"
elif "RACE REWIND" in mode:
    mode = "Race Rewind"

# =========================================================
# MODULE 1: SINGLE ANALYSIS
# =========================================================
if mode == "Single Analysis":
    c_left, c_right = st.columns([1, 2])
    with c_left:
        st.markdown("##### SELECT DRIVER")
        driver = st.selectbox("Driver", DRIVER_NAMES, label_visibility="collapsed")
        d_stats = next((d for d in DRIVER_DATA if d["surname"] == driver), {})
        if d_stats: render_driver_badge(driver, d_stats)

    with c_right:
        st.markdown("##### INQUIRY PROTOCOL")
        question = st.selectbox("Select Query", [
            "Is this driver winning because of skill or car advantage?",
            "How consistent is this driver under race pressure?",
            "Would this driver still perform well in a weaker car?",
            "What kind of driver profile does this data suggest?"
        ], label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("INITIALIZE AI ANALYSIS"):
            with st.spinner("ESTABLISHING DATA LINK..."):
                result = explain_driver(driver, question)
                st.markdown(f"""
                <div class="glass-card">
                    <div style="font-family:'Orbitron'; color:#00F0FF; margin-bottom:10px; border-bottom:1px solid #333; padding-bottom:5px;">
                        >> AI STRATEGY REPORT
                    </div>
                    <div style="line-height:1.6; color:#ddd;">{result}</div>
                </div>
                """, unsafe_allow_html=True)

# =========================================================
# MODULE 2: COMPARATIVE TELEMETRY
# =========================================================
elif mode == "Comparative Telemetry":
    st.markdown("##### ⚔️ HEAD-TO-HEAD TELEMETRY")

    col_a, col_mid, col_b = st.columns([1, 0.1, 1])
    with col_a:
        d_a = st.selectbox("Driver A", DRIVER_NAMES, index=0)
        s_a = next((d for d in DRIVER_DATA if d["surname"] == d_a), {})
        if s_a: render_driver_badge(d_a, s_a)

    with col_mid:
        st.markdown(
            "<div style='text-align:center; padding-top:100px; font-size:2rem; font-family:Orbitron; color:#FF1801;'>VS</div>",
            unsafe_allow_html=True)

    with col_b:
        d_b = st.selectbox("Driver B", DRIVER_NAMES, index=1)
        s_b = next((d for d in DRIVER_DATA if d["surname"] == d_b), {})
        if s_b: render_driver_badge(d_b, s_b)

    if s_a and s_b:
        st.markdown("##### 📊 DATA VISUALIZATION")
        c_chart, c_txt = st.columns([2, 1])
        with c_chart:
            st.plotly_chart(render_radar_chart(d_a, d_b, s_a, s_b), use_container_width=True,
                            config={'displayModeBar': False})
        with c_txt:
            st.markdown("<br><br>", unsafe_allow_html=True)
            if st.button("RUN SIMULATION"):
                with st.spinner("CALCULATING DELTAS..."):
                    res = compare_drivers(d_a, d_b)
                    st.markdown(f"""
                    <div class="terminal-output">
                        {res}
                    </div>
                    """, unsafe_allow_html=True)

# =========================================================
# MODULE 3: DOPPELGÄNGER ENGINE
# =========================================================
elif mode == "Doppelgänger Engine":
    st.markdown("##### 🧬 STATISTICAL TWIN IDENTIFICATION")

    c_search, c_res = st.columns([1, 2])
    with c_search:
        st.markdown("Select a driver to find their historical statistical twin.")
        target_twin = st.selectbox("Target Driver", DRIVER_NAMES)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("SCAN DATABASE"):
            matches = get_similar_drivers(target_twin, DRIVER_DATA)
            if matches:
                st.session_state['matches'] = matches
                with st.spinner("ANALYZING CORRELATIONS..."):
                    st.session_state['vec_exp'] = explain_similarity_multi(target_twin, matches)
            else:
                st.error("No matches found.")

    with c_res:
        if 'matches' in st.session_state:
            matches = st.session_state['matches']
            cols = st.columns(3)
            for i, col in enumerate(cols):
                if i < len(matches):
                    m = matches[i]
                    pct = int(m['similarity_score'] * 100)
                    with col:
                        st.markdown(f"""
                        <div class="match-card">
                            <div style="font-size:0.7rem; color:#888;">MATCH #{i + 1}</div>
                            <div style="font-size:1.2rem; font-weight:bold; color:white; margin:5px 0;">{m['surname']}</div>
                            <div style="font-size:2rem; font-family:'Orbitron'; color:#00F0FF;">{pct}%</div>
                            <div style="font-size:0.6rem; color:#555;">CONFIDENCE</div>
                        </div>
                        """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="glass-card" style="margin-top:20px;">
                <div style="color:#00F0FF; font-family:'Orbitron'; font-size:0.9rem; margin-bottom:10px;">>> AI CORRELATION ANALYSIS</div>
                <div style="color:#ccc;">{st.session_state.get('vec_exp', '...')}</div>
            </div>
            """, unsafe_allow_html=True)

# =========================================================
# MODULE 4: RACE REWIND
# =========================================================
elif mode == "Race Rewind":
    st.markdown("##### 📖 HISTORICAL RECONSTRUCTION")

    years = get_years()
    if not years:
        st.warning("Database unavailable.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            sel_year = st.selectbox("1. SEASON", years)
        with c2:
            races = get_races_for_year(sel_year)
            sel_race = st.selectbox("2. GRAND PRIX", races['name']) if not races.empty else None
            race_id = races[races['name'] == sel_race].iloc[0]['raceId'] if sel_race else None
        with c3:
            drivers = get_drivers_in_race(race_id) if race_id else []
            sel_driver = st.selectbox("3. DRIVER", drivers) if drivers else None

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("GENERATE NARRATIVE", disabled=not sel_driver):
            with st.spinner("RECONSTRUCTING RACE EVENTS..."):
                stats = get_race_story_stats(race_id, sel_driver)
                if stats:
                    story = narrate_race_story(stats)
                    st.markdown(f"""
                    <div class="glass-card" style="border-left: 4px solid #FF1801;">
                        <div style="display:flex; justify-content:space-between; border-bottom:1px solid #444; padding-bottom:10px; margin-bottom:10px;">
                            <span style="font-family:'Orbitron'; color:#aaa;">GRID: P{stats['grid']}</span>
                            <span style="font-family:'Orbitron'; color:#fff;">FINISH: P{stats['finish']}</span>
                            <span style="font-family:'Orbitron'; color:#FF1801;">{stats['status']}</span>
                        </div>
                        <div style="line-height:1.8; font-size:1.1rem; color:#e0e0e0;">
                            {story}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

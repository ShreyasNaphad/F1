import streamlit as st
import json
import plotly.graph_objects as go
import pandas as pd
import base64
import os

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="F1 INTELLIGENCE TERMINAL",
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


# --- 3. LOAD DATA (CSV - AUTHORITATIVE SOURCE FOR NAMES & CHARTS) ---
@st.cache_data
def load_race_data():
    """
    Loads raw CSV data and creates a 'full_name' column to distinguish drivers like Schumacher.
    """
    base_dir = os.getcwd()
    data_dir = os.path.join(base_dir, "data")

    # Check if main file exists
    if not os.path.exists(os.path.join(data_dir, "results.csv")):
        return None

    try:
        # Load CSVs
        df_res = pd.read_csv(os.path.join(data_dir, "results.csv"))
        df_drv = pd.read_csv(os.path.join(data_dir, "drivers.csv"))
        df_race = pd.read_csv(os.path.join(data_dir, "races.csv"))

        # Merge to get Names and Dates
        # We grab 'forename' here to fix the Schumacher issue
        merged = pd.merge(df_res, df_drv[['driverId', 'forename', 'surname']], on='driverId', how='left')
        merged = pd.merge(merged, df_race[['raceId', 'year', 'date', 'name']], on='raceId', how='left')

        # Create Unique Identifier: Full Name
        merged['full_name'] = merged['forename'] + " " + merged['surname']

        # Convert date
        merged['date'] = pd.to_datetime(merged['date'])

        return merged.sort_values(by='date')
    except Exception as e:
        # Silently fail or log if needed, return None so app continues
        return None


# Load CSV Data first (it's our source of truth for names)
RACE_DATA_CACHE = load_race_data()

# --- 4. LOAD JSON (STATISTICAL KNOWLEDGE BASE) ---
try:
    with open("driver_knowledge.json", "r") as f:
        DRIVER_DATA = json.load(f)
except:
    DRIVER_DATA = []

# --- 5. BUILD DRIVER LIST ---
# We use the CSV 'full_name' list if available because it distinguishes Michael vs Mick
# --- 5. BUILD DRIVER LIST (SMART FILTER) ---
# Goal: Use Full Names from CSV (to fix Schumacher), but ONLY if they exist in JSON.

if RACE_DATA_CACHE is not None and DRIVER_DATA:
    # 1. Get a set of all valid surnames from your JSON file
    valid_json_surnames = {d["surname"].lower() for d in DRIVER_DATA}

    # 2. Get all Full Names from the CSV
    all_csv_names = sorted(RACE_DATA_CACHE['full_name'].unique())

    # 3. Filter: Only keep a Full Name if its surname exists in your JSON
    # Example: "Michael Schumacher" -> surname "Schumacher" -> Found in JSON? -> Keep.
    # Example: "Random Driver" -> surname "Driver" -> Not in JSON? -> Drop.
    DRIVER_LIST = []
    for full_name in all_csv_names:
        surname_part = full_name.split()[-1].lower()
        if surname_part in valid_json_surnames:
            DRIVER_LIST.append(full_name)

else:
    # Fallback: If CSV fails, just use the surnames from JSON
    DRIVER_LIST = sorted(list({d["surname"] for d in DRIVER_DATA}))


def get_json_stats(full_name):
    """Finds the JSON profile matching the Full Name's surname."""
    if not full_name: return {}
    surname = full_name.split()[-1].lower()

    # Find the matching dictionary in the JSON list
    for d in DRIVER_DATA:
        if d["surname"].lower() == surname:
            return d
    return {}

def get_base64_of_bin_file(file_path):
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return None


def generate_persona_response(driver_name, user_query, stats, json_traits):
    """
    Generates an in-character response grounded in real stats + traits.
    """

    stats_context = (
        f"Total races: {stats.get('races', 0)}, "
        f"Wins: {stats.get('wins', 0)}, "
        f"Average finish: {stats.get('avg_finish', 0):.1f}, "
        f"Teams driven for: {', '.join(stats.get('teams', []))}"
    )

    traits_context = (
        f"Skill level: {json_traits.get('skill_level', 'unknown')}, "
        f"Consistency: {json_traits.get('consistency_level', 'unknown')}, "
        f"Era reputation: {json_traits.get('data_reliability', 'unknown')}"
    )

    system_prompt = f"""
SYSTEM:
You are {driver_name}, a Formula 1 driver.
- Speak ONLY in first person.
- Stay in character.
- Be reflective, honest, and concise (max 4 sentences).
- Never mention being an AI.

FACTUAL CONTEXT:
{stats_context}
{traits_context}

USER QUESTION:
{user_query}
"""

    try:
        # Using your existing backend pipe
        response = explain_driver(driver_name.split()[-1], system_prompt)
        return response
    except Exception as e:
        return "Radio interference… I can't answer that right now."


def get_driver_image_path(full_name):
    """
    Maps a driver name to a local image file.
    You need to place images in an 'assets/drivers/' folder.
    """
    filename = full_name.lower().replace(" ", "_") + ".png"
    path = os.path.join("assets", filename)
    if os.path.exists(path):
        return path
    return None  # Returns None if image not found (we will show a placeholder)


def inject_custom_css():
    # --- VISUAL ENGINE (CSS) ---
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;500;700&display=swap');

        /* --- 1. BACKGROUND FIX (GRADIENT THEME) --- */
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #0a0a0e 0%, #061D42 60%, #004e92 100%) !important;
            background-size: cover;
            background-attachment: fixed;
        }

        /* Make the default background transparent so the gradient shows through */
        .stApp {
            background: transparent !important;
        }

        /* --- 2. HIDE STREAMLIT HEADER --- */
        [data-testid="stHeader"] {
            background-color: rgba(0,0,0,0) !important;
        }

        [data-testid="stDecoration"] {
            display: none;
        }

        /* --- 3. SIDEBAR --- */
        section[data-testid="stSidebar"] {
            background: rgba(0, 0, 0, 0.6) !important; /* Semi-transparent black */
            backdrop-filter: blur(15px); /* Strong glass blur */
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }

        /* --- 4. RADIO BUTTONS (MENU) --- */
        div[role="radiogroup"] > label > div:first-child {
            display: none !important;
        }

        div[role="radiogroup"] label {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-left: 3px solid #333;
            padding: 12px 15px !important;
            margin-bottom: 8px !important;
            border-radius: 0px 10px 10px 0px; 
            transition: all 0.3s ease;
            font-family: 'Orbitron', sans-serif;
            font-size: 0.9rem;
            cursor: pointer;
            display: flex;
            color: #ccc;
        }

        div[role="radiogroup"] label:hover {
            background: rgba(255, 255, 255, 0.15);
            border-left: 3px solid #00F0FF; 
            transform: translateX(5px);
            color: white;
        }

        div[role="radiogroup"] label[data-checked="true"] {
            background: linear-gradient(90deg, rgba(255, 24, 1, 0.6) 0%, rgba(0,0,0,0) 100%);
            border: 1px solid #FF1801;
            border-left: 5px solid #FFFFFF; 
            color: white !important;
            box-shadow: 0 0 20px rgba(255, 24, 1, 0.4);
        }

        div[role="radiogroup"] label p {
            font-weight: 600;
            letter-spacing: 1px;
            margin: 0;
            color: inherit;
        }

        /* --- 5. TEXT & CARDS --- */
        h1, h2, h3 { 
            font-family: 'Orbitron', sans-serif; 
            text-transform: uppercase; 
            color: white;
            text-shadow: 0 0 10px rgba(0, 240, 255, 0.5); /* Neon Glow on headers */
        }

        .glass-card {
            background: rgba(20, 20, 25, 0.6);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 15px;
        }

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


def render_momentum_chart(full_name):
    """
    Renders the Momentum Area Chart using CSV data.
    Uses FULL NAME to filter, solving the Schumacher Collision.
    """
    # Check if data loaded correctly
    if RACE_DATA_CACHE is None:
        st.warning("⚠️ CSV Data not found in 'data/' folder. Cannot show momentum.")
        return

    # STRICT FILTERING by Full Name
    # This prevents Michael's races appearing for Mick
    driver_df = RACE_DATA_CACHE[RACE_DATA_CACHE['full_name'] == full_name].copy()

    # Check if we have data
    if driver_df.empty:
        st.info(f"No recent race history found for {full_name}.")
        return

    # Get last 10 races (most recent)
    driver_df = driver_df.sort_values(by='date', ascending=False).head(10)

    # Sort back to ascending for the timeline plot
    driver_df = driver_df.sort_values(by='date', ascending=True)

    # Create Plotly Chart
    fig = go.Figure()

    # Add the Neon Line
    fig.add_trace(go.Scatter(
        x=driver_df['year'].astype(str) + " " + driver_df['name'],  # Label: "2023 Monaco"
        y=driver_df['positionOrder'],
        mode='lines+markers',
        line=dict(color='#00F0FF', width=3, shape='spline'),  # Cyan Spline
        marker=dict(size=6, color='black', line=dict(width=2, color='#00F0FF')),
        fill='tozeroy',  # Fill area below
        fillcolor='rgba(0, 240, 255, 0.1)'  # Transparent Cyan Glow
    ))

    # Style the Graph
    fig.update_layout(
        title=dict(text=f">> RECENT MOMENTUM: {full_name.upper()}",
                   font=dict(color="#666", size=10, family="Orbitron")),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=180,
        margin=dict(t=30, b=10, l=10, r=10),
        yaxis=dict(autorange="reversed", showgrid=True, gridcolor='rgba(255,255,255,0.05)', zeroline=False),
        # Invert Y so P1 is top
        xaxis=dict(showgrid=False, showticklabels=False)  # Hide X labels to keep it clean
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def render_legacy_chart(full_name_a, full_name_b):
    """
    Renders a Cumulative Points 'Race' between two drivers over their careers.
    """
    if RACE_DATA_CACHE is None:
        return

    # Filter for both drivers
    df = RACE_DATA_CACHE[RACE_DATA_CACHE['full_name'].isin([full_name_a, full_name_b])].copy()

    if df.empty:
        st.info("Insufficient data for comparison chart.")
        return

    # Sort by date to ensure the line goes forward in time
    df = df.sort_values(by='date')

    # Create the figure
    fig = go.Figure()

    # Define styles for A and B
    drivers = [full_name_a, full_name_b]
    colors = ['#FF1801', '#00F0FF']  # Red vs Cyan

    for i, driver in enumerate(drivers):
        # Filter driver specific data
        d_data = df[df['full_name'] == driver].copy()

        # Calculate Cumulative Points
        d_data['cumulative_points'] = d_data['points'].cumsum()

        # Add Trace
        fig.add_trace(go.Scatter(
            x=d_data['date'],
            y=d_data['cumulative_points'],
            mode='lines',
            name=driver.split()[-1].upper(),  # Show Surname in legend
            line=dict(color=colors[i], width=4),
            fill='tozeroy',  # Fill to bottom for "Mountain" effect
            fillcolor=f"rgba({int(colors[i][1:3], 16)}, {int(colors[i][3:5], 16)}, {int(colors[i][5:7], 16)}, 0.1)"
        ))

    # Cyberpunk Styling
    fig.update_layout(
        title=dict(text=">> LEGACY TRAJECTORY (CUMULATIVE POINTS)",
                   font=dict(color="#888", family="Orbitron", size=12)),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=300,
        margin=dict(t=40, b=20, l=20, r=20),
        xaxis=dict(
            showgrid=False,
            gridcolor='rgba(255,255,255,0.1)',
            tickfont=dict(color='#666')
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.05)',
            tickfont=dict(color='#666'),
            title="TOTAL POINTS"
        ),
        legend=dict(
            orientation="h",
            y=1.1,
            font=dict(color="white")
        ),
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# --- 6. HEADER ---
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown("<h1 class='neon-text'>F1 INTELLIGENCE TERMINAL</h1>", unsafe_allow_html=True)
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
    # UPDATED MENU
    mode = st.radio(
        "Navigation",
        [
            "⚡ SINGLE ANALYSIS",
            "⚔️ COMPARATIVE TELEMETRY",
            "🧬 DOPPELGÄNGER ENGINE",
            "🧑‍🚀 DRIVERS ARCHIVE",  # <--- NEW ENTRY
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
elif "DRIVERS ARCHIVE" in mode:
    mode = "Drivers Archive"
elif "RACE REWIND" in mode:
    mode = "Race Rewind"

# =========================================================
# MODULE 1: SINGLE ANALYSIS
# =========================================================
# =========================================================
# MODULE 1: SINGLE ANALYSIS
# =========================================================
if mode == "Single Analysis":
    c_left, c_right = st.columns([1, 2])
    with c_left:
        st.markdown("##### SELECT DRIVER")

        # 1. Dropdown (Now contains 'Michael Schumacher', 'Mick Schumacher', etc.)
        # but ONLY if they are in your JSON.
        sel_full_name = st.selectbox("Driver", DRIVER_LIST, label_visibility="collapsed")

        # 2. Get Stats (Finds the 'Schumacher' JSON entry for either Michael or Mick)
        d_stats = get_json_stats(sel_full_name)

        # 3. Render Badge (If stats found)
        if d_stats:
            render_driver_badge(sel_full_name, d_stats)

        # 4. Render Momentum Chart (Uses Full Name to show ONLY that person's races)
        st.markdown("<br>", unsafe_allow_html=True)
        render_momentum_chart(sel_full_name)

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
            # Extract surname for the AI backend (which likely expects just 'Schumacher')
            surname_extracted = sel_full_name.split()[-1]

            with st.spinner(f"ANALYZING {sel_full_name.upper()}..."):
                result = explain_driver(surname_extracted, question)
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
# =========================================================
# MODULE 2: COMPARATIVE TELEMETRY (RESULT-FIRST LAYOUT)
# =========================================================
elif mode == "Comparative Telemetry":
    st.markdown("##### ⚔️ HEAD-TO-HEAD TELEMETRY")

    # --- 1. SELECTION & ACTION ROW ---
    col_a, col_mid, col_b = st.columns([1, 0.4, 1])

    # -- DRIVER A --
    with col_a:
        d_a_full = st.selectbox("Driver A", DRIVER_LIST, index=0)
        s_a = get_json_stats(d_a_full)
        if s_a: render_driver_badge(d_a_full, s_a)

    # -- CENTER (VS + BUTTON) --
    with col_mid:
        st.markdown("""
        <div style="height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; padding-top: 40px;">
            <div style='font-family:Orbitron; font-size:1.5rem; color:#FF1801; text-shadow: 0 0 15px #FF1801; margin-bottom: 10px;'>VS</div>
        </div>
        """, unsafe_allow_html=True)

        # Primary Action Button
        run_sim = st.button("⚡ SIMULATE", use_container_width=True, type="primary")

    # -- DRIVER B --
    with col_b:
        d_b_full = st.selectbox("Driver B", DRIVER_LIST, index=1)
        s_b = get_json_stats(d_b_full)
        if s_b: render_driver_badge(d_b_full, s_b)

    # --- 2. LOGIC PROCESSING ---
    if s_a and s_b:
        # If button clicked, store result in session state
        if run_sim:
            st.session_state['sim_result'] = compare_drivers(d_a_full.split()[-1], d_b_full.split()[-1])
            st.session_state['sim_drivers'] = (d_a_full, d_b_full)

        # --- 3. AI REPORT (RENDERED FIRST) ---
        # We check if a result exists and display it HERE, right under the buttons
        if 'sim_result' in st.session_state and st.session_state.get('sim_drivers') == (d_a_full, d_b_full):
            res = st.session_state['sim_result']
            sur_a = d_a_full.split()[-1]
            sur_b = d_b_full.split()[-1]

            st.markdown(f"""
            <div class="glass-card" style="border-top: 3px solid #00F0FF; margin-top: 25px; margin-bottom: 25px; animation: slideIn 0.5s ease-out;">
                <div style="font-family:'Orbitron'; color:#00F0FF; margin-bottom:15px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:10px; display:flex; justify-content:space-between;">
                    <span>>> TACTICAL SIMULATION REPORT</span>
                    <span style="font-size:0.8rem; color:#666;">LOG_ID: {sur_a[:3].upper()}vs{sur_b[:3].upper()}</span>
                </div>
                <div style="font-family:'Rajdhani'; font-size:1.1rem; line-height:1.6; color:#e0e0e0; white-space: pre-line;">
                    {res}
                </div>
            </div>
            <style>
                @keyframes slideIn {{
                    from {{ opacity: 0; transform: translateY(-10px); }}
                    to {{ opacity: 1; transform: translateY(0); }}
                }}
            </style>
            """, unsafe_allow_html=True)

        # --- 4. VISUALIZATION ROW (RENDERED SECOND) ---
        # The graphs will naturally get pushed down when the report appears
        c_radar, c_legacy = st.columns([1, 1.5])

        with c_radar:
            st.markdown(
                "<div style='text-align:center; font-family:Orbitron; color:#888; font-size:0.8rem; margin-bottom:5px;'>ATTRIBUTE MATRIX</div>",
                unsafe_allow_html=True)
            st.plotly_chart(render_radar_chart(d_a_full, d_b_full, s_a, s_b), use_container_width=True,
                            config={'displayModeBar': False})

        with c_legacy:
            render_legacy_chart(d_a_full, d_b_full)

# =========================================================
# MODULE 3: DOPPELGÄNGER ENGINE
# =========================================================
elif mode == "Doppelgänger Engine":
    st.markdown("##### 🧬 STATISTICAL TWIN IDENTIFICATION")
    c_search, c_res = st.columns([1, 2])

    with c_search:
        st.markdown(
            """<div style="font-size:0.8rem; color:#aaa; margin-bottom:10px;">Map driver telemetry against historical DNA.</div>""",
            unsafe_allow_html=True)
        target_twin_full = st.selectbox("Target Driver", DRIVER_LIST)
        if target_twin_full:
            st.markdown(
                f"""<div style="background: rgba(0,0,0,0.3); border: 1px solid #00F0FF; padding: 12px; border-radius: 4px; margin: 15px 0; box-shadow: 0 0 10px rgba(0, 240, 255, 0.1);"><div style="color:#00F0FF; font-size:0.7rem; font-family:'Orbitron'; margin-bottom: 2px;">TARGET LOCKED</div><div style="color:white; font-weight:bold; font-size:1.1rem; letter-spacing: 1px;">{target_twin_full.upper()}</div></div>""",
                unsafe_allow_html=True)

        if st.button("INITIATE SCAN", type="primary"):
            if 'matches' in st.session_state: del st.session_state['matches']
            target_surname = target_twin_full.split()[-1]
            matches = get_similar_drivers(target_surname, DRIVER_DATA)
            if matches:
                st.session_state['matches'] = matches
                with st.spinner("CALCULATING VECTOR ALIGNMENT..."):
                    st.session_state['vec_exp'] = explain_similarity_multi(target_surname, matches)
            else:
                st.error("INSUFFICIENT DATA.")

    with c_res:
        if 'matches' in st.session_state:
            matches = st.session_state['matches']
            cols = st.columns(3)
            for i, col in enumerate(cols):
                if i < len(matches):
                    m = matches[i]
                    pct = int(m['similarity_score'] * 100)
                    with col:
                        st.markdown(
                            f"""<div class="glass-card" style="text-align:center; border-top:3px solid #00F0FF;"><div style="font-size:0.7rem; color:#888;">MATCH #{i + 1}</div><div style="font-size:1.2rem; font-weight:bold; color:white; margin:5px 0;">{m['surname']}</div><div style="font-size:2rem; font-family:'Orbitron'; color:#00F0FF;">{pct}%</div></div>""",
                            unsafe_allow_html=True)
            st.markdown(
                f"""<div class="glass-card" style="margin-top:10px;"><div style="color:#00F0FF; font-family:'Orbitron'; font-size:0.9rem; margin-bottom:10px; border-bottom:1px solid #333; padding-bottom:5px;">>> ANALYTICS</div><div style="color:#ccc; line-height:1.6;">{st.session_state.get('vec_exp', '...')}</div></div>""",
                unsafe_allow_html=True)
        else:
            idle_html = """
            <style>
                .holo-container {
                    height: 350px; background-color: #050505;
                    background-image: linear-gradient(rgba(0, 240, 255, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 240, 255, 0.1) 1px, transparent 1px);
                    background-size: 40px 40px; border: 1px solid #333; border-radius: 8px;
                    display: flex; flex-direction: column; justify-content: center; align-items: center; position: relative; box-shadow: inset 0 0 50px rgba(0,0,0,0.8);
                }
                .holo-icon { font-size: 4rem; color: rgba(0, 240, 255, 0.8); text-shadow: 0 0 20px rgba(0, 240, 255, 0.6); margin-bottom: 20px; animation: float 3s ease-in-out infinite; }
                @keyframes float { 0% { transform: translateY(0px); opacity: 0.8; } 50% { transform: translateY(-10px); opacity: 1; } 100% { transform: translateY(0px); opacity: 0.8; } }
                .holo-text { font-family: 'Orbitron'; color: white; font-size: 1.5rem; letter-spacing: 4px; background: rgba(0,0,0,0.6); padding: 5px 15px; border-radius: 4px; }
                .holo-sub { font-family: 'Rajdhani'; color: #00F0FF; margin-top: 5px; font-size: 1rem; text-transform: uppercase; }
            </style>
            <div class="holo-container"><div class="holo-icon">🧬</div><div class="holo-text">SYSTEM IDLE</div><div class="holo-sub">Initialize Driver Scan</div></div>
            """
            st.markdown(idle_html, unsafe_allow_html=True)
# =========================================================
# MODULE 4: RACE REWIND (ARCHIVE UI OVERHAUL)
# =========================================================
elif mode == "Race Rewind":

    # --- 1. HEADER ---
    st.markdown("##### 📖 STORY MODE")

    # --- 2. CONTROL PANEL UI (INPUTS) ---
    # We wrap the inputs in a styled container to make them look like a cohesive unit
    st.markdown("""
    <style>
        .control-panel {
            background: linear-gradient(180deg, rgba(20, 20, 25, 0.9) 0%, rgba(10, 10, 15, 0.95) 100%);
            border: 1px solid #333;
            border-top: 3px solid #FF1801; /* Ferrari Red Accent */
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.5);
        }
        .panel-header {
            font-family: 'Orbitron';
            color: #aaa;
            font-size: 0.8rem;
            letter-spacing: 2px;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
        }
        .step-label {
            font-family: 'Rajdhani';
            font-weight: bold;
            color: #FF1801;
            font-size: 0.9rem;
            margin-bottom: 5px;
        }
    </style>
    <div class="control-panel">
        <div class="panel-header">
            <span>ARCHIVE QUERY PROTOCOL</span>
            <span style="color:#FF1801;">● SECURE</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # We move the columns *up* to visually sit inside/below the header we just drew
    # (Streamlit doesn't allow widgets inside HTML, so we stack them closely)
    years = get_years()

    if not years:
        st.warning("⚠️ ARCHIVE DATABASE OFFLINE.")
    else:
        # --- THE INPUTS ---
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown("<div class='step-label'>SELECT ERA</div>", unsafe_allow_html=True)
            sel_year = st.selectbox("Season", years, label_visibility="collapsed")

        with c2:
            st.markdown("<div class='step-label'>TARGET EVENT</div>", unsafe_allow_html=True)
            races = get_races_for_year(sel_year)
            if not races.empty:
                sel_race = st.selectbox("Grand Prix", races['name'], label_visibility="collapsed")
                # Get Race Details
                race_row = races[races['name'] == sel_race].iloc[0]
                race_id = race_row['raceId']
                race_date = race_row['date']
            else:
                sel_race = None
                race_id = None

        with c3:
            st.markdown("<div class='step-label'>SELECT DRIVER</div>", unsafe_allow_html=True)
            if race_id:
                drivers = get_drivers_in_race(race_id)
                sel_driver = st.selectbox("Driver", drivers, label_visibility="collapsed")
            else:
                sel_driver = None
                st.selectbox("Driver", ["Wait for Race..."], disabled=True, label_visibility="collapsed")

        # --- DYNAMIC "RACE TICKET" ---
        # Show details about the selected race immediately to make it look responsive
        if sel_race:
            st.markdown(f"""
            <div style="margin-top: 15px; background: rgba(255,255,255,0.05); border-left: 3px solid #fff; padding: 10px; display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <div style="font-size:0.7rem; color:#888; font-family:'Orbitron';">EVENT CONFIRMED</div>
                    <div style="font-size:1.1rem; color:white; font-weight:bold;">{str(sel_race).upper()}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:0.7rem; color:#888; font-family:'Orbitron';">DATE LOG</div>
                    <div style="font-size:1.1rem; color:#FF1801; font-family:'Rajdhani';">{race_date}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- ACTION BUTTON ---
        if st.button("GENERATE NARRATIVE REPORT", type="primary", disabled=not sel_driver, use_container_width=True):
            with st.spinner("DECRYPTING RACE TELEMETRY..."):
                stats = get_race_story_stats(race_id, sel_driver)
                if stats:
                    story = narrate_race_story(stats)

                    # --- SUCCESS RESULT ---
                    st.markdown(f"""
                    <div class="glass-card" style="border-left: 4px solid #FF1801; margin-top: 20px; animation: slideIn 0.5s ease-out;">
                        <div style="display:flex; justify-content:space-between; border-bottom:1px solid #444; padding-bottom:10px; margin-bottom:10px;">
                            <div>
                                <span style="font-family:'Orbitron'; color:#aaa; font-size:0.8rem;">GRID</span>
                                <span style="font-family:'Rajdhani'; font-size:1.5rem; font-weight:bold; color:white;">P{stats['grid']}</span>
                            </div>
                            <div style="text-align:right;">
                                <span style="font-family:'Orbitron'; color:#aaa; font-size:0.8rem;">FINISH</span>
                                <span style="font-family:'Rajdhani'; font-size:1.5rem; font-weight:bold; color:#FF1801;">P{stats['finish']}</span>
                            </div>
                        </div>
                        <div style="margin-bottom: 15px; font-family:'Orbitron'; font-size:0.9rem; color:#FF1801;">
                            STATUS: {stats['status'].upper()}
                        </div>
                        <div style="line-height:1.8; font-size:1.1rem; color:#e0e0e0; font-family: 'Rajdhani', sans-serif; background: rgba(0,0,0,0.2); padding: 15px; border-radius: 4px;">
                            {story}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # --- IDLE STATE (If Button Not Clicked) ---
        # This keeps the bottom area looking cool instead of empty
        else:
            idle_archive_html = """
            <style>
                .archive-placeholder {
                    height: 250px;
                    border: 1px dashed rgba(255, 255, 255, 0.1);
                    background: rgba(0, 0, 0, 0.2);
                    border-radius: 8px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    margin-top: 20px;
                }
                .tape-icon {
                    font-size: 3rem;
                    opacity: 0.5;
                    margin-bottom: 10px;
                    animation: spin-slow 10s linear infinite;
                }
                .archive-text {
                    font-family: 'Orbitron';
                    color: #666;
                    font-size: 1rem;
                    letter-spacing: 2px;
                }
                @keyframes spin-slow { 100% { transform: rotate(360deg); } }
            </style>

            <div class="archive-placeholder">
                <div class="tape-icon">📼</div>
                <div class="archive-text">ARCHIVE VAULT LOCKED</div>
                <div style="font-size: 0.8rem; color: #444; margin-top: 5px; font-family: 'Rajdhani';">
                    Select parameters to begin reconstruction
                </div>
            </div>
            """
            st.markdown(idle_archive_html, unsafe_allow_html=True)

# =========================================================
# =========================================================
# MODULE 5: DRIVERS ARCHIVE
# =========================================================
elif mode == "Drivers Archive":

    # ---------- STATE ----------
    if "archive_selection" not in st.session_state:
        st.session_state["archive_selection"] = None

    def clear_selection():
        st.session_state["archive_selection"] = None

    # =====================================================
    # VIEW 1: DRIVER GRID (CHARACTER SELECT)
    # =====================================================
    if st.session_state["archive_selection"] is None:

        st.markdown("##### 🧑‍🚀SELECT PERSONA")

        archive_legends = [
            "Lando Norris", "Lewis Hamilton", "Max Verstappen",
            "Oscar Piastri", "Sebastian Vettel", "Charles Leclerc",
            "Fernando Alonso", "Niki Lauda", "Michael Schumacher",
            "Charles Leclerc", "Michael Schumacher", "Nigel Mansell"
        ]

        available_legends = [d for d in archive_legends if d in DRIVER_LIST]
        cols = st.columns(4)

        for i, driver in enumerate(available_legends):
            with cols[i % 4]:
                d_json = get_json_stats(driver)

                # ---- DRIVER IMAGE ----
                img_path = get_driver_image_path(driver)
                if img_path:
                    st.image(img_path, use_container_width=True)
                else:
                    st.markdown("""
                    <div style="height:140px; background:#111;
                                border:1px solid #333;
                                display:flex; align-items:center; justify-content:center;
                                border-radius:8px;">
                        <div style="font-family:'Orbitron'; color:#666;">NO IMAGE</div>
                    </div>
                    """, unsafe_allow_html=True)

                # ---- DRIVER CARD ----
                st.markdown(f"""
                <div style="margin-top:-6px; border:1px solid #333; border-radius:0 0 8px 8px;
                            background:rgba(255,255,255,0.05); padding:10px;">
                    <div style="font-family:'Orbitron'; font-size:0.85rem;
                                letter-spacing:1px; color:#fff;">
                        {driver.upper()}
                    </div>
                    <div style="font-family:'Rajdhani'; font-size:0.75rem;
                                color:#888; margin-top:2px;">
                        {d_json.get('team_name', 'LEGEND')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # ---- ACTION BUTTON ----
                if st.button("ACCESS DRIVER", key=f"arc_{i}", use_container_width=True):
                    st.session_state["archive_selection"] = driver
                    st.rerun()


    # =====================================================
    # VIEW 2: DRIVER PERSONA INTERFACE
    # =====================================================
    else:
        target_driver = st.session_state["archive_selection"]
        surname = target_driver.split()[-1]

        st.button("← RETURN TO ARCHIVE", on_click=clear_selection)

        # ---------- LOAD DRIVER DATA ----------
        df_d = RACE_DATA_CACHE[RACE_DATA_CACHE["full_name"] == target_driver]

        total_races = df_d["raceId"].nunique()
        wins = df_d[df_d["positionOrder"] == 1]["raceId"].nunique()

        valid_finishes = df_d[df_d["positionOrder"].notna()]
        avg_finish = valid_finishes["positionOrder"].mean()

        # ---------- CONSTRUCTORS ----------
        df_cons = pd.read_csv("data/constructors.csv")
        df_cons = df_cons.rename(columns={"name": "constructor_name"})

        df_d = df_d.merge(
            df_cons[["constructorId", "constructor_name"]],
            on="constructorId",
            how="left"
        )

        teams = df_d["constructor_name"].dropna().unique().tolist()

        # ---------- ERA ----------
        first_year = df_d["year"].min()
        last_year = df_d["year"].max()

        if last_year >= 2023:
            era = "Modern Era"
        elif last_year >= 2014:
            era = "Hybrid Era"
        elif last_year >= 2000:
            era = "V10 / V8 Era"
        elif last_year >= 1980:
            era = "Turbo Era"
        else:
            era = "Classic Era"

        d_json = get_json_stats(target_driver)

        col_L, col_R = st.columns([1, 2])

        # ---------------- LEFT PANEL ----------------
        with col_L:
            img_path = get_driver_image_path(target_driver)
            if img_path:
                st.image(img_path, use_container_width=True)
            else:
                st.markdown("""
                <div style="height:300px; background:#111;
                            border:2px solid #333; border-radius:10px;
                            display:flex; align-items:center; justify-content:center;">
                    <div style="font-family:'Orbitron'; color:#666;">NO IMAGE DATA</div>
                </div>
                """, unsafe_allow_html=True)

            if wins > 20:
                quote = "I didn’t race to participate. I raced to dominate."
            elif total_races > 100:
                quote = "Consistency was my weapon. The grid was my home."
            else:
                quote = "Every lap was a battle for survival."

            st.markdown(f"""
            <div style="margin-top:15px; border-left:3px solid #00F0FF; padding-left:15px;">
                <div style="font-family:'Rajdhani'; font-style:italic;
                            font-size:1.25rem; line-height:1.6; color:#fff;">
                    "{quote}"
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ---------------- RIGHT PANEL ----------------
        with col_R:
            # ---------- DATA DECK ----------
            # FIX: We remove the indentation inside the string so Markdown doesn't treat it as a code block
            st.markdown(f"""
        <div class="glass-card">
            <div style="display:grid; grid-template-columns: repeat(4,1fr); gap:10px; text-align:center;">
                <div>
                    <div style="font-family:'Orbitron'; font-size:0.65rem; letter-spacing:1px; color:#888;">RACES</div>
                    <div style="font-family:'Orbitron'; font-size:1.6rem; color:white;">{total_races}</div>
                </div>
                <div>
                    <div style="font-family:'Orbitron'; font-size:0.65rem; letter-spacing:1px; color:#888;">WINS</div>
                    <div style="font-family:'Orbitron'; font-size:1.6rem; color:#FF1801;">{wins}</div>
                </div>
                <div>
                    <div style="font-family:'Orbitron'; font-size:0.65rem; letter-spacing:1px; color:#888;">AVG FINISH</div>
                    <div style="font-family:'Orbitron'; font-size:1.6rem; color:white;">{avg_finish:.1f}</div>
                </div>
                <div>
                    <div style="font-family:'Orbitron'; font-size:0.65rem; letter-spacing:1px; color:#888;">ERA</div>
                    <div style="font-family:'Orbitron'; font-size:1.4rem; color:white;">{era}</div>
                </div>
            </div>
            <div style="margin-top:15px; border-top:1px solid #333; padding-top:10px;">
                <span style="font-family:'Orbitron'; font-size:0.7rem; letter-spacing:1px; color:#00F0FF;">
                    KNOWN TEAMS:
                </span>
                <span style="font-family:'Rajdhani'; font-size:0.95rem; color:#aaa;">
                    {", ".join(teams[:4])}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

            # ---------- CHAT ----------
            st.markdown("##### 💬 ASK THE DRIVER")
            if "archive_chat" not in st.session_state:
                st.session_state["archive_chat"] = []

            if (
                "last_archive_driver" not in st.session_state
                or st.session_state["last_archive_driver"] != target_driver
            ):
                st.session_state["archive_chat"] = []
                st.session_state["last_archive_driver"] = target_driver

            for q, a in st.session_state["archive_chat"]:
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.05); padding:10px; border-radius:5px; margin-bottom:5px;">
                    <div style="font-family:'Orbitron'; font-size:0.65rem; letter-spacing:1px; color:#888;">YOU</div>
                    <div style="font-family:'Rajdhani'; font-size:1rem; color:white;">{q}</div>
                </div>

                <div style="background:rgba(0,240,255,0.1); border-left:3px solid #00F0FF;
                            padding:10px; border-radius:0 5px 5px 0; margin-bottom:15px;">
                    <div style="font-family:'Orbitron'; font-size:0.65rem; letter-spacing:1px; color:#00F0FF;">
                        {surname.upper()}
                    </div>
                    <div style="font-family:'Rajdhani'; font-size:1.1rem; line-height:1.6; color:white;">
                        {a}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with st.form("archive_chat_form"):
                user_q = st.text_input("Interview Question",
                                       placeholder=f"Ask {surname} about their greatest race…")
                send = st.form_submit_button("TRANSMIT MESSAGE")

            if send and user_q:
                stats_payload = {
                    "races": total_races,
                    "wins": wins,
                    "avg_finish": avg_finish,
                    "teams": teams
                }

                reply = generate_persona_response(
                    target_driver,
                    user_q,
                    stats_payload,
                    d_json
                )

                st.session_state["archive_chat"].append((user_q, reply))
                st.rerun()


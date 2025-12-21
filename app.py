import streamlit as st
import json
import plotly.graph_objects as go

# --- ERROR HANDLING FOR BACKEND ---
# This ensures the UI renders even if backend logic fails or files are missing
try:
    from f1_explain import explain_driver, compare_drivers
except ImportError:
    st.error("⚠️ Backend modules not found. Please ensure f1_explain.py is in the directory.")


    def explain_driver(d, q):
        return f"Mock analysis for {d}: {q}"


    def compare_drivers(d1, d2):
        return f"Mock comparison between {d1} and {d2}"

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="F1 Performance Analyst AI",
    layout="wide",
    page_icon="🏎️",
    initial_sidebar_state="expanded"
)

# --- LOAD DATA ---
try:
    with open("driver_knowledge.json", "r") as f:
        DRIVER_DATA = json.load(f)
    DRIVER_NAMES = sorted(list({d["surname"] for d in DRIVER_DATA}))
except FileNotFoundError:
    st.warning("⚠️ driver_knowledge.json not found. Using placeholder data.")
    DRIVER_DATA = []
    DRIVER_NAMES = ["Verstappen", "Hamilton", "Leclerc", "Norris", "Alonso"]


# --- CUSTOM CSS (THE VISUALS) ---
def local_css():
    st.markdown("""
    <style>
        /* Import Titillium Web - A very 'tech/sport' font */
        @import url('https://fonts.googleapis.com/css2?family=Titillium+Web:wght@300;400;700&display=swap');

        /* APP BACKGROUND */
        .stApp {
            background-color: #0e1117;
            background-image: radial-gradient(circle at 50% 0%, #1c1c2e 0%, #0e1117 70%);
            color: #ffffff;
            font-family: 'Titillium Web', sans-serif;
        }

        /* TYPOGRAPHY */
        h1, h2, h3, h4 {
            font-family: 'Titillium Web', sans-serif;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        h1 {
            color: #FF1801; /* F1 Red */
            font-weight: 800;
            font-style: italic;
            text-shadow: 0px 0px 10px rgba(255, 24, 1, 0.3);
        }

        /* SIDEBAR */
        section[data-testid="stSidebar"] {
            background-color: #121212;
            border-right: 1px solid #333;
        }

        /* BUTTONS */
        div.stButton > button {
            background-color: #FF1801;
            color: white;
            border: none;
            border-radius: 0px; /* Sharp edges for racing look */
            padding: 0.5rem 1rem;
            font-weight: bold;
            text-transform: uppercase;
            clip-path: polygon(10% 0, 100% 0, 100% 100%, 0% 100%); /* Angled button */
            transition: all 0.3s ease;
            width: 100%;
        }

        div.stButton > button:hover {
            background-color: #D90000;
            transform: translateX(5px);
        }

        /* RESULT CARDS */
        .result-card {
            background-color: #1a1a24;
            border-top: 3px solid #FF1801;
            padding: 25px;
            border-radius: 5px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.5);
            margin-top: 20px;
        }

        .result-text {
            font-size: 1.1rem;
            color: #e0e0e0;
            line-height: 1.6;
        }

        /* METRIC BOXES */
        .metric-box {
            background: rgba(255, 255, 255, 0.05);
            padding: 10px;
            border-radius: 5px;
            text-align: center;
            border: 1px solid #333;
        }
        .metric-label { font-size: 0.8rem; color: #888; text-transform: uppercase; }
        .metric-value { font-size: 1.5rem; font-weight: bold; color: white; }

        /* FOOTER */
        .footer {
            position: fixed; bottom: 0; left: 0; width: 100%;
            background: #000; color: #444; text-align: center;
            font-size: 0.7rem; padding: 5px; z-index: 100;
        }
    </style>
    """, unsafe_allow_html=True)


local_css()


# --- HELPER: RADAR CHART GENERATOR ---
def create_radar_chart(driver_a_stats, driver_b_stats):
    """
    Creates a comparative radar chart.
    Note: We invert some stats (like avg_finish) so that 'Outer' is always 'Better'.
    """
    categories = ['Avg Position', 'Consistency', 'Team Delta', 'Experience']

    # --- SCORING LOGIC (Normalizing to 0-100) ---
    # 1. Avg Finish: Finish 1 = Score 100. Finish 20 = Score 0.
    def score_finish(val): return max(0, (22 - val) / 22 * 100)

    # 2. Consistency (Std Dev): 0 deviation = Score 100. 10 deviation = Score 0.
    def score_const(val): return max(0, (12 - val) / 12 * 100)

    # 3. Team Delta: 0 (matches team) = Score 80. Negative (beats team) -> 100. Positive (loses) -> 0.
    # We assume 'delta_vs_team' is a position or time delta.
    def score_delta(val): return max(0, (10 - val) / 10 * 100)

    # 4. Experience: Cap at 100 races
    def score_exp(val): return min(100, (val / 100) * 100)

    # Process Driver A
    val_a = [
        score_finish(driver_a_stats.get('avg_finish', 20)),
        score_const(driver_a_stats.get('finish_std', 10)),
        score_delta(driver_a_stats.get('delta_vs_team', 5)),
        score_exp(driver_a_stats.get('races', 0))
    ]

    # Process Driver B
    val_b = [
        score_finish(driver_b_stats.get('avg_finish', 20)),
        score_const(driver_b_stats.get('finish_std', 10)),
        score_delta(driver_b_stats.get('delta_vs_team', 5)),
        score_exp(driver_b_stats.get('races', 0))
    ]

    fig = go.Figure()

    # Driver A Layer
    fig.add_trace(go.Scatterpolar(
        r=val_a, theta=categories,
        fill='toself', name=driver_a_stats['surname'],
        line_color='#FF1801', opacity=0.7
    ))

    # Driver B Layer
    fig.add_trace(go.Scatterpolar(
        r=val_b, theta=categories,
        fill='toself', name=driver_b_stats['surname'],
        line_color='#FFFFFF', opacity=0.6
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, linecolor='#333'),
            bgcolor='rgba(255,255,255,0.05)',
            gridshape='linear'
        ),
        paper_bgcolor='rgba(0,0,0,0)',  # Transparent
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', family="Titillium Web"),
        margin=dict(l=40, r=40, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig


# --- SIDEBAR NAV ---
with st.sidebar:
    st.title("🏎️ Paddock")
    st.markdown("---")
    mode = st.radio(
        "Select Telemetry Mode",
        ["Single Driver Analysis", "Driver Comparison"],
        captions=["Detailed profile & AI insights", "Head-to-head stats & visualization"]
    )
    st.markdown("---")
    st.info("💡 **Tip:** Comparison mode activates the Telemetry Wall.")

# --- HEADER ---
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.title("F1 Performance Analyst")
    st.caption("GenAI Powered Telemetry & Strategy Insights")
with col_h2:
    st.markdown("<div style='text-align:right; font-size:3rem;'>🏁</div>", unsafe_allow_html=True)

st.write("")  # Spacer

# ==========================================
# MODE 1: SINGLE DRIVER ANALYSIS
# ==========================================
if mode == "Single Driver Analysis":
    st.subheader("🔍 Driver Deep Dive")

    c1, c2 = st.columns([1, 2])

    with c1:
        st.markdown("##### Driver Selection")
        driver = st.selectbox("Select Driver", DRIVER_NAMES, label_visibility="collapsed")

        # Display mini stats if available
        d_stats = next((d for d in DRIVER_DATA if d["surname"] == driver), None)
        if d_stats:
            st.markdown(f"""
            <div style="margin-top: 10px;">
                <div class="metric-box">
                    <div class="metric-label">Races</div>
                    <div class="metric-value">{d_stats.get('races', 'N/A')}</div>
                </div>
                <div class="metric-box" style="margin-top:5px;">
                    <div class="metric-label">Team</div>
                    <div class="metric-value" style="font-size:1rem;">{d_stats.get('team_name', 'N/A')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with c2:
        st.markdown("##### Inquiry")
        question = st.selectbox(
            "Select Analysis Question",
            [
                "Is this driver winning because of skill or car advantage?",
                "How consistent is this driver under race pressure?",
                "Would this driver still perform well in a weaker car?",
                "What kind of driver profile does this data suggest?"
            ],
            label_visibility="collapsed"
        )

        st.write("")
        if st.button("Initialize Analysis ➜", use_container_width=True):
            with st.spinner("Processing Telemetry..."):
                try:
                    result = explain_driver(driver, question)
                    st.markdown(f"""
                    <div class="result-card">
                        <h4 style="color:#FF1801; margin-top:0;">AI Analysis Output</h4>
                        <div class="result-text">{result}</div>
                    </div>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Analysis failed: {e}")

# ==========================================
# MODE 2: DRIVER COMPARISON (WITH TELEMETRY WALL)
# ==========================================
elif mode == "Driver Comparison":
    st.subheader("⚔️ Head-to-Head Telemetry")

    # Selection Row
    c_a, c_mid, c_b = st.columns([1, 0.2, 1])
    with c_a:
        driver_a = st.selectbox("Driver A", DRIVER_NAMES, key="da")
    with c_mid:
        st.markdown("<h2 style='text-align:center; color:#FF1801;'>VS</h2>", unsafe_allow_html=True)
    with c_b:
        driver_b = st.selectbox("Driver B", DRIVER_NAMES, key="db")

    # The Telemetry Wall (Visuals)
    st.markdown("### 📊 The Telemetry Wall")

    # Fetch Data
    d_a_stats = next((d for d in DRIVER_DATA if d["surname"] == driver_a), None)
    d_b_stats = next((d for d in DRIVER_DATA if d["surname"] == driver_b), None)

    if d_a_stats and d_b_stats:
        # Create columns: Left for text stats, Right for Radar Chart
        chart_col1, chart_col2 = st.columns([1, 2])

        with chart_col1:
            st.markdown(f"**{driver_a}**")
            st.progress(min(100, int((22 - d_a_stats.get('avg_finish', 20)) / 22 * 100)))
            st.caption(f"Avg Finish: {d_a_stats.get('avg_finish', 0):.1f}")

            st.markdown(f"**{driver_b}**")
            st.progress(min(100, int((22 - d_b_stats.get('avg_finish', 20)) / 22 * 100)))
            st.caption(f"Avg Finish: {d_b_stats.get('avg_finish', 0):.1f}")

            st.info("Charts normalized for visualization (Outer edge = Better performance)")

        with chart_col2:
            fig = create_radar_chart(d_a_stats, d_b_stats)
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("Insufficient data to generate charts.")

    # AI Analysis Button
    st.markdown("### 🧠 AI Comparative Analysis")
    if st.button("Run Simulation & Analysis ➜", use_container_width=True):
        with st.spinner("Calculating performance deltas..."):
            try:
                result = compare_drivers(driver_a, driver_b)
                st.markdown(f"""
                <div class="result-card">
                    <h4 style="color:#FF1801; margin-top:0;">Tactical Breakdown</h4>
                    <div class="result-text">{result}</div>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Comparison failed: {e}")

# --- FOOTER ---
st.markdown("""
<div class="footer">
    F1 Performance Analyst | Not affiliated with Formula 1 | Data driven by Groq & Llama 3
</div>
""", unsafe_allow_html=True)
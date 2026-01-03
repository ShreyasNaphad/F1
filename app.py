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
            background: rgba(0, 0, 0, 0.6) !important; 
            backdrop-filter: blur(15px); 
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
            text-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
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

        /* --- 6. BUTTONS (FIX FOR RENDER) --- */
        /* Primary (Simulate) - RED */
        button[kind="primary"] {
            background-color: #FF1801 !important;
            border: 1px solid #FF1801 !important;
            color: white !important;
            font-family: 'Orbitron', sans-serif !important;
            transition: all 0.3s ease !important;
        }
        button[kind="primary"]:hover {
            background-color: #D00000 !important;
            box-shadow: 0 0 15px rgba(255, 24, 1, 0.6) !important;
            transform: scale(1.02);
        }
        
        /* Secondary (Initialize AI) - Outline Red */
        div.stButton > button[kind="secondary"] {
            border: 1px solid #FF1801 !important;
            color: #FF1801 !important;
            font-family: 'Orbitron', sans-serif !important;
            background: transparent !important;
        }
        div.stButton > button[kind="secondary"]:hover {
            border-color: #00F0FF !important;
            color: #00F0FF !important;
            box-shadow: 0 0 10px rgba(0, 240, 255, 0.4) !important;
        }

        /* --- 7. INPUT FIELDS (FIX FOR BLACK BOXES) --- */
        /* Force the dropdowns/text-boxes to be Grey/Glassy */
        div[data-baseweb="select"] > div, 
        div[data-baseweb="input"] > div {
            background-color: rgba(255, 255, 255, 0.1) !important;
            border-color: rgba(255, 255, 255, 0.2) !important;
            color: white !important;
        }
        
        /* Fix the text color inside the box */
        div[data-baseweb="select"] span {
            color: white !important;
        }

        /* Fix the dropdown menu popup (the list that appears) */
        ul[data-baseweb="menu"] {
            background-color: #0a0a0e !important;
            border: 1px solid #333 !important;
        }
        
        /* Highlight color in dropdown list */
        li[aria-selected="true"] {
            background-color: rgba(255, 24, 1, 0.3) !important;
            color: white !important;
        }

    </style>
    """, unsafe_allow_html=True)

import streamlit as st

def inject_css():
    st.markdown("""
    <style>

    /* ── Polices Google ─────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ── Global ─────────────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    /* ── Sidebar ─────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1A1A2E 0%, #16213E 100%) !important;
        border-right: 1px solid #2D2D5E;
    }
    [data-testid="stSidebar"] * {
        color: #E8E8F0 !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        padding: 8px 12px;
        border-radius: 8px;
        transition: background 0.2s;
        display: block;
        margin: 2px 0;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(83, 74, 183, 0.3) !important;
    }

    /* ── Titres ──────────────────────────────────────────────── */
    h1 {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #1A1A2E !important;
        border-bottom: 3px solid #534AB7;
        padding-bottom: 0.5rem;
        margin-bottom: 1.5rem !important;
    }
    h2, h3 {
        font-weight: 600 !important;
        color: #2D2D5E !important;
    }

    /* ── Boutons principaux ──────────────────────────────────── */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 500 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.2s ease !important;
        border: 1.5px solid #534AB7 !important;
        padding: 0.5rem 1.2rem !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(83, 74, 183, 0.3) !important;
        background: #534AB7 !important;
        color: white !important;
    }
    .stButton > button[kind="primary"] {
        background: #534AB7 !important;
        color: white !important;
    }

    /* ── Métriques ───────────────────────────────────────────── */
    [data-testid="stMetric"] {
        background: white;
        border-radius: 12px;
        padding: 1rem 1.2rem !important;
        border: 1px solid #E0DFFF;
        box-shadow: 0 2px 8px rgba(83, 74, 183, 0.08);
        transition: box-shadow 0.2s;
    }
    [data-testid="stMetric"]:hover {
        box-shadow: 0 4px 16px rgba(83, 74, 183, 0.15);
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
        color: #666 !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #534AB7 !important;
    }

    /* ── Zones de texte et inputs ────────────────────────────── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 10px !important;
        border: 1.5px solid #D0CFFF !important;
        font-family: 'Inter', sans-serif !important;
        transition: border-color 0.2s !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #534AB7 !important;
        box-shadow: 0 0 0 3px rgba(83, 74, 183, 0.15) !important;
    }

    /* ── Code ────────────────────────────────────────────────── */
    code, pre, .stCode {
        font-family: 'JetBrains Mono', monospace !important;
        border-radius: 10px !important;
    }
    [data-testid="stCode"] {
        border: 1px solid #E0DFFF !important;
        border-radius: 10px !important;
    }

    /* ── Alertes / Info / Success / Error ────────────────────── */
    [data-testid="stAlert"] {
        border-radius: 10px !important;
        border: none !important;
        font-weight: 500 !important;
    }

    /* ── Selectbox ───────────────────────────────────────────── */
    .stSelectbox > div > div {
        border-radius: 10px !important;
        border: 1.5px solid #D0CFFF !important;
    }

    /* ── Divider ─────────────────────────────────────────────── */
    hr {
        border-color: #E0DFFF !important;
        margin: 1.5rem 0 !important;
    }

    /* ── Chat messages ───────────────────────────────────────── */
    [data-testid="stChatMessage"] {
        border-radius: 12px !important;
        margin-bottom: 0.5rem !important;
        border: 1px solid #E0DFFF !important;
    }
    [data-testid="stChatInput"] > div {
        border-radius: 12px !important;
        border: 1.5px solid #D0CFFF !important;
    }

    /* ── Dataframe ───────────────────────────────────────────── */
    [data-testid="stDataFrame"] {
        border-radius: 10px !important;
        overflow: hidden !important;
        border: 1px solid #E0DFFF !important;
    }

    /* ── Cards personnalisées ────────────────────────────────── */
    .tuteur-card {
        background: white;
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        border: 1px solid #E0DFFF;
        box-shadow: 0 2px 8px rgba(83, 74, 183, 0.07);
        margin-bottom: 1rem;
        transition: box-shadow 0.2s, transform 0.2s;
    }
    .tuteur-card:hover {
        box-shadow: 0 6px 20px rgba(83, 74, 183, 0.15);
        transform: translateY(-2px);
    }
    .tuteur-badge {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .badge-facile   { background: #EAF3DE; color: #3B6D11; }
    .badge-moyen    { background: #FAEEDA; color: #854F0B; }
    .badge-difficile{ background: #FCEBEB; color: #A32D2D; }
    .badge-algo     { background: #EEEDFE; color: #3C3489; }
    .badge-c        { background: #E1F5EE; color: #085041; }
    .badge-html     { background: #FFF0E0; color: #8A4500; }
    .badge-js       { background: #FFFBE0; color: #7A6000; }

    /* ── Page de connexion ───────────────────────────────────── */
    .auth-container {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        border: 1px solid #E0DFFF;
        box-shadow: 0 8px 32px rgba(83, 74, 183, 0.12);
    }

    /* ── Scrollbar ───────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #F8F7FF; }
    ::-webkit-scrollbar-thumb {
        background: #C0BFFF;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover { background: #534AB7; }

    /* ── Spinner ─────────────────────────────────────────────── */
    .stSpinner > div {
        border-top-color: #534AB7 !important;
    }

    </style>
    """, unsafe_allow_html=True)

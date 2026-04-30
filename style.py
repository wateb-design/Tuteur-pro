import streamlit as st

def inject_css():
    st.markdown("""
    <style>

    /* ── Polices Google ─────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ── Global ─────────────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        background-color: #F4F7FC !important;
        color: #1A202C !important;
    }

    /* ── Sidebar ─────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #778899 0%, #1A3354 100%) !important;
        border-right: 1px solid #2A4A7F !important;
    }
    [data-testid="stSidebar"] * {
        color: #E8F0FE !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        padding: 8px 12px;
        border-radius: 8px;
        transition: background 0.2s;
        display: block;
        margin: 2px 0;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(255, 255, 255, 0.1) !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: rgba(232, 240, 254, 0.75) !important;
        font-size: 0.9rem;
    }

    /* ── Titres ──────────────────────────────────────────────── */
    h1 {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #1A202C !important;
        border-bottom: 3px solid #0D9AFC !important;
        padding-bottom: 0.5rem !important;
        margin-bottom: 1.5rem !important;
    }
    h2, h3, h4 {
        font-weight: 600 !important;
        color: #1A202C !important;
    }

    /* ── Boutons ─────────────────────────────────────────────── */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 500 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.2s ease !important;
        border: 1.5px solid #0D9AFC !important;
        color: #0D9AFC !important;
        background: white !important;
        padding: 0.5rem 1.2rem !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(13, 154, 252, 0.3) !important;
        background: #0D9AFC !important;
        color: white !important;
    }
    .stButton > button[kind="primary"] {
        background: #0D9AFC !important;
        color: white !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: #0A7FD4 !important;
    }

    /* ── Métriques ───────────────────────────────────────────── */
    [data-testid="stMetric"] {
        background: white !important;
        border-radius: 14px !important;
        padding: 1rem 1.2rem !important;
        border: 1px solid #D0E4F7 !important;
        box-shadow: 0 2px 8px rgba(13, 154, 252, 0.08) !important;
        transition: box-shadow 0.2s, transform 0.2s !important;
    }
    [data-testid="stMetric"]:hover {
        box-shadow: 0 6px 20px rgba(13, 154, 252, 0.15) !important;
        transform: translateY(-2px) !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.78rem !important;
        color: #718096 !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #0D9AFC !important;
    }

    /* ── Inputs et TextArea ──────────────────────────────────── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 10px !important;
        border: 1.5px solid #D0E4F7 !important;
        background: white !important;
        font-family: 'Inter', sans-serif !important;
        color: #1A202C !important;
        transition: border-color 0.2s !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #0D9AFC !important;
        box-shadow: 0 0 0 3px rgba(13, 154, 252, 0.15) !important;
    }

    /* ── Selectbox ───────────────────────────────────────────── */
    .stSelectbox > div > div {
        border-radius: 10px !important;
        border: 1.5px solid #D0E4F7 !important;
        background: white !important;
    }

    /* ── Code ────────────────────────────────────────────────── */
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
        border-radius: 10px !important;
    }
    [data-testid="stCode"] {
        border: 1px solid #D0E4F7 !important;
        border-radius: 10px !important;
        background: #F0F7FF !important;
    }

    /* ── Alertes ─────────────────────────────────────────────── */
    [data-testid="stAlert"] {
        border-radius: 10px !important;
        border: none !important;
        font-weight: 500 !important;
    }

    /* ── Cartes personnalisées ───────────────────────────────── */
    .tuteur-card {
        background: white;
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        border: 1px solid #D0E4F7;
        box-shadow: 0 2px 8px rgba(13, 154, 252, 0.07);
        margin-bottom: 1rem;
        transition: box-shadow 0.2s, transform 0.2s;
    }
    .tuteur-card:hover {
        box-shadow: 0 6px 20px rgba(13, 154, 252, 0.15);
        transform: translateY(-2px);
    }

    /* ── Badges ──────────────────────────────────────────────── */
    .tuteur-badge {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .badge-facile    { background: #EAF3DE; color: #3B6D11; }
    .badge-moyen     { background: #FEF3C7; color: #92400E; }
    .badge-difficile { background: #FEE2E2; color: #991B1B; }
    .badge-algo      { background: #EFF6FF; color: #1D4ED8; }
    .badge-c         { background: #ECFDF5; color: #065F46; }
    .badge-html      { background: #FFF7ED; color: #9A3412; }
    .badge-js        { background: #FEFCE8; color: #713F12; }

    /* ── Chat ────────────────────────────────────────────────── */
    [data-testid="stChatMessage"] {
        border-radius: 12px !important;
        margin-bottom: 0.5rem !important;
        border: 1px solid #D0E4F7 !important;
        background: white !important;
    }
    [data-testid="stChatInput"] > div {
        border-radius: 12px !important;
        border: 1.5px solid #D0E4F7 !important;
        background: white !important;
    }

    /* ── Dataframe ───────────────────────────────────────────── */
    [data-testid="stDataFrame"] {
        border-radius: 10px !important;
        overflow: hidden !important;
        border: 1px solid #D0E4F7 !important;
        background: white !important;
    }

    /* ── Divider ─────────────────────────────────────────────── */
    hr {
        border-color: #D0E4F7 !important;
        margin: 1.5rem 0 !important;
    }

    /* ── Scrollbar ───────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #F4F7FC; }
    ::-webkit-scrollbar-thumb {
        background: #90CAF9;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover { background: #0D9AFC; }

    /* ── Spinner ─────────────────────────────────────────────── */
    .stSpinner > div {
        border-top-color: #0D9AFC !important;
    }

     /* ── Bouton déconnexion ──────────────────────────────────── */
    [data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        border: 1.5px solid rgba(255,255,255,0.3) !important;
        color: #E8F0FE !important;
        border-radius: 10px !important;
        width: 100% !important;
        margin-top: 0.5rem !important;
        font-size: 0.85rem !important;
        transition: all 0.2s !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(220, 53, 69, 0.2) !important;
        border-color: #DC3545 !important;
        color: #FF8A95 !important;
        transform: none !important;
        box-shadow: none !important;
    }

    </style>
    """, unsafe_allow_html=True)

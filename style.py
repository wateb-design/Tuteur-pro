import streamlit as st

def inject_css():
    st.markdown("""
    <style>

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        background-color: #F5F7FA !important;
        color: #1A237E !important;
    }

    [data-testid="stSidebar"] {
        background: #2D3748 !important;
        border-right: none !important;
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
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
        color: rgba(255,255,255,0.75) !important;
        font-size: 0.9rem;
    }
    [data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        border: 1.5px solid rgba(255,255,255,0.3) !important;
        color: #E3F2FD !important;
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

    h1 {
        font-size: 1.8rem !important;
        font-weight: 500 !important;
        color: #1A237E !important;
        border-bottom: 3px solid #1565C0 !important;
        padding-bottom: 0.5rem !important;
        margin-bottom: 1.5rem !important;
    }
    h2, h3, h4 {
        font-weight: 500 !important;
        color: #1A237E !important;
    }

    .stButton > button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.2s ease !important;
        border: 1.5px solid #1565C0 !important;
        color: #1565C0 !important;
        background: white !important;
        padding: 0.5rem 1.2rem !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(21, 101, 192, 0.25) !important;
        background: #1565C0 !important;
        color: white !important;
    }
    .stButton > button[kind="primary"] {
        background: #1565C0 !important;
        color: white !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: #0D47A1 !important;
    }

    [data-testid="stMetric"] {
        background: white !important;
        border-radius: 14px !important;
        padding: 1rem 1.2rem !important;
        border: 1px solid #BBDEFB !important;
        box-shadow: 0 2px 8px rgba(21, 101, 192, 0.07) !important;
        transition: box-shadow 0.2s, transform 0.2s !important;
    }
    [data-testid="stMetric"]:hover {
        box-shadow: 0 6px 20px rgba(21, 101, 192, 0.14) !important;
        transform: translateY(-2px) !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.78rem !important;
        color: #5C6BC0 !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 500 !important;
        color: #1565C0 !important;
    }

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 8px !important;
        border: 1.5px solid #BBDEFB !important;
        background: white !important;
        font-family: 'Inter', sans-serif !important;
        color: #1A237E !important;
        transition: border-color 0.2s !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #1565C0 !important;
        box-shadow: 0 0 0 3px rgba(21, 101, 192, 0.12) !important;
    }

    .stSelectbox > div > div {
        border-radius: 8px !important;
        border: 1.5px solid #BBDEFB !important;
        background: white !important;
    }

    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
        border-radius: 8px !important;
    }
    [data-testid="stCode"] {
        border: 1px solid #BBDEFB !important;
        border-radius: 8px !important;
        background: #E3F2FD !important;
    }

    [data-testid="stAlert"] {
        border-radius: 8px !important;
        border: none !important;
        font-weight: 500 !important;
    }

    .tuteur-card {
        background: white;
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        border: 1px solid #BBDEFB;
        box-shadow: 0 2px 8px rgba(21, 101, 192, 0.06);
        margin-bottom: 1rem;
        transition: box-shadow 0.2s, transform 0.2s;
    }
    .tuteur-card:hover {
        box-shadow: 0 6px 20px rgba(21, 101, 192, 0.13);
        transform: translateY(-2px);
    }
    .tuteur-badge {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 500;
        margin-bottom: 8px;
    }
    .badge-facile    { background: #EAF3DE; color: #3B6D11; }
    .badge-moyen     { background: #FEF3C7; color: #92400E; }
    .badge-difficile { background: #FEE2E2; color: #991B1B; }
    .badge-algo      { background: #E3F2FD; color: #0D47A1; }
    .badge-c         { background: #E8F5E9; color: #1B5E20; }
    .badge-html      { background: #FFF3E0; color: #E65100; }
    .badge-js        { background: #FFFDE7; color: #F57F17; }

    [data-testid="stChatMessage"] {
        border-radius: 12px !important;
        margin-bottom: 0.5rem !important;
        border: 1px solid #BBDEFB !important;
        background: white !important;
    }
    [data-testid="stChatInput"] > div {
        border-radius: 12px !important;
        border: 1.5px solid #BBDEFB !important;
        background: white !important;
    }

    [data-testid="stDataFrame"] {
        border-radius: 10px !important;
        overflow: hidden !important;
        border: 1px solid #BBDEFB !important;
        background: white !important;
    }

    hr {
        border-color: #BBDEFB !important;
        margin: 1.5rem 0 !important;
    }

    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #F5F7FA; }
    ::-webkit-scrollbar-thumb {
        background: #90CAF9;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover { background: #1565C0; }

    .stSpinner > div {
        border-top-color: #1565C0 !important;
    }

    .stProgress > div > div {
        background: #1565C0 !important;
        border-radius: 4px !important;
    }

    [data-testid="stExpander"] {
        border: 1px solid #BBDEFB !important;
        border-radius: 8px !important;
        background: white !important;
    }

    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        border-bottom: 2px solid #BBDEFB !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab"] {
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        color: #5C6BC0 !important;
    }
    [data-testid="stTabs"] [aria-selected="true"] {
        color: #1565C0 !important;
        border-bottom: 2px solid #1565C0 !important;
    }

    [data-testid="stRadio"] label {
        font-size: 14px !important;
        color: #1A237E !important;
    }

    </style>
    """, unsafe_allow_html=True)

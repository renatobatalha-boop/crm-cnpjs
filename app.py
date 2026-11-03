# ==========================================
# 3. IDENTIDADE VISUAL EXPO CIEE & 3D (CSS)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    header {visibility: hidden;}
    [data-testid="collapsedControl"] {display: block;}
    
    .stApp {
        background-color: #1a082e !important;
        background-image: radial-gradient(circle at 50% 0%, #321054 0%, #1a082e 100%) !important;
        color: #F8FAFC !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }

    /* Sidebar Dark CIEE */
    section[data-testid="stSidebar"] {
        background-color: #120422 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] label {
        color: #E2E8F0 !important;
    }

    /* Top Bar Executive */
    .ciee-top-bar {
        background: linear-gradient(135deg, #0E0E76 0%, #8C0073 50%, #F76D4D 100%);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 16px;
        padding: 20px 26px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 22px;
        box-shadow: 0 12px 35px rgba(0, 0, 0, 0.5), inset 0 1px 1px rgba(255, 255, 255, 0.2);
    }
    .ciee-title-wrapper {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .ciee-title {
        font-size: 22px;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #FFFFFF;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
    }
    .ciee-subtitle {
        font-size: 13px;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.9);
    }
    .ciee-badge-live {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        color: #ffffff;
        border: 1px solid rgba(255, 255, 255, 0.25);
        padding: 6px 14px;
        border-radius: 30px;
        font-size: 12px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .live-dot {
        width: 8px;
        height: 8px;
        background-color: #10B981;
        border-radius: 50%;
        box-shadow: 0 0 10px #10B981;
    }

    /* Cards KPI 3D */
    .card-kpi {
        background: rgba(35, 15, 65, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px;
        padding: 16px 18px;
        height: 125px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35), inset 0 1px 2px rgba(255, 255, 255, 0.08);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        pointer-events: none;
    }

    .border-total { 
        background: linear-gradient(135deg, #0E0E76 0%, #151552 100%) !important;
        border: 1px solid rgba(14, 14, 118, 0.5) !important;
    }
    .border-nao-contatado { 
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
        border: 1px solid rgba(148, 163, 184, 0.3) !important;
    }
    .border-contatado { 
        background: linear-gradient(135deg, #8C0073 0%, #440138 100%) !important;
        border: 1px solid rgba(140, 0, 115, 0.5) !important;
    }
    .border-futuro { 
        background: linear-gradient(135deg, #D02560 0%, #610d2b 100%) !important;
        border: 1px solid rgba(208, 37, 96, 0.5) !important;
    }
    .border-convertido { 
        background: linear-gradient(135deg, #F76D4D 0%, #7e2f1e 100%) !important;
        border: 1px solid rgba(247, 109, 77, 0.5) !important;
    }
    .border-semana { 
        background: linear-gradient(135deg, #5b137d 0%, #29083d 100%) !important;
        border: 1px solid rgba(216, 180, 254, 0.4) !important;
    }
    .border-ativo { 
        background: linear-gradient(135deg, #055e3a 0%, #022014 100%) !important;
        border: 1px solid rgba(16, 185, 129, 0.5) !important;
    }
    .border-negado { 
        background: linear-gradient(135deg, #991b1b 0%, #3f0707 100%) !important;
        border: 1px solid rgba(239, 68, 68, 0.5) !important;
    }

    .card-kpi-ativo {
        border: 2px solid #F76D4D !important;
        box-shadow: 0 0 25px rgba(247, 109, 77, 0.6), inset 0 1px 3px rgba(255, 255, 255, 0.3) !important;
        transform: translateY(-3px);
    }

    .kpi-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .kpi-title {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: rgba(255, 255, 255, 0.9);
    }
    .kpi-icon {
        font-size: 14px;
        background: rgba(255, 255, 255, 0.12);
        width: 26px;
        height: 26px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .kpi-value {
        font-size: 34px !important;
        font-weight: 800 !important;
        line-height: 1.0;
        margin: 8px 0 4px 0;
        color: #FFFFFF !important;
        text-shadow: 0 4px 12px rgba(0, 0, 0, 0.6), 0 0 10px rgba(255, 255, 255, 0.3);
    }
    .kpi-sub {
        font-size: 11px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.85);
    }

    /* Labels dos Filtros Principais */
    div[data-testid="stExpander"] label, 
    div[data-testid="stExpander"] label p, 
    div[data-testid="stExpander"] p,
    .stSelectbox label, 
    .stTextInput label, 
    .stNumberInput label {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.8) !important;
    }

    /* Filtros da Tela Principal: Expander Escuro */
    div[data-testid="stExpander"] {
        background-color: rgba(18, 4, 34, 0.9) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 16px !important;
    }
    div[data-testid="stExpander"] summary {
        background-color: transparent !important;
        color: #FFFFFF !important;
    }
    div[data-testid="stExpander"] summary:hover {
        color: #F76D4D !important;
    }
    div[data-testid="stExpander"] summary svg {
        fill: #FFFFFF !important;
    }
    div[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        background-color: transparent !important;
    }

    /* Inputs e Selects Gerais: Fundo Preto */
    div[data-baseweb="base-input"],
    div[data-baseweb="input"],
    .stTextInput > div > div,
    .stNumberInput > div > div,
    .stNumberInput [data-baseweb="input"] {
        background-color: #000000 !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        border-radius: 10px !important;
    }

    .stTextInput input,
    .stNumberInput input,
    div[data-baseweb="base-input"] input,
    div[data-baseweb="input"] input {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    .stTextInput input::placeholder {
        color: rgba(255, 255, 255, 0.45) !important;
        -webkit-text-fill-color: rgba(255, 255, 255, 0.45) !important;
    }

    .stNumberInput button {
        background-color: #0b0214 !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }

    div[data-baseweb="select"],
    div[data-baseweb="select"] > div,
    div[data-baseweb="select"] [aria-expanded] {
        background-color: #000000 !important;
        border-color: rgba(255, 255, 255, 0.25) !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
    }
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] div[value] {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    div[data-baseweb="select"] svg {
        fill: #FFFFFF !important;
    }

    /* Menu dropdown suspenso */
    ul[data-baseweb="menu"],
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div {
        background-color: #0a0114 !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    li[data-baseweb="menu-item"] {
        background-color: #0a0114 !important;
        color: #FFFFFF !important;
    }
    li[data-baseweb="menu-item"]:hover {
        background-color: #F76D4D !important;
        color: #FFFFFF !important;
    }

    /* ========================================================
       MODAL DE TRATAMENTO (@st.dialog) - TEMA ESCURO COMPLETO
       ======================================================== */
    div[role="dialog"],
    div[data-testid="stModal"] > div {
        background-color: #120422 !important;
        background-image: radial-gradient(circle at 50% 0%, #260a45 0%, #120422 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 18px !important;
    }

    div[role="dialog"] h2,
    div[role="dialog"] [data-testid="stDialogHeader"] {
        color: #FFFFFF !important;
    }
    div[role="dialog"] button[aria-label="Close"] svg {
        fill: #FFFFFF !important;
    }

    div[role="dialog"] label,
    div[role="dialog"] label p,
    div[role="dialog"] p,
    div[role="dialog"] span,
    div[role="dialog"] .stMarkdown {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    div[role="dialog"] div[data-baseweb="select"],
    div[role="dialog"] div[data-baseweb="select"] > div,
    div[role="dialog"] div[data-baseweb="select"] [aria-expanded] {
        background-color: #000000 !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
    }
    div[role="dialog"] div[data-baseweb="select"] span {
        color: #FFFFFF !important;
    }
    div[role="dialog"] div[data-baseweb="select"] svg {
        fill: #FFFFFF !important;
    }

    div[role="dialog"] div[data-baseweb="textarea"],
    div[role="dialog"] div[data-baseweb="textarea"] textarea,
    div[role="dialog"] div[data-baseweb="base-input"],
    div[role="dialog"] div[data-baseweb="input"] input {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        border-radius: 10px !important;
    }

    div[role="dialog"] textarea::placeholder,
    div[role="dialog"] input::placeholder {
        color: rgba(255, 255, 255, 0.45) !important;
        -webkit-text-fill-color: rgba(255, 255, 255, 0.45) !important;
    }

    div[role="dialog"] a[data-testid="stLinkButton"],
    div[role="dialog"] .stButton button:not([kind="primary"]) {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 10px !important;
    }

    /* Tabela de Leads */
    div[data-testid="stDataFrame"], 
    div[data-testid="stDataFrame"] > div, 
    div[data-testid="stDataFrame"] [role="grid"],
    div[data-testid="stDataFrame"] canvas {
        background-color: #1a082e !important;
        color: #FFFFFF !important;
    }

    div[data-testid="stDataFrame"] [role="columnheader"] {
        background-color: #120422 !important;
        color: #FFFFFF !important;
        border-bottom: 2px solid rgba(255, 255, 255, 0.35) !important;
    }

    div[data-testid="stDataFrame"] [role="row"],
    div[data-testid="stDataFrame"] [role="gridcell"] {
        background-color: #1a082e !important;
        color: #FFFFFF !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.2) !important;
    }

    /* Botão Laranja Principal */
    .stFormSubmitButton button, .stDownloadButton button {
        background: linear-gradient(135deg, #F76D4D 0%, #D02560 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        box-shadow: 0 6px 20px rgba(247, 109, 77, 0.35), inset 0 1px 1px rgba(255,255,255,0.3) !important;
        transition: all 0.2s ease !important;
    }
    .stFormSubmitButton button:hover, .stDownloadButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 25px rgba(247, 109, 77, 0.45) !important;
    }

    /* Camada de clique dos cards */
    div[data-testid="stHorizontalBlock"]:has(.card-kpi) .stButton {
        margin-top: -125px !important;
        height: 125px !important;
        position: relative;
        z-index: 10;
    }
    div[data-testid="stHorizontalBlock"]:has(.card-kpi) .stButton button {
        height: 125px !important;
        width: 100% !important;
        background: transparent !important;
        color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: 16px !important;
        cursor: pointer !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.card-kpi) .stButton button:hover {
        background: rgba(255, 255, 255, 0.03) !important;
    }
    </style>
""", unsafe_allow_html=True)

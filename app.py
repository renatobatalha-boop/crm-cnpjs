import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import urllib.parse
import re

# ==========================================
# 1. CONFIGURAÇÃO GERAL DA PÁGINA (DARK MODE)
# ==========================================
st.set_page_config(
    page_title="Painel Corporativo - Gestão de Leads | CIEE",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. CONEXÃO COM O BANCO DE DADOS (NEONDB)
# ==========================================
if "connections" in st.secrets and "postgresql" in st.secrets["connections"]:
    POSTGRES_URI = st.secrets["connections"]["postgresql"]["url"]
else:
    POSTGRES_URI = "postgresql+psycopg2://neondb_owner:npg_bNDxjo9L2giC@ep-empty-hall-b4zx7bew-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require"

@st.cache_resource
def get_db_engine():
    return create_engine(POSTGRES_URI, pool_pre_ping=True, pool_size=5, max_overflow=10)

try:
    engine = get_db_engine()
except Exception as e:
    st.error(f"Erro ao conectar ao banco de dados: {e}")
    st.stop()

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

    /* Labels dos Filtros da tela principal */
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

    /* Expander dos Filtros */
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

    /* Inputs de Texto e Número da tela principal (Fundo Preto) */
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

    /* Selectboxes da tela principal (Fundo Preto) */
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

    /* Menu Dropdown suspenso */
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
       MODAL DE TRATAMENTO (@st.dialog) - TEMA ESCURO E PRETO
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

    /* Botão Principal Laranja */
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

# ==========================================
# 4. FUNÇÕES DE SUPORTE E CONSTANTES
# ==========================================
def fmt_num(val):
    if val is None:
        return "0"
    return f"{int(val):,}".replace(",", ".")

def eh_celular(numero_limpo):
    if len(numero_limpo) > 11 and numero_limpo.startswith('55'):
        numero_limpo = numero_limpo[2:]
    if len(numero_limpo) >= 11:
        numero_local = numero_limpo[2:]
        if numero_local.startswith('9'):
            return True
    return False

def extrair_datas_observacoes(texto_obs):
    if not texto_obs or not isinstance(texto_obs, str):
        return []
    padrao = r'\[(\d{2}/\d{2}/\d{4})'
    datas_str = re.findall(padrao, texto_obs)
    datas_validas = []
    for d_str in datas_str:
        try:
            dt = datetime.strptime(d_str, "%d/%m/%Y")
            datas_validas.append(dt)
        except Exception:
            pass
    return datas_validas

STATUS_OFICIAIS = [
    "Lead Não Contatado",
    "Lead Contatado",
    "Contato Futuro",
    "Lead Convertido",
    "Parceiro Ativo",
    "Proposta Negada"
]

MOTIVOS_RECUSA_OPCOES = [
    "Sem orçamento para contratação",
    "Já possui instituição parceira",
    "Não deseja contratar Menor Aprendiz/Estagiário no momento",
    "Processo interno burocrático",
    "Prefere concorrente",
    "Outros"
]

LISTA_OPERADORES_OFICIAIS = [
    "AGATHA CRUZ", "ALINE CRUZ", "ANY MORIMITSU", "BARBRA COSIELLO", "BRUNO SOUZA", 
    "DIOGO VASCONCELOS", "DOUGLAS FRAGA", "ELAINE BORGES", "FABIANA LESSA MOLICA", 
    "ISABELLY NOGUEIRA", "ITALO BERTI", "JEFFERSON ANDRADE", "LUCIANA PINA", 
    "MATEUS LIMA", "MAYARA SOUZA", "RONALDO FERRAMOLA", "SANDRA MARA", 
    "TAINA ZANELLATO", "THAYNA CRUZ", "THAYNA IBRAIM", "VINICIUS RODRIGUES", 
    "VIVIANE VENAGLIA", "WILLIAM LIMA"
]

# ==========================================
# 5. CONSULTAS OTIMIZADAS COM CACHE
# ==========================================
@st.cache_data(ttl=180)
def carregar_kpis_base():
    query = """
        SELECT 
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE status_followup IS NULL 
                                OR TRIM(status_followup) = '' 
                                OR status_followup = 'Lead Não Contatado'
                                OR status_followup NOT IN ('Lead Contatado', 'Contato Futuro', 'Lead Convertido', 'Parceiro Ativo', 'Proposta Negada')) AS nao_contatados,
            COUNT(*) FILTER (WHERE status_followup = 'Lead Contatado') AS contatados,
            COUNT(*) FILTER (WHERE status_followup = 'Contato Futuro') AS futuros,
            COUNT(*) FILTER (WHERE status_followup = 'Lead Convertido') AS convertidos,
            COUNT(*) FILTER (WHERE status_followup = 'Parceiro Ativo') AS ativos,
            COUNT(*) FILTER (WHERE status_followup = 'Proposta Negada') AS negados
        FROM empresas
    """
    try:
        with engine.connect() as conn:
            row = conn.execute(text(query)).fetchone()
            return {
                "total": row.total or 0,
                "nao_contatados": row.nao_contatados or 0,
                "contatados": row.contatados or 0,
                "futuros": row.futuros or 0,
                "convertidos": row.convertidos or 0,
                "ativos": row.ativos or 0,
                "negados": row.negados or 0,
            }
    except Exception:
        return {"total": 0, "nao_contatados": 0, "contatados": 0, "futuros": 0, "convertidos": 0, "ativos": 0, "negados": 0}

@st.cache_data(ttl=300)
def calcular_contatos_semana():
    hoje = datetime.now()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    inicio_semana = inicio_semana.replace(hour=0, minute=0, second=0, microsecond=0)
    contatos = 0
    try:
        with engine.connect() as conn:
            df_obs = pd.read_sql(text("SELECT observacoes FROM empresas WHERE observacoes IS NOT NULL AND TRIM(observacoes) != ''"), conn)
            for obs in df_obs['observacoes']:
                datas = extrair_datas_observacoes(obs)
                for d in datas:
                    if d >= inicio_semana:
                        contatos += 1
    except Exception:
        contatos = 0
    return contatos

@st.cache_data(ttl=60)
def get_responsaveis_cadastrados():
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text("""
                SELECT DISTINCT responsavel_tratamento 
                FROM empresas 
                WHERE responsavel_tratamento IS NOT NULL 
                  AND TRIM(responsavel_tratamento) != ''
            """), conn)
            banco_lista = df["responsavel_tratamento"].dropna().tolist()
            return ["Todos", "Sem Responsável"] + sorted(list(set(banco_lista + LISTA_OPERADORES_OFICIAIS)))
    except Exception:
        return ["Todos", "Sem Responsável"] + LISTA_OPERADORES_OFICIAIS

lista_responsaveis_filtro = get_responsaveis_cadastrados()

# ==========================================
# 6. MENU LATERAL (NAVEGAÇÃO)
# ==========================================
with st.sidebar:
    st.markdown("""
        <div style="padding: 10px 0 20px 0; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 18px;">
            <div style="font-size: 20px; font-weight: 800; color: #FFFFFF; display: flex; align-items: center; gap: 10px;">
                <span>🏛️</span> <span>CIEE B2B CRM</span>
            </div>
            <div style="font-size: 11px; color: #cbd5e1; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-top: 4px;">São Paulo • Prospecção</div>
        </div>
    """, unsafe_allow_html=True)

    aba_selecionada = st.radio(
        "Navegue pelo Painel:",
        ["🔍 Prospecção de Leads", "📊 Gestão e Produtividade CIEE"],
        index=0
    )

    st.markdown("<hr style='margin: 20px 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    st.markdown("##### 👤 Operador Autenticado")
    
    operador_logado = st.selectbox(
        "Sessão ativa como:",
        options=LISTA_OPERADORES_OFICIAIS,
        index=1  # Default: ALINE CRUZ
    )
    st.session_state["usuario_ativo"] = operador_logado

    st.markdown(f"""
        <div style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-left: 4px solid #F76D4D; border-radius: 10px; padding: 12px; margin-top: 15px;">
            <div style="font-size: 10px; color: rgba(255,255,255,0.5); text-transform: uppercase; font-weight: 700;">Status Operacional</div>
            <div style="font-size: 13px; color: #FFFFFF; font-weight: 800; margin-top: 2px;">{st.session_state['usuario_ativo']}</div>
        </div>
    """, unsafe_allow_html=True)

# Cabeçalho Principal (Paleta CIEE)
st.markdown(f"""
    <div class="ciee-top-bar">
        <div class="ciee-title-wrapper">
            <div class="ciee-title">🏛️ CENTRAL INTELIGENTE DE PROSPECÇÃO</div>
            <div class="ciee-subtitle">Gestão Ativa de Prospecção de CNPJs • CIEE São Paulo</div>
        </div>
        <div class="ciee-badge-live">
            <span class="live-dot"></span>
            <span>Operador: <b>{st.session_state['usuario_ativo']}</b></span>
        </div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# ABA 1: PROSPECÇÃO DE LEADS
# ==========================================
if aba_selecionada == "🔍 Prospecção de Leads":
    if "filtro_status_clique" not in st.session_state:
        st.session_state["filtro_status_clique"] = "Todos"

    kpis = carregar_kpis_base()
    total_cnpjs = kpis["total"]
    qtd_nao_contatados = kpis["nao_contatados"]
    qtd_contatados = kpis["contatados"]
    qtd_futuros = kpis["futuros"]
    qtd_convertidos = kpis["convertidos"]
    qtd_ativos = kpis["ativos"]
    qtd_negados = kpis["negados"]

    pct = lambda val: (val / total_cnpjs * 100) if total_cnpjs > 0 else 0.0
    status_atual = st.session_state["filtro_status_clique"]

    contatos_esta_semana = calcular_contatos_semana()

    # DASHBOARD DE MÉTRICAS (8 CARDS)
    c_t, c_nc, c_c, c_cf, c_conv, c_sem, c_pa, c_pn = st.columns(8)
    
    with c_t:
        cls_ativo = "card-kpi-ativo" if status_atual == "Todos" else ""
        st.markdown(f'''
            <div class="card-kpi border-total {cls_ativo}">
                <div class="kpi-header"><span class="kpi-title">Total Base</span><span class="kpi-icon">🏛️</span></div>
                <div class="kpi-value">{fmt_num(total_cnpjs)}</div>
                <div class="kpi-sub">100% da base</div>
            </div>
        ''', unsafe_allow_html=True)
        if st.button(" ", key="card_todos", use_container_width=True):
            st.session_state["filtro_status_clique"] = "Todos"
            st.rerun()

    with c_nc:
        cls_ativo = "card-kpi-ativo" if status_atual == "Lead Não Contatado" else ""
        st.markdown(f'''
            <div class="card-kpi border-nao-contatado {cls_ativo}">
                <div class="kpi-header"><span class="kpi-title">Não Contatados</span><span class="kpi-icon">⏳</span></div>
                <div class="kpi-value">{fmt_num(qtd_nao_contatados)}</div>
                <div class="kpi-sub">{pct(qtd_nao_contatados):.1f}% da base</div>
            </div>
        ''', unsafe_allow_html=True)
        if st.button(" ", key="card_nc", use_container_width=True):
            st.session_state["filtro_status_clique"] = "Lead Não Contatado"
            st.rerun()

    with c_c:
        cls_ativo = "card-kpi-ativo" if status_atual == "Lead Contatado" else ""
        st.markdown(f'''
            <div class="card-kpi border-contatado {cls_ativo}">
                <div class="kpi-header"><span class="kpi-title">Contatados</span><span class="kpi-icon">📞</span></div>
                <div class="kpi-value">{fmt_num(qtd_contatados)}</div>
                <div class="kpi-sub">{pct(qtd_contatados):.1f}% da base</div>
            </div>
        ''', unsafe_allow_html=True)
        if st.button(" ", key="card_c", use_container_width=True):
            st.session_state["filtro_status_clique"] = "Lead Contatado"
            st.rerun()

    with c_cf:
        cls_ativo = "card-kpi-ativo" if status_atual == "Contato Futuro" else ""
        st.markdown(f'''
            <div class="card-kpi border-futuro {cls_ativo}">
                <div class="kpi-header"><span class="kpi-title">Contato Futuro</span><span class="kpi-icon">📅</span></div>
                <div class="kpi-value">{fmt_num(qtd_futuros)}</div>
                <div class="kpi-sub">{pct(qtd_futuros):.1f}% da base</div>
            </div>
        ''', unsafe_allow_html=True)
        if st.button(" ", key="card_cf", use_container_width=True):
            st.session_state["filtro_status_clique"] = "Contato Futuro"
            st.rerun()

    with c_conv:
        cls_ativo = "card-kpi-ativo" if status_atual == "Lead Convertido" else ""
        st.markdown(f'''
            <div class="card-kpi border-convertido {cls_ativo}">
                <div class="kpi-header"><span class="kpi-title">Convertidos</span><span class="kpi-icon">🚀</span></div>
                <div class="kpi-value">{fmt_num(qtd_convertidos)}</div>
                <div class="kpi-sub">{pct(qtd_convertidos):.1f}% da base</div>
            </div>
        ''', unsafe_allow_html=True)
        if st.button(" ", key="card_conv", use_container_width=True):
            st.session_state["filtro_status_clique"] = "Lead Convertido"
            st.rerun()

    with c_sem:
        st.markdown(f'''
            <div class="card-kpi border-semana">
                <div class="kpi-header"><span class="kpi-title">Nesta Semana</span><span class="kpi-icon">⚡</span></div>
                <div class="kpi-value" style="color: #E9D5FF !important;">{fmt_num(contatos_esta_semana)}</div>
                <div class="kpi-sub">Contatos realizados</div>
            </div>
        ''', unsafe_allow_html=True)

    with c_pa:
        cls_ativo = "card-kpi-ativo" if status_atual == "Parceiro Ativo" else ""
        st.markdown(f'''
            <div class="card-kpi border-ativo {cls_ativo}">
                <div class="kpi-header"><span class="kpi-title">Parceiro Ativo</span><span class="kpi-icon">🤝</span></div>
                <div class="kpi-value">{fmt_num(qtd_ativos)}</div>
                <div class="kpi-sub">{pct(qtd_ativos):.1f}% da base</div>
            </div>
        ''', unsafe_allow_html=True)
        if st.button(" ", key="card_pa", use_container_width=True):
            st.session_state["filtro_status_clique"] = "Parceiro Ativo"
            st.rerun()

    with c_pn:
        cls_ativo = "card-kpi-ativo" if status_atual == "Proposta Negada" else ""
        st.markdown(f'''
            <div class="card-kpi border-negado {cls_ativo}">
                <div class="kpi-header"><span class="kpi-title">Prop. Negada</span><span class="kpi-icon">✖️</span></div>
                <div class="kpi-value">{fmt_num(qtd_negados)}</div>
                <div class="kpi-sub">{pct(qtd_negados):.1f}% da base</div>
            </div>
        ''', unsafe_allow_html=True)
        if st.button(" ", key="card_pn", use_container_width=True):
            st.session_state["filtro_status_clique"] = "Proposta Negada"
            st.rerun()

    st.caption("👆 **Interatividade:** Selecione qualquer card de métrica para filtrar os registros instantaneamente.")

    # ==========================================
    # FILTROS DE BUSCA (COM CEP INCLUÍDO)
    # ==========================================
    with st.expander("🎛️ FILTROS AVANÇADOS DE SELEÇÃO & PERÍODO SEMANAL", expanded=True):
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1:
            opcoes_status = ["Todos"] + STATUS_OFICIAIS
            idx_status_sel = opcoes_status.index(st.session_state["filtro_status_clique"]) if st.session_state["filtro_status_clique"] in opcoes_status else 0
            filtro_status_sel = st.selectbox("Status de Prospecção:", opcoes_status, index=idx_status_sel)
            if filtro_status_sel != st.session_state["filtro_status_clique"]:
                st.session_state["filtro_status_clique"] = filtro_status_sel
                st.rerun()
        with col_f2:
            filtro_responsavel_sel = st.selectbox("Responsável pelo Lead:", lista_responsaveis_filtro, index=0)
        with col_f3:
            lista_portes = ["Todos", "Micro Empresa (ME)", "Empresa de Pequeno Porte (EPP)", "Demais (Médio/Grande Porte)", "Não Informado"]
            filtro_porte_sel = st.selectbox("Porte da Empresa:", lista_portes, index=0)
        with col_f4:
            filtro_semana_sel = st.selectbox(
                "📅 Filtro de Contatos por Período:",
                ["Qualquer Período", "Contatados Esta Semana", "Contatados nos Últimos 14 Dias", "Contatados no Último Mês"],
                index=0
            )

        col_f5, col_f6, col_f7, col_f8, col_f9 = st.columns(5)
        with col_f5:
            filtro_segmentacao_sel = st.selectbox("Segmentação de Atuação:", ["Todos", "Varejo", "Outros Serviços"], index=0)
        with col_f6:
            filtro_setor_tipo_sel = st.selectbox("Tipo de Setor:", ["Todos", "Público", "Privado"], index=0)
        with col_f7:
            busca_bairro = st.text_input("Bairro ou Região:", placeholder="Ex: Centro, Pinheiros...")
        with col_f8:
            busca_cep = st.text_input("CEP:", placeholder="Ex: 01310 ou 01310-100")
        with col_f9:
            busca_texto = st.text_input("Razão Social ou CNPJ:", placeholder="Digite nome ou números...")

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            registros_por_pagina = st.selectbox("Registros por Página:", [50, 100, 250, 500], index=1)
        with col_p2:
            pagina_atual = st.number_input("Página Atual:", min_value=1, value=1, step=1)

    offset_val = (pagina_atual - 1) * registros_por_pagina

    # Montagem Dinâmica de WHERE SQL
    where_clauses = ["1=1"]
    params = {}

    if filtro_status_sel != "Todos":
        if filtro_status_sel == "Lead Não Contatado":
            where_clauses.append("""
                (status_followup IS NULL 
                 OR TRIM(status_followup) = '' 
                 OR status_followup = 'Lead Não Contatado'
                 OR status_followup NOT IN ('Lead Contatado', 'Contato Futuro', 'Lead Convertido', 'Parceiro Ativo', 'Proposta Negada'))
            """)
        else:
            where_clauses.append("status_followup = :stat")
            params["stat"] = filtro_status_sel

    if filtro_responsavel_sel != "Todos":
        if filtro_responsavel_sel == "Sem Responsável":
            where_clauses.append("(responsavel_tratamento IS NULL OR TRIM(responsavel_tratamento) = '')")
        else:
            where_clauses.append("responsavel_tratamento = :resp")
            params["resp"] = filtro_responsavel_sel

    if filtro_porte_sel != "Todos":
        where_clauses.append("porte_empresa = :porte")
        params["porte"] = filtro_porte_sel

    if busca_bairro.strip():
        where_clauses.append("bairro ILIKE :bairro")
        params["bairro"] = f"%{busca_bairro.strip()}%"

    if busca_cep.strip():
        cep_limpo = re.sub(r'\D', '', busca_cep.strip())
        where_clauses.append("REPLACE(REPLACE(cep, '-', ''), '.', '') LIKE :cep")
        params["cep"] = f"{cep_limpo}%"

    if busca_texto.strip():
        where_clauses.append("(razao_social ILIKE :txt OR cnpj_formatado LIKE :txt)")
        params["txt"] = f"%{busca_texto.strip()}%"

    if filtro_segmentacao_sel != "Todos":
        varejo_cond = "(razao_social ILIKE '%comercio%' OR razao_social ILIKE '%varejo%' OR nome_fantasia ILIKE '%loja%' OR nome_fantasia ILIKE '%supermercado%')"
        if filtro_segmentacao_sel == "Varejo":
            where_clauses.append(varejo_cond)
        else:
            where_clauses.append(f"NOT {varejo_cond}")

    if filtro_setor_tipo_sel != "Todos":
        if filtro_setor_tipo_sel == "Público":
            where_clauses.append("(razao_social ILIKE '%publica%' OR razao_social ILIKE '%prefeitura%' OR razao_social ILIKE '%municip%' OR razao_social ILIKE '%federal%')")
        else:
            where_clauses.append("NOT (razao_social ILIKE '%publica%' OR razao_social ILIKE '%prefeitura%' OR razao_social ILIKE '%municip%' OR razao_social ILIKE '%federal%')")

    sql_where = " WHERE " + " AND ".join(where_clauses)
    query_count = f"SELECT COUNT(*) as total FROM empresas {sql_where}"
    try:
        with engine.connect() as conn:
            total_filtrado = conn.execute(text(query_count), params).fetchone().total or 0
    except Exception:
        total_filtrado = 0

    # ==========================================
    # MODAL DE TRATAMENTO DE LEADS (POP-UP)
    # ==========================================
    @st.dialog("📝 Ficha do Lead & Histórico de Interação", width="large")
    def abrir_modal_tratamento(cnpj):
        query_emp = "SELECT * FROM empresas WHERE cnpj_formatado = :cnpj"
        res_df = pd.read_sql(text(query_emp), engine, params={"cnpj": cnpj})
        
        if res_df.empty:
            st.error("Empresa não localizada no banco de dados.")
            return
        row = res_df.iloc[0]
        cnpj_completo_exibicao = row.get('cnpj_formatado', 'Não Informado')
        
        ddd = str(row.get('ddd1', '')).replace('.0', '').strip()
        tel = str(row.get('telefone1', '')).replace('.0', '').strip()
        tel_fmt = f"({ddd}) {tel}" if ddd and tel and ddd not in ['nan', 'None'] else (tel or "Não informado")
        email_fmt = row.get('correio_eletronico') or "Não informado"
        
        nome_fantasia_val = str(row.get('nome_fantasia', '')).strip()
        nome_exibicao = nome_fantasia_val if nome_fantasia_val and nome_fantasia_val not in ['nan', 'None', ''] else row.get('razao_social', '-')
        logradouro = str(row.get("logradouro") or "").strip()
        numero = str(row.get("numero") or "").strip()
        bairro = str(row.get("bairro") or "").strip()
        cep = str(row.get("cep") or "").strip()
        endereco_comple

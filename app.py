import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import urllib.parse

# ==========================================
# 1. CONFIGURAÇÃO GERAL DA PÁGINA (DARK MODE ATIVO)
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
# 3. IDENTIDADE VISUAL EXPO CIEE (CSS COMPLETO E DEFINITIVO)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    header {visibility: hidden;}
    [data-testid="collapsedControl"] {display: block;}
    
    /* Fundo roxo ligeiramente mais claro e vibrante para fluidez */
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

    /* Top Bar Executive (CIEE Colors) */
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
        -webkit-backdrop-filter: blur(10px);
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

    /* Cards KPI baseados nas cores solicitadas com Efeito 3D */
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

    /* Gradientes utilizando especificamente sua paleta */
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
    .border-ativo { 
        background: linear-gradient(135deg, #055e3a 0%, #022014 100%) !important;
        border: 1px solid rgba(16, 185, 129, 0.5) !important;
    }
    .border-negado { 
        background: linear-gradient(135deg, #991b1b 0%, #3f0707 100%) !important;
        border: 1px solid rgba(239, 68, 68, 0.5) !important;
    }

    /* Card Selecionado com Borda Iluminada Laranja */
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
        color: rgba(255, 255, 255, 0.85);
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
    
    /* EVIDENCIANDO NÚMEROS: Fonte aumentada para 34px, em negrito e com sombra proeminente */
    .kpi-value {
        font-size: 34px !important;
        font-weight: 800 !important;
        line-height: 1.0;
        margin: 8px 0 4px 0;
        color: #FFFFFF !important;
        text-shadow: 0 4px 12px rgba(0, 0, 0, 0.5), 0 0 8px rgba(255, 255, 255, 0.2);
    }
    .kpi-sub {
        font-size: 11px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.7);
    }

    /* Containers de Filtro em Glassmorphism Escuro */
    div[data-testid="stExpander"], .section-header-bar {
        background-color: rgba(25, 12, 45, 0.75) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3) !important;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
    }

    /* Inputs Dark Customizados */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: rgba(12, 5, 25, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
    }

    /* BOTÃO LARANJA PREMIUM DA PALETA */
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

    /* =======================================================
       CORREÇÃO DEFINITIVA DO FUNDO DA TABELA (GLIDE DATA GRID)
       ======================================================= */
    /* Força todas as áreas internas do grid do Streamlit a serem pretas/roxo escuro */
    div[data-testid="stDataFrame"] iframe,
    div[data-testid="stDataFrame"] > div,
    div[data-testid="stDataFrame"] [data-testid="StyledFullScreenButton"]+div,
    div[data-testid="stDataFrame"] [role="grid"],
    div[data-testid="stDataFrame"] canvas {
        background-color: #120422 !important;
        color-scheme: dark !important; /* Força o componente a herdar as cores escuras nativas */
    }

    /* Força o container do widget a ocultar qualquer elemento de fundo branco residual */
    div[data-testid="stDataFrame"] {
        background-color: #120422 !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important;
    }

    /* Camada para clique nos cards KPI */
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
# 5. MENU LATERAL (NAVEGAÇÃO)
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

# ==========================================
# 6. LISTA DE RESPONSÁVEIS
# ==========================================
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

# Cabeçalho Principal (Paleta de cores integrada)
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

    # Consulta dos KPIs Gerais
    query_kpis_geral = """
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
            kpi_res = conn.execute(text(query_kpis_geral)).fetchone()
        total_cnpjs = kpi_res.total or 0
        qtd_nao_contatados = kpi_res.nao_contatados or 0
        qtd_contatados = kpi_res.contatados or 0
        qtd_futuros = kpi_res.futuros or 0
        qtd_convertidos = kpi_res.convertidos or 0
        qtd_ativos = kpi_res.ativos or 0
        qtd_negados = kpi_res.negados or 0
    except Exception:
        total_cnpjs = qtd_nao_contatados = qtd_contatados = qtd_futuros = qtd_convertidos = qtd_ativos = qtd_negados = 0

    pct = lambda val: (val / total_cnpjs * 100) if total_cnpjs > 0 else 0.0
    status_atual = st.session_state["filtro_status_clique"]

    # ==========================================
    # DASHBOARD DE MÉTRICAS 3D (COM NÚMEROS DESTACADOS)
    # ==========================================
    c_t, c_nc, c_c, c_cf, c_conv, c_pa, c_pn = st.columns(7)
    
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
    # FILTROS DE BUSCA (NEON GLASS DESIGN)
    # ==========================================
    with st.expander("🎛️ FILTROS AVANÇADOS DE SELEÇÃO", expanded=True):
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
            busca_cep = st.text_input("CEP da Empresa:", placeholder="Ex: 01310-100")

        col_f5, col_f6, col_f7, col_f8 = st.columns(4)
        with col_f5:
            filtro_segmentacao_sel = st.selectbox("Segmentação de Atuação:", ["Todos", "Varejo", "Outros Serviços"], index=0)
        with col_f6:
            filtro_setor_tipo_sel = st.selectbox("Tipo de Setor:", ["Todos", "Público", "Privado"], index=0)
        with col_f7:
            busca_bairro = st.text_input("Bairro ou Região:", placeholder="Ex: Centro, Pinheiros...")
        with col_f8:
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

    if busca_cep.strip():
        where_clauses.append("cep LIKE :cep")
        params["cep"] = f"%{busca_cep.strip()}%"

    if busca_bairro.strip():
        where_clauses.append("bairro ILIKE :bairro")
        params["bairro"] = f"%{busca_bairro.strip()}%"

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
    # MODAL DE TRATAMENTO DE LEADS
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
        endereco_completo = f"{logradouro}, {numero} - {bairro}, São Paulo - SP, {cep}".strip(", -")
        query_maps = urllib.parse.quote(endereco_completo)
        maps_link = f"https://www.google.com/maps/search/?api=1&query={query_maps}"

        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #180933 0%, #0c021c 100%); border: 1px solid rgba(255,255,255,0.15); border-left: 5px solid #F76D4D; border-radius: 12px; padding: 20px; margin-bottom: 18px; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <div style="font-size: 19px; font-weight: 800; color: #FFFFFF;">🏢 {nome_exibicao}</div>
                    <code style="background-color: rgba(247, 109, 77, 0.15); color: #F76D4D; font-weight: 700; padding: 4px 10px; border-radius: 6px; font-size: 12px; border: 1px solid rgba(247, 109, 77, 0.3);">CNPJ: {cnpj_completo_exibicao}</code>
                </div>
                <div style="font-size: 13px; color: #e2e8f0; display: grid; grid-template-columns: 1fr 1fr; gap: 12px; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 12px;">
                    <div><span style="color: #94a3b8; font-weight: 600;">Razão Social:</span><br><b>{row.get('razao_social', '-')}</b></div>
                    <div><span style="color: #94a3b8; font-weight: 600;">Porte Empresarial:</span><br><b>{row.get('porte_empresa', 'Não Informado')}</b></div>
                    <div><span style="color: #94a3b8; font-weight: 600;">Telefone de Contato:</span><br><b>📞 {tel_fmt}</b></div>
                    <div><span style="color: #94a3b8; font-weight: 600;">E-mail Cadastrado:</span><br><b>✉️ {email_fmt}</b></div>
                    <div style="grid-column: span 2;"><span style="color: #94a3b8; font-weight: 600;">Endereço Completo:</span><br><b>📍 {endereco_completo}</b></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        col_acao1, col_acao2 = st.columns(2)
        with col_acao1:
            st.link_button("📍 Ver Rota Google Maps", maps_link, use_container_width=True)
        with col_acao2:
            clean_tel = "".join(filter(str.isdigit, tel_fmt))
            if clean_tel and eh_celular(clean_tel):
                msg_whats = urllib.parse.quote(f"Olá! Sou {st.session_state['usuario_ativo']} do CIEE e gostaria de falar com o responsável de RH da {nome_exibicao} sobre programas de Estágio e Aprendizagem.")
                st.link_button("💬 Chamar no WhatsApp Web", f"https://wa.me/55{clean_tel}?text={msg_whats}", use_container_width=True)
            else:
                st.button("☎️ Contato Fixo (WhatsApp)", disabled=True, use_container_width=True)

        st.markdown("<hr style='margin: 18px 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        st.markdown("##### ⚙️ Atualização do Follow-up")
        
        status_banco = row.get('status_followup', '')
        idx_status = STATUS_OFICIAIS.index(status_banco) if status_banco in STATUS_OFICIAIS else 0
        col_st, col_rp = st.columns(2)
        with col_st:
            status_selecionado = st.selectbox("📌 Status de Evolução:", options=STATUS_OFICIAIS, index=idx_status, key=f"status_select\_{cnpj}")
        with col_rp:
            resp_banco = row.get('responsavel_tratamento', '') or ''
            idx_operador_atual = 0
            if resp_banco in LISTA_OPERADORES_OFICIAIS:
                idx_operador_atual = LISTA_OPERADORES_OFICIAIS.index(resp_banco)
            elif st.session_state["usuario_ativo"] in LISTA_OPERADORES_OFICIAIS:
                idx_operador_atual = LISTA_OPERADORES_OFICIAIS.index(st.session_state["usuario_ativo"])
                
            novo_resp_selecionado = st.selectbox(
                "👤 Atribuir Responsável:",
                options=LISTA_OPERADORES_OFICIAIS,
                index=idx_operador_atual,
                key=f"resp_select\_{cnpj}"
            )

        ticket_conversao = ""
        if status_selecionado == "Lead Convertido":
            ticket_conversao = st.text_input("🎟️ Protocolo / Ticket CIEE:", placeholder="Ex: CIEE-SP-12345", key=f"ticket\_{cnpj}")
        motivo_recusa_sel = ""
        if status_selecionado == "Proposta Negada":
            motivo_recusa_sel = st.selectbox("❌ Principal Motivo da Recusa:", MOTIVOS_RECUSA_OPCOES, key=f"recusa\_{cnpj}")

        st.markdown("📜 **Histórico de Interações:**")
        obs_banco = row.get('observacoes', '') or ''
        if obs_banco:
            st.info(obs_banco)
        else:
            st.caption("Sem interações salvas.")

        with st.form(f"form_tratamento\_{cnpj}"):
            nova_nota = st.text_area(
                "✍️ Registrar Detalhes de Nova Interação:",
                placeholder="Anotar resumo de ligação, retorno, decisor contactado...",
                height=90
            )
            
            is_admin = str(st.session_state["usuario_ativo"]).strip().upper() == "ALINE CRUZ"
            if is_admin:
                obs_manual_expander = st.expander("🔧 Editar histórico completo (Administrador)")
                with obs_manual_expander:
                    obs_manual = st.text_area("Histórico Bruto:", value=obs_banco, height=80)
            else:
                obs_manual = obs_banco
            btn_salvar = st.form_submit_button("💾 Salvar Tratamento", use_container_width=True)
            
            if btn_salvar:
                base_obs = obs_manual.strip() if is_admin else obs_banco.strip()
                if nova_nota.strip():
                    carimbo_tempo = datetime.now().strftime("%d/%m/%Y %H:%M")
                    autor = novo_resp_selecionado or st.session_state["usuario_ativo"]
                    novo_bloco = f"[{carimbo_tempo} - {autor}]: {nova_nota.strip()}"
                    base_obs = f"{novo_bloco}\\n{base_obs}".strip() if base_obs else novo_bloco
                obs_final = base_obs
                if status_selecionado == "Lead Convertido" and ticket_conversao.strip():
                    registro_ticket = f"[TICKET: {ticket_conversao.strip()}]"
                    if registro_ticket not in obs_final:
                        obs_final = f"{registro_ticket} {obs_final}".strip()
                if status_selecionado == "Proposta Negada" and motivo_recusa_sel:
                    registro_recusa = f"[MOTIVO NEGADO: {motivo_recusa_sel}]"
                    if registro_recusa not in obs_final:
                        obs_final = f"{registro_recusa} {obs_final}".strip()
                try:
                    with engine.begin() as conn:
                        conn.execute(text("""
                            UPDATE empresas 
                            SET responsavel_tratamento = :resp,
                                status_followup = :stat,
                                observacoes = :obs
                            WHERE cnpj_formatado = :cnpj
                        """), {
                            "resp": novo_resp_selecionado,
                            "stat": status_selecionado,
                            "obs": obs_final,
                            "cnpj": cnpj
                        })
                    st.cache_data.clear()
                    st.success("✅ Lead atualizado com sucesso!")
                    st.rerun()
                except Exception as err:
                    st.error(f"Erro ao salvar: {err}")

    # ==========================================
    # TABELA PRINCIPAL DE EMPRESAS (RELAÇÃO EM MODO ESCURO)
    # ==========================================
    query_dados = f"""
        SELECT 
            cnpj_formatado, razao_social, nome_fantasia, porte_empresa,
            CASE 
                WHEN razao_social ILIKE '%comercio%' OR razao_social ILIKE '%varejo%' OR nome_fantasia ILIKE '%loja%' OR nome_fantasia ILIKE '%supermercado%' THEN 'Varejo'
                ELSE 'Outros Serviços'
            END AS segmentacao,
            CASE 
                WHEN razao_social ILIKE '%publica%' OR razao_social ILIKE '%prefeitura%' OR razao_social ILIKE '%municip%' OR razao_social ILIKE '%federal%' THEN 'Público'
                ELSE 'Privado'
            END AS setor_tipo,
            COALESCE(bairro, 'Não Informado') AS bairro, cep
        FROM empresas {sql_where}
        ORDER BY 
            CASE WHEN (razao_social ILIKE '%comercio%' OR razao_social ILIKE '%varejo%' OR nome_fantasia ILIKE '%loja%') THEN 0 ELSE 1 END,
            cnpj_formatado
        LIMIT {registros_por_pagina} OFFSET {offset_val}
    """
    df_tabela = pd.read_sql(text(query_dados), engine, params=params)

    # Titulo e Botão de Exportação Alinhados
    col_titulo_tab, col_export = st.columns([3, 2])
    with col_titulo_tab:
        status_indicador = f" • Filtro ativo: [{filtro_status_sel}]" if filtro_status_sel != "Todos" else ""
        st.markdown(f"#### 📋 Relação de Prospecção ({fmt_num(total_filtrado)} CNPJs{status_indicador})")
    with col_export:
        if not df_tabela.empty:
            csv_data = df_tabela.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="📥 Exportar Dados Atuais (CSV)",
                data=csv_data,
                file_name=f"base_empresas_ciee_pag\_{pagina_atual}.csv",
                mime="text/csv",
                use_container_width=True
            )

    if df_tabela.empty:
        st.info("Nenhum CNPJ localizado com os filtros selecionados.")
    else:
        st.caption("👉 **Ação:** Toque em qualquer linha da tabela para abrir o modal do lead e registrar follow-ups.")
        
        event = st.dataframe(
            df_tabela[[
                'cnpj_formatado', 'razao_social', 'nome_fantasia', 'porte_empresa',
                'segmentacao', 'setor_tipo', 'bairro', 'cep'
            ]],
            column_config={
                "cnpj_formatado": "CNPJ",
                "razao_social": "Razão Social",
                "nome_fantasia": "Nome Fantasia",
                "porte_empresa": "Porte",
                "segmentacao": "Segmentação",
                "setor_tipo": "Tipo de Setor",
                "bairro": "Bairro",
                "cep": "CEP"
            },
            hide_index=True,
            use_container_width=True,
            on_select="rerun",
            selection_mode="single-row",
            key="tabela_leads"
        )
        
        if event and event.selection and event.selection.rows:
            idx_selecionado = event.selection.rows[0]
            cnpj_clicado = df_tabela.iloc[idx_selecionado]['cnpj_formatado']
            abrir_modal_tratamento(cnpj_clicado)

        total_paginas = (total_filtrado // registros_por_pagina) + (1 if total_filtrado % registros_por_pagina > 0 else 0)
        st.caption(f"Página **{pagina_atual}** de **{fmt_num(total_paginas)}** • Exibindo **{len(df_tabela)}** de **{fmt_num(total_filtrado)}** registros.")

# ==========================================
# ABA 2: GESTÃO E PRODUTIVIDADE CIEE
# ==========================================
else:
    st.markdown("### 📊 Indicadores Comerciais & Produtividade")
    st.markdown("---")
    query_gestao = """
        SELECT 
            COALESCE(NULLIF(TRIM(responsavel_tratamento), ''), 'Não Atribuído') AS "Responsável",
            status_followup,
            observacoes,
            COUNT(*) AS total
        FROM empresas
        GROUP BY 1, 2, 3
    """
    try:
        df_gestao = pd.read_sql(text(query_gestao), engine)
    except Exception:
        df_gestao = pd.DataFrame()

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("#### 🏆 Ranking de Conversões por Consultor")
        if not df_gestao.empty:
            df_ranking = df_gestao.groupby("Responsável").agg(
                Total_Leads_Trabalhados=("total", "sum"),
                Conversoes_Efetivas=("total", lambda x: sum(df_gestao.loc[x.index, "total"][df_gestao.loc[x.index, "status_followup"].isin(["Lead Convertido", "Parceiro Ativo"])]))
            ).reset_index().sort_values(by="Conversoes_Efetivas", ascending=False)
            
            st.dataframe(df_ranking, hide_index=True, use_container_width=True)
        else:
            st.info("Nenhum indicador disponível.")

    with col_g2:
        st.markdown("#### ❌ Principais Motivos de Recusa")
        motivos_contagem = {motivo: 0 for motivo in MOTIVOS_RECUSA_OPCOES}
        
        if not df_gestao.empty:
            for _, r in df_gestao.iterrows():
                obs = str(r['observacoes'])
                for motivo in MOTIVOS_RECUSA_OPCOES:
                    if motivo in obs:
                        motivos_contagem[motivo] += r['total']
        
        df_recusas = pd.DataFrame(list(motivos_contagem.items()), columns=["Motivo", "Quantidade"]).sort_values(by="Quantidade", ascending=False)
        
        if df_recusas["Quantidade"].sum() > 0:
            st.bar_chart(df_recusas.set_index("Motivo"), color="#D02560")
        else:
            st.caption("Sem dados de recusa informados.")

    st.markdown("---")
    st.markdown("#### 📈 Fluxo e Distribuição Geral de Atendimentos")
    query_total_status = "SELECT status_followup, COUNT(*) as qtd FROM empresas WHERE status_followup IS NOT NULL GROUP BY 1"
    try:
        df_status = pd.read_sql(text(query_total_status), engine)
        if not df_status.empty:
            st.bar_chart(df_status.set_index("status_followup"), color="#F76D4D")
        else:
            st.caption("Nenhuma interação cadastrada.")
    except Exception:
        st.caption("Carregando gráficos...")



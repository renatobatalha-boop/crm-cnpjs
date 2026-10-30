import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import urllib.parse

# ==========================================
# 1. CONFIGURAÇÃO GERAL DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Painel Corporativo - Gestão de Leads | CIEE",
    page_icon="🏛️",
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
# 3. DESIGN SYSTEM APPS SCRIPT / TAILWIND CIEE (CSS)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    header {visibility: hidden;}
    [data-testid="collapsedControl"] {display: block;}
    
    .stApp {
        background: radial-gradient(circle at top left, #F8FAFC 0%, #EFF4FB 100%) !important;
        color: #0F172A !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
        max-width: 100% !important;
    }

    /* Sidebar Estilo Web App */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1E004A 0%, #31006F 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    section[data-testid="stSidebar"] * {
        color: #F8FAFC !important;
    }
    section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
        background-color: rgba(255, 255, 255, 0.12) !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
    }

    /* Hero Banner Superior */
    .ciee-hero {
        background: linear-gradient(120deg, #240054 0%, #4A0E8F 50%, #005CB9 100%);
        border-radius: 16px;
        padding: 18px 26px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 16px;
        box-shadow: 0 10px 25px -5px rgba(49, 0, 111, 0.28);
        border-bottom: 3px solid #FF5F00;
        color: #ffffff;
    }
    .ciee-hero-left {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .ciee-hero-icon {
        width: 46px;
        height: 46px;
        background: rgba(255, 95, 0, 0.2);
        border: 1px solid rgba(255, 95, 0, 0.5);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
    }
    .ciee-hero-title {
        font-size: 20px;
        font-weight: 800;
        letter-spacing: -0.4px;
        margin: 0;
        line-height: 1.2;
    }
    .ciee-hero-sub {
        font-size: 12.5px;
        color: #E2E8F0;
        font-weight: 400;
        margin-top: 2px;
    }
    .ciee-badge-live {
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(8px);
        color: #ffffff;
        border: 1px solid rgba(255, 255, 255, 0.25);
        padding: 6px 14px;
        border-radius: 999px;
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

    /* Cards KPI Estilo Apps Script */
    .card-kpi {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 12px 14px;
        height: 108px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        position: relative;
        overflow: hidden;
        pointer-events: none;
        transition: all 0.2s ease;
    }
    .card-kpi-ativo {
        background: linear-gradient(180deg, #FFFFFF 0%, #FFF7ED 100%);
        border: 2px solid #FF5F00 !important;
        box-shadow: 0 8px 20px rgba(255, 95, 0, 0.18);
    }
    .kpi-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .kpi-title {
        font-size: 10.5px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #64748B;
    }
    .kpi-icon-pill {
        width: 24px;
        height: 24px;
        border-radius: 7px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
    }
    .kpi-value {
        font-size: 21px;
        font-weight: 900;
        letter-spacing: -0.6px;
        line-height: 1.1;
        color: #0F172A;
    }
    .kpi-footer {
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 10.5px;
        font-weight: 600;
    }
    .kpi-progress-bg {
        width: 100%;
        height: 4px;
        background-color: #F1F5F9;
        border-radius: 99px;
        margin-top: 4px;
        overflow: hidden;
    }
    .kpi-progress-fill {
        height: 100%;
        border-radius: 99px;
    }

    /* Camada invisível clicável sobre os Cards */
    div[data-testid="stHorizontalBlock"]:has(.card-kpi) .stButton {
        margin-top: -108px !important;
        height: 108px !important;
        position: relative;
        z-index: 10;
    }
    div[data-testid="stHorizontalBlock"]:has(.card-kpi) .stButton button {
        height: 108px !important;
        width: 100% !important;
        background: transparent !important;
        color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: 14px !important;
        cursor: pointer !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.card-kpi) .stButton button:hover {
        background: rgba(49, 0, 111, 0.035) !important;
    }

    /* Painéis e Containers de Relatório (Aba 2) */
    .report-panel {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 20px 22px;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
        margin-bottom: 16px;
    }
    .report-panel-title {
        font-size: 15px;
        font-weight: 800;
        color: #1E293B;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 14px;
        padding-bottom: 10px;
        border-bottom: 1px solid #F1F5F9;
    }
    .metric-row {
        margin-bottom: 12px;
    }
    .metric-row-header {
        display: flex;
        justify-content: space-between;
        font-size: 12.5px;
        font-weight: 600;
        color: #334155;
        margin-bottom: 4px;
    }
    .metric-bar-bg {
        width: 100%;
        height: 9px;
        background: #F1F5F9;
        border-radius: 99px;
        overflow: hidden;
    }
    .metric-bar-fill {
        height: 100%;
        border-radius: 99px;
    }

    /* Botões de Ação e Exportação */
    .stFormSubmitButton button, .stDownloadButton button {
        background: linear-gradient(90deg, #FF5F00 0%, #E05300 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 12px rgba(255, 95, 0, 0.25) !important;
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
    "DIOGO OSVASCONCELOS", "DOUGLAS FRAGA", "ELAINE BORGES", "FABIANA LESSA MOLICA", 
    "ISABELLY NOGUEIRA", "ITALO BERTI", "JEFFERSON ANDRADE", "LUCIANA PINA", 
    "MATEUS LIMA", "MAYARA SOUZA", "RONALDO FERRAMOLA", "SANDRA MARA", 
    "TAINA ZANELLATO", "THAYNA CRUZ", "THAYNA IBRAIM", "VINICIUS RODRIGUES", 
    "VIVIANE VENAGLIA", "WILLIAM LIMA"
]

# ==========================================
# 5. MENU LATERAL (NAVEGAÇÃO)
# ==========================================
st.sidebar.markdown("### 🏢 Gestão CIEE")
st.sidebar.caption("Painel Inteligente de Prospecção SP")

aba_selecionada = st.sidebar.radio(
    "Módulo de Acesso:",
    ["🔍 Prospecção de Leads", "📊 Relatório de Gestão & Ranking"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 👤 Identificação")

operador_logado = st.sidebar.selectbox(
    "Consultor(a) Ativo(a):",
    options=LISTA_OPERADORES_OFICIAIS,
    index=1  # Default: ALINE CRUZ
)
st.session_state["usuario_ativo"] = operador_logado
st.sidebar.success(f"Logado como:\n**{st.session_state['usuario_ativo']}**")

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

# Hero Banner Superior
subtitulo_topo = "Mapeamento Operacional de Empresas • Receita Federal SP" if aba_selecionada == "🔍 Prospecção de Leads" else "Painel Executivo de Acompanhamento, Eficiência Comercial e Diagnóstico de Recusas"
st.markdown(f"""
    <div class="ciee-hero">
        <div class="ciee-hero-left">
            <div class="ciee-hero-icon">🏛️</div>
            <div>
                <div class="ciee-hero-title">PAINEL DE GESTÃO E PROSPECÇÃO CIEE</div>
                <div class="ciee-hero-sub">{subtitulo_topo}</div>
            </div>
        </div>
        <div class="ciee-badge-live">
            <span class="live-dot"></span>
            <span>Operador: {st.session_state['usuario_ativo']}</span>
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

    # Função auxiliar para renderizar Cards no padrão Web App CIEE
    def render_kpi_card(titulo, valor, percentual, cor_hex, bg_icone, emoji, ativo):
        cls_ativo = "card-kpi-ativo" if ativo else ""
        largura_barra = min(max(percentual, 4.0), 100.0)
        return f"""
            <div class="card-kpi {cls_ativo}">
                <div class="kpi-header">
                    <span class="kpi-title">{titulo}</span>
                    <span class="kpi-icon-pill" style="background: {bg_icone}; color: {cor_hex};">{emoji}</span>
                </div>
                <div class="kpi-value" style="color: {cor_hex};">{fmt_num(valor)}</div>
                <div>
                    <div class="kpi-footer">
                        <span style="color: #64748B;">Participação</span>
                        <span style="color: {cor_hex};">{percentual:.1f}%</span>
                    </div>
                    <div class="kpi-progress-bg">
                        <div class="kpi-progress-fill" style="width: {largura_barra}%; background: {cor_hex};"></div>
                    </div>
                </div>
            </div>
        """

    # Dashboard Clicável
    c_t, c_nc, c_c, c_cf, c_conv, c_pa, c_pn = st.columns(7)

    with c_t:
        st.markdown(render_kpi_card("Total Base", total_cnpjs, 100.0, "#31006F", "#F3E8FF", "🏢", status_atual == "Todos"), unsafe_allow_html=True)
        if st.button(" ", key="card_todos", use_container_width=True):
            st.session_state["filtro_status_clique"] = "Todos"
            st.rerun()

    with c_nc:
        st.markdown(render_kpi_card("Pendentes", qtd_nao_contatados, pct(qtd_nao_contatados), "#475569", "#F1F5F9", "⏳", status_atual == "Lead Não Contatado"), unsafe_allow_html=True)
        if st.button(" ", key="card_nc", use_container_width=True):
            st.session_state["filtro_status_clique"] = "Lead Não Contatado"
            st.rerun()

    with c_c:
        st.markdown(render_kpi_card("Contatados", qtd_contatados, pct(qtd_contatados), "#005CB9", "#E0F2FE", "📞", status_atual == "Lead Contatado"), unsafe_allow_html=True)
        if st.button(" ", key="card_c", use_container_width=True):
            st.session_state["filtro_status_clique"] = "Lead Contatado"
            st.rerun()

    with c_cf:
        st.markdown(render_kpi_card("Contato Futuro", qtd_futuros, pct(qtd_futuros), "#722282", "#FAE8FF", "📅", status_atual == "Contato Futuro"), unsafe_allow_html=True)
        if st.button(" ", key="card_cf", use_container_width=True):
            st.session_state["filtro_status_clique"] = "Contato Futuro"
            st.rerun()

    with c_conv:
        st.markdown(render_kpi_card("Convertidos", qtd_convertidos, pct(qtd_convertidos), "#FF5F00", "#FFEDD5", "🚀", status_atual == "Lead Convertido"), unsafe_allow_html=True)
        if st.button(" ", key="card_conv", use_container_width=True):
            st.session_state["filtro_status_clique"] = "Lead Convertido"
            st.rerun()

    with c_pa:
        st.markdown(render_kpi_card("Parceiro Ativo", qtd_ativos, pct(qtd_ativos), "#059669", "#D1FAE5", "🤝", status_atual == "Parceiro Ativo"), unsafe_allow_html=True)
        if st.button(" ", key="card_pa", use_container_width=True):
            st.session_state["filtro_status_clique"] = "Parceiro Ativo"
            st.rerun()

    with c_pn:
        st.markdown(render_kpi_card("Prop. Negada", qtd_negados, pct(qtd_negados), "#DC2626", "#FEE2E2", "✖️", status_atual == "Proposta Negada"), unsafe_allow_html=True)
        if st.button(" ", key="card_pn", use_container_width=True):
            st.session_state["filtro_status_clique"] = "Proposta Negada"
            st.rerun()

    st.caption("👆 **Filtro Interativo:** Clique diretamente sobre qualquer card acima para filtrar a listagem de empresas.")

    # Filtros de Busca
    with st.expander("🔍 FILTROS AVANÇADOS E SEGMENTAÇÃO", expanded=True):
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
            busca_cep = st.text_input("CEP:", "")

        col_f5, col_f6, col_f7, col_f8 = st.columns(4)
        with col_f5:
            filtro_segmentacao_sel = st.selectbox("Segmentação:", ["Todos", "Varejo", "Outros Serviços"], index=0)
        with col_f6:
            filtro_setor_tipo_sel = st.selectbox("Tipo de Setor:", ["Todos", "Público", "Privado"], index=0)
        with col_f7:
            busca_bairro = st.text_input("Bairro ou Região:", "")
        with col_f8:
            busca_texto = st.text_input("Razão Social ou CNPJ:", "")

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            registros_por_pagina = st.selectbox("Linhas por Página:", [50, 100, 250, 500], index=1)
        with col_p2:
            pagina_atual = st.number_input("Página Atual:", min_value=1, value=1, step=1)

    offset_val = (pagina_atual - 1) * registros_por_pagina

    # Montagem do WHERE SQL
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
    # MODAL DE TRATAMENTO DE LEADS (POP-UP)
    # ==========================================
    @st.dialog("📝 Tratar Prospecção", width="large")
    def abrir_modal_tratamento(cnpj):
        query_emp = "SELECT * FROM empresas WHERE cnpj_formatado = :cnpj"
        res_df = pd.read_sql(text(query_emp), engine, params={"cnpj": cnpj})
        
        if res_df.empty:
            st.error("Empresa não localizada.")
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
            <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-left: 5px solid #FF5F00; border-radius: 12px; padding: 16px; margin-bottom: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
                <div style="font-size: 17px; font-weight: 800; color: #31006F; margin-bottom: 8px;">🏢 {nome_exibicao}</div>
                <div style="font-size: 13px; color: #334155; display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                    <div><b>Razão Social:</b> {row.get('razao_social', '-')}</div>
                    <div><b>CNPJ Completo:</b> <code style="background-color: #EFF6FF; color: #005CB9; font-weight: 800; padding: 3px 8px; border-radius: 6px;">{cnpj_completo_exibicao}</code></div>
                    <div><b>Porte:</b> {row.get('porte_empresa', 'Não Informado')}</div>
                    <div><b>Telefone:</b> {tel_fmt}</div>
                    <div><b>E-mail:</b> {email_fmt}</div>
                    <div><b>Endereço:</b> {endereco_completo}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        col_acao1, col_acao2 = st.columns(2)
        with col_acao1:
            st.link_button("📍 Ver Rota no Google Maps", maps_link, use_container_width=True)
        with col_acao2:
            clean_tel = "".join(filter(str.isdigit, tel_fmt))
            if clean_tel and eh_celular(clean_tel):
                msg_whats = urllib.parse.quote(f"Olá! Sou {st.session_state['usuario_ativo']} do CIEE e gostaria de falar com o responsável de RH da {nome_exibicao} sobre programas de Estágio e Aprendizagem.")
                st.link_button("💬 Abordar via WhatsApp Web", f"https://wa.me/55{clean_tel}?text={msg_whats}", use_container_width=True)
            else:
                st.button("☎️ Contato é Telefone Fixo (WhatsApp indisponível)", disabled=True, use_container_width=True)

        st.markdown("---")
        st.markdown("##### ⚙️ Atualização de Follow-up")
        
        status_banco = row.get('status_followup', '')
        idx_status = STATUS_OFICIAIS.index(status_banco) if status_banco in STATUS_OFICIAIS else 0

        col_st, col_rp = st.columns(2)
        with col_st:
            status_selecionado = st.selectbox("📌 Status do Follow-up:", options=STATUS_OFICIAIS, index=idx_status, key=f"status_select_{cnpj}")

        with col_rp:
            resp_banco = row.get('responsavel_tratamento', '') or ''
            idx_operador_atual = 0
            if resp_banco in LISTA_OPERADORES_OFICIAIS:
                idx_operador_atual = LISTA_OPERADORES_OFICIAIS.index(resp_banco)
            elif st.session_state["usuario_ativo"] in LISTA_OPERADORES_OFICIAIS:
                idx_operador_atual = LISTA_OPERADORES_OFICIAIS.index(st.session_state["usuario_ativo"])
                
            novo_resp_selecionado = st.selectbox(
                "👤 Responsável pelo Tratamento:",
                options=LISTA_OPERADORES_OFICIAIS,
                index=idx_operador_atual,
                key=f"resp_select_{cnpj}"
            )

        ticket_conversao = ""
        if status_selecionado == "Lead Convertido":
            ticket_conversao = st.text_input("🎟️ Protocolo / Ticket de Parceria CIEE:", placeholder="Ex: CIEE-SP-12345", key=f"ticket_{cnpj}")

        motivo_recusa_sel = ""
        if status_selecionado == "Proposta Negada":
            motivo_recusa_sel = st.selectbox("❌ Principal Motivo da Recusa:", MOTIVOS_RECUSA_OPCOES, key=f"recusa_{cnpj}")

        st.markdown("📜 **Histórico de Interações:**")
        obs_banco = row.get('observacoes', '') or ''
        if obs_banco:
            st.info(obs_banco)
        else:
            st.caption("Nenhum histórico registrado ainda.")

        with st.form(f"form_tratamento_{cnpj}"):
            nova_nota = st.text_area(
                "✍️ Registrar Nova Interação (será anexada ao histórico):",
                placeholder="Digite os detalhes da interação realizada...",
                height=90
            )
            
            is_admin = str(st.session_state["usuario_ativo"]).strip().upper() == "ALINE CRUZ"
            if is_admin:
                obs_manual_expander = st.expander("🔧 Editar histórico completo manualmente (Administrador)")
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
                        conn.execute(text(\"\"\"
                            UPDATE empresas 
                            SET responsavel_tratamento = :resp,
                                status_followup = :stat,
                                observacoes = :obs
                            WHERE cnpj_formatado = :cnpj
                        \"\"\"), {
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
    # TABELA PRINCIPAL DE EMPRESAS (RELAÇÃO)
    # ==========================================
    query_dados = f\"\"\"
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
    \"\"\"

    df_tabela = pd.read_sql(text(query_dados), engine, params=params)

    # CORREÇÃO DO ERRO st.columns() - PASSAMOS LARGURAS EXPLICITAS [3, 2]
    col_titulo_tab, col_export = st.columns([3, 2])
    with col_titulo_tab:
        status_indicator = f" • Filtro ativo: [{filtro_status_sel}]" if filtro_status_sel != "Todos" else ""
        st.markdown(f"#### 📋 Relação de Empresas ({fmt_num(total_filtrado)} CNPJs localizados{status_indicator})")

    with col_export:
        if not df_tabela.empty:
            csv_data = df_tabela.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="📥 Exportar Base Atual (CSV)",
                data=csv_data,
                file_name=f"base_empresas_ciee_pag_{pagina_atual}.csv",
                mime="text/csv",
                use_container_width=True
            )

    if df_tabela.empty:
        st.info("Nenhuma empresa encontrada com os parâmetros informados.")
    else:
        # Tabela totalmente limpa sem Responsável, Status e Observações
        colunas_exibicao = [
            'cnpj_formatado', 'razao_social', 'nome_fantasia', 'porte_empresa',
            'segmentacao', 'setor_tipo', 'bairro', 'cep'
        ]

        st.caption("👉 **Clique sobre qualquer linha da tabela** para abrir o pop-up com os dados completos e registrar o atendimento.")

        event = st.dataframe(
            df_tabela[colunas_exibicao],
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
        st.caption(f"Página {pagina_atual} de {fmt_num(total_paginas)} • Exibindo {len(df_tabela)} registros nesta página.")

# ==========================================
# ABA 2: RELATÓRIO DE GESTÃO E PRODUTIVIDADE (DESIGN APPS SCRIPT)
# ==========================================
else:
    query_gestao = """
        SELECT 
            COALESCE(NULLIF(TRIM(responsavel_tratamento), ''), 'Não Atribuído') AS responsavel,
            status_followup,
            observacoes,
            COUNT(*) AS total
        FROM empresas
        WHERE (responsavel_tratamento IS NOT NULL AND TRIM(responsavel_tratamento) != '')
           OR (status_followup IS NOT NULL AND TRIM(status_followup) != '' AND status_followup != 'Lead Não Contatado')
        GROUP BY 1, 2, 3
    """
    try:
        df_gestao = pd.read_sql(text(query_gestao), engine)
    except Exception:
        df_gestao = pd.DataFrame()

    total_abordados = int(df_gestao["total"].sum()) if not df_gestao.empty else 0
    total_conv_ativos = int(df_gestao[df_gestao["status_followup"].isin(["Lead Convertido", "Parceiro Ativo"])]["total"].sum()) if not df_gestao.empty else 0
    total_negados_rel = int(df_gestao[df_gestao["status_followup"] == "Proposta Negada"]["total"].sum()) if not df_gestao.empty else 0
    taxa_eficiencia_global = (total_conv_ativos / total_abordados * 100) if total_abordados > 0 else 0.0

    # Big Numbers Executivos
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
            <div class="report-panel" style="border-top: 4px solid #005CB9; padding: 16px;">
                <div class="kpi-title">Total de Empresas Trabalhadas</div>
                <div class="kpi-value" style="color: #005CB9; font-size: 28px; margin-top: 6px;">{fmt_num(total_abordados)}</div>
                <div class="kpi-sub">Leads com atuação registrada</div>
            </div>
        """, unsafe_allow_html=True)

    with m2:
        st.markdown(f"""
            <div class="report-panel" style="border-top: 4px solid #059669; padding: 16px;">
                <div class="kpi-title">Conversões + Parceiros Ativos</div>
                <div class="kpi-value" style="color: #059669; font-size: 28px; margin-top: 6px;">{fmt_num(total_conv_ativos)}</div>
                <div class="kpi-sub">Fechamentos consolidados</div>
            </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
            <div class="report-panel" style="border-top: 4px solid #FF5F00; padding: 16px;">
                <div class="kpi-title">Eficiência da Equipe (Conversão)</div>
                <div class="kpi-value" style="color: #FF5F00; font-size: 28px; margin-top: 6px;">{taxa_eficiencia_global:.1f}%</div>
                <div class="kpi-sub">Contatos vs. Convertidos</div>
            </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
            <div class="report-panel" style="border-top: 4px solid #DC2626; padding: 16px;">
                <div class="kpi-title">Propostas Negadas</div>
                <div class="kpi-value" style="color: #DC2626; font-size: 28px; margin-top: 6px;">{fmt_num(total_negados_rel)}</div>
                <div class="kpi-sub">Oportunidades recusadas</div>
            </div>
        """, unsafe_allow_html=True)

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("""
            <div class="report-panel">
                <div class="report-panel-title">
                    <span>🏆 Ranking de Eficiência da Equipe (Contatos x Convertidos)</span>
                    <span style="font-size: 11px; color: #64748B; font-weight: 600;">Performance Individual</span>
                </div>
        """, unsafe_allow_html=True)

        if not df_gestao.empty:
            df_ranking = df_gestao.groupby("Responsável").agg(
                Contatos_Realizados=("total", "sum"),
                Convertidos=("total", lambda x: sum(df_gestao.loc[x.index, "total"][df_gestao.loc[x.index, "status_followup"].isin(["Lead Convertido", "Parceiro Ativo"])])),
                Em_Negociacao=("total", lambda x: sum(df_gestao.loc[x.index, "total"][df_gestao.loc[x.index, "status_followup"].isin(["Lead Contatado", "Contato Futuro"])]))
            ).reset_index()

            df_ranking["Taxa_Eficiencia"] = df_ranking.apply(
                lambda r: round((r["Convertidos"] / r["Contatos_Realizados"] * 100), 1) if r["Contatos_Realizados"] > 0 else 0.0,
                axis=1
            )
            df_ranking = df_ranking.sort_values(by=["Convertidos", "Contatos_Realizados"], ascending=False).reset_index(drop=True)

            medalhas = ["🥇 ", "🥈 ", "🥉 "]
            df_ranking["Consultor(a)"] = [
                f"{medalhas[i] if i < 3 else f'{i+1}º • '}{row['Responsável']}"
                for i, row in df_ranking.iterrows()
            ]

            st.dataframe(
                df_ranking[["Consultor(a)", "Contatos_Realizados", "Em_Negociacao", "Convertidos", "Taxa_Eficiencia"]],
                column_config={
                    "Consultor(a)": "Consultor(a)",
                    "Contatos_Realizados": st.column_config.NumberColumn("Trabalhados", format="%d"),
                    "Em_Negociacao": st.column_config.NumberColumn("Em Andamento", format="%d"),
                    "Convertidos": st.column_config.NumberColumn("Convertidos", format="%d"),
                    "Taxa_Eficiencia": st.column_config.ProgressColumn(
                        "% Eficiência",
                        help="Percentual de conversão sobre os leads trabalhados",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100
                    )
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("Ainda não há interações registradas pelos consultores.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_g2:
        motivos_contagem = {motivo: 0 for motivo in MOTIVOS_RECUSA_OPCOES}
        if not df_gestao.empty:
            for _, r in df_gestao.iterrows():
                obs = str(r['observacoes'])
                for motivo in MOTIVOS_RECUSA_OPCOES:
                    if motivo in obs:
                        motivos_contagem[motivo] += int(r['total'])

        total_motivos = sum(motivos_contagem.values())
        html_recusas = """
            <div class="report-panel">
                <div class="report-panel-title">
                    <span>❌ Diagnóstico: Principais Recusas dos Clientes</span>
                    <span style="font-size: 11px; color: #DC2626; font-weight: 700;">Programas CIEE</span>
                </div>
        """
        for motivo, qtd in sorted(motivos_contagem.items(), key=lambda x: x[1], reverse=True):
            pct_m = (qtd / total_motivos * 100) if total_motivos > 0 else 0.0
            larg_m = max(pct_m, 3.0) if qtd > 0 else 0.0
            html_recusas += f"""
                <div class="metric-row">
                    <div class="metric-row-header">
                        <span>{motivo}</span>
                        <span style="color: #DC2626; font-weight: 800;">{fmt_num(qtd)} ({pct_m:.1f}%)</span>
                    </div>
                    <div class="metric-bar-bg">
                        <div class="metric-bar-fill" style="width: {larg_m}%; background: linear-gradient(90deg, #EF4444 0%, #DC2626 100%);"></div>
                    </div>
                </div>
            """
        html_recusas += "</div>"
        st.markdown(html_recusas, unsafe_allow_html=True)

        # Evolução do Pipeline
        html_funil = """
            <div class="report-panel">
                <div class="report-panel-title">
                    <span>📈 Evolução das Parcerias por Etapa</span>
                    <span style="font-size: 11px; color: #005CB9; font-weight: 700;">Pipeline Ativo</span>
                </div>
        """
        cores_status = {
            "Lead Contatado": "#005CB9",
            "Contato Futuro": "#722282",
            "Lead Convertido": "#FF5F00",
            "Parceiro Ativo": "#059669",
            "Proposta Negada": "#DC2626"
        }
        for st_nome, cor_st in cores_status.items():
            qtd_st = int(df_gestao[df_gestao["status_followup"] == st_nome]["total"].sum()) if not df_gestao.empty else 0
            pct_st = (qtd_st / total_abordados * 100) if total_abordados > 0 else 0.0
            larg_st = max(pct_st, 3.0) if qtd_st > 0 else 0.0
            html_funil += f"""
                <div class="metric-row">
                    <div class="metric-row-header">
                        <span>{st_nome}</span>
                        <span style="color: {cor_st}; font-weight: 800;">{fmt_num(qtd_st)} ({pct_st:.1f}%)</span>
                    </div>
                    <div class="metric-bar-bg">
                        <div class="metric-bar-fill" style="width: {larg_st}%; background: {cor_st};"></div>
                    </div>
                </div>
            """
        html_funil += "</div>"
        st.markdown(html_funil, unsafe_allow_html=True)


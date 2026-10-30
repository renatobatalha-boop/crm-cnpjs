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
# 3. IDENTIDADE VISUAL E AJUSTES DE EXPANSÃO LATERAL (CSS)
# ==========================================
st.markdown("""
    <style>
    header {visibility: hidden;}
    [data-testid="collapsedControl"] {display: block;}
    
    .stApp {
        background-color: #F4F6FB !important;
        color: #1E293B !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }

    .ciee-top-bar {
        background: linear-gradient(90deg, #31006F 0%, #722282 60%, #005CB9 100%);
        border-radius: 12px;
        padding: 14px 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
        box-shadow: 0 4px 14px rgba(49, 0, 111, 0.18);
        color: #ffffff;
    }
    .ciee-title {
        font-size: 19px;
        font-weight: 800;
        letter-spacing: -0.2px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .ciee-badge-live {
        background-color: rgba(255, 255, 255, 0.15);
        color: #ffffff;
        border: 1px solid rgba(255, 255, 255, 0.35);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .live-dot {
        width: 8px;
        height: 8px;
        background-color: #FF5F00;
        border-radius: 50%;
        box-shadow: 0 0 8px #FF5F00;
    }

    /* Cards e Botões de Filtro Rápido */
    .card-kpi {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px 12px 0 0;
        padding: 10px 12px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        border-top: 4px solid #CBD5E1;
    }
    .border-total { border-top-color: #31006F; }
    .border-nao-contatado { border-top-color: #94A3B8; }
    .border-contatado { border-top-color: #005CB9; }
    .border-futuro { border-top-color: #722282; }
    .border-convertido { border-top-color: #FF5F00; }
    .border-ativo { border-top-color: #059669; }
    .border-negado { border-top-color: #DC2626; }

    .kpi-title {
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #64748B;
    }
    .kpi-value {
        font-size: 20px;
        font-weight: 900;
        letter-spacing: -0.5px;
        line-height: 1.1;
        margin: 2px 0;
        color: #1E293B;
    }
    .kpi-sub {
        font-size: 10px;
        font-weight: 500;
        color: #94A3B8;
    }

    .stButton button {
        border-radius: 0 0 10px 10px !important;
        font-weight: 700 !important;
        font-size: 11px !important;
        padding: 4px !important;
        margin-top: -6px !important;
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
st.sidebar.markdown("### 🏢 Gestão CIEE")
aba_selecionada = st.sidebar.radio(
    "Navegue pelo painel:",
    ["🔍 Prospecção de Leads", "📊 Gestão e Produtividade CIEE"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 👤 Operador Ativo")

operador_logado = st.sidebar.selectbox(
    "Selecione seu nome:",
    options=LISTA_OPERADORES_OFICIAIS,
    index=1  # Default: ALINE CRUZ
)
st.session_state["usuario_ativo"] = operador_logado
st.sidebar.info(f"Conectado como:\n**{st.session_state['usuario_ativo']}**")

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

# Cabeçalho do Painel
st.markdown(f"""
    <div class="ciee-top-bar">
        <div class="ciee-title">
            <span>🏛️ PROSPECÇÃO DE CNPJs</span>
            <span style="font-size: 14px; font-weight: 400; opacity: 0.9;">| CIEE São Paulo</span>
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

    # Estado de sessão para filtro rápido via clique no Card
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

    # ==========================================
    # DASHBOARD INTERATIVO CLICÁVEL (ACIMA DOS FILTROS)
    # ==========================================
    c_t, c_nc, c_c, c_cf, c_conv, c_pa, c_pn = st.columns(7)

    with c_t:
        st.markdown(f'<div class="card-kpi border-total"><div class="kpi-title">Total Base</div><div class="kpi-value" style="color: #31006F;">{fmt_num(total_cnpjs)}</div><div class="kpi-sub">Todos</div></div>', unsafe_allow_html=True)
        if st.button("Ver Todos", key="btn_card_todos", use_container_width=True):
            st.session_state["filtro_status_clique"] = "Todos"
            st.rerun()

    with c_nc:
        st.markdown(f'<div class="card-kpi border-nao-contatado"><div class="kpi-title">Não Contatados</div><div class="kpi-value" style="color: #64748B;">{fmt_num(qtd_nao_contatados)}</div><div class="kpi-sub">{pct(qtd_nao_contatados):.1f}%</div></div>', unsafe_allow_html=True)
        if st.button("Ver Pendentes", key="btn_card_nc", use_container_width=True):
            st.session_state["filtro_status_clique"] = "Lead Não Contatado"
            st.rerun()

    with c_c:
        st.markdown(f'<div class="card-kpi border-contatado"><div class="kpi-title">Contatados</div><div class="kpi-value" style="color: #005CB9;">{fmt_num(qtd_contatados)}</div><div class="kpi-sub">{pct(qtd_contatados):.1f}%</div></div>', unsafe_allow_html=True)
        if st.button("Ver Contatados", key="btn_card_c", use_container_width=True):
            st.session_state["filtro_status_clique"] = "Lead Contatado"
            st.rerun()

    with c_cf:
        st.markdown(f'<div class="card-kpi border-futuro"><div class="kpi-title">Contato Futuro</div><div class="kpi-value" style="color: #722282;">{fmt_num(qtd_futuros)}</div><div class="kpi-sub">{pct(qtd_futuros):.1f}%</div></div>', unsafe_allow_html=True)
        if st.button("Ver Futuros", key="btn_card_cf", use_container_width=True):
            st.session_state["filtro_status_clique"] = "Contato Futuro"
            st.rerun()

    with c_conv:
        st.markdown(f'<div class="card-kpi border-convertido"><div class="kpi-title">Convertidos</div><div class="kpi-value" style="color: #FF5F00;">{fmt_num(qtd_convertidos)}</div><div class="kpi-sub">{pct(qtd_convertidos):.1f}%</div></div>', unsafe_allow_html=True)
        if st.button("Ver Convertidos", key="btn_card_conv", use_container_width=True):
            st.session_state["filtro_status_clique"] = "Lead Convertido"
            st.rerun()

    with c_pa:
        st.markdown(f'<div class="card-kpi border-ativo"><div class="kpi-title">Parceiro Ativo</div><div class="kpi-value" style="color: #059669;">{fmt_num(qtd_ativos)}</div><div class="kpi-sub">{pct(qtd_ativos):.1f}%</div></div>', unsafe_allow_html=True)
        if st.button("Ver Ativos", key="btn_card_pa", use_container_width=True):
            st.session_state["filtro_status_clique"] = "Parceiro Ativo"
            st.rerun()

    with c_pn:
        st.markdown(f'<div class="card-kpi border-negado"><div class="kpi-title">Prop. Negada</div><div class="kpi-value" style="color: #DC2626;">{fmt_num(qtd_negados)}</div><div class="kpi-sub">{pct(qtd_negados):.1f}%</div></div>', unsafe_allow_html=True)
        if st.button("Ver Negados", key="btn_card_pn", use_container_width=True):
            st.session_state["filtro_status_clique"] = "Proposta Negada"
            st.rerun()

    st.write("")

    # ==========================================
    # FILTROS DE BUSCA (ABAIXO DO DASHBOARD)
    # ==========================================
    with st.expander("🔍 FILTROS AVANÇADOS E PROSPECÇÃO", expanded=True):
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1:
            opcoes_status = ["Todos"] + STATUS_OFICIAIS
            idx_status_sel = opcoes_status.index(st.session_state["filtro_status_clique"]) if st.session_state["filtro_status_clique"] in opcoes_status else 0
            filtro_status_sel = st.selectbox("Status de Prospecção:", opcoes_status, index=idx_status_sel)
            st.session_state["filtro_status_clique"] = filtro_status_sel
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

    # Contagem de total filtrado
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
            <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-left: 5px solid #FF5F00; border-radius: 10px; padding: 16px; margin-bottom: 16px;">
                <div style="font-size: 17px; font-weight: 800; color: #31006F; margin-bottom: 8px;">🏢 {nome_exibicao}</div>
                <div style="font-size: 13px; color: #475569; display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                    <div><b>Razão Social:</b> {row.get('razao_social', '-')}</div>
                    <div><b>CNPJ Completo:</b> <code style="background-color: #F1F5F9; color: #005CB9; font-weight: 700; padding: 2px 6px; border-radius: 4px;">{cnpj_completo_exibicao}</code></div>
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
                    base_obs = f"{novo_bloco}\n{base_obs}".strip() if base_obs else novo_bloco

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
    # TABELA PRINCIPAL DE EMPRESAS (RELAÇÃO)
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
            COALESCE(bairro, 'Não Informado') AS bairro, cep,
            COALESCE(observacoes, '') AS observacoes
        FROM empresas {sql_where}
        ORDER BY 
            CASE WHEN (razao_social ILIKE '%comercio%' OR razao_social ILIKE '%varejo%' OR nome_fantasia ILIKE '%loja%') THEN 0 ELSE 1 END,
            cnpj_formatado
        LIMIT {registros_por_pagina} OFFSET {offset_val}
    """

    df_tabela = pd.read_sql(text(query_dados), engine, params=params)

    col_titulo_tab, col_export = st.columns([4, 1])
    with col_titulo_tab:
        status_indicador = f" - Filtrando por: [{filtro_status_sel}]" if filtro_status_sel != "Todos" else ""
        st.markdown(f"#### 📋 Relação de Empresas ({fmt_num(total_filtrado)} CNPJs localizados{status_indicador})")

    with col_export:
        if not df_tabela.empty:
            csv_data = df_tabela.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="📥 Exportar Página (CSV)",
                data=csv_data,
                file_name=f"leads_ciee_pag_{pagina_atual}.csv",
                mime="text/csv",
                use_container_width=True
            )

    if df_tabela.empty:
        st.info("Nenhuma empresa encontrada com os parâmetros informados.")
    else:
        # Colunas exibidas: Sem Responsável e Sem Status (visualização limpa)
        colunas_exibicao = [
            'cnpj_formatado', 'razao_social', 'nome_fantasia', 'porte_empresa',
            'segmentacao', 'setor_tipo', 'bairro', 'cep', 'observacoes'
        ]

        st.caption("👉 **Clique na linha da empresa** para abrir a ficha de prospecção.")

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
                "cep": "CEP",
                "observacoes": "Observações / Histórico"
            },
            hide_index=True,
            use_container_width=True,
            on_select="rerun",
            selection_mode="single-row"
        )

        if event and event.selection and event.selection.rows:
            idx_selecionado = event.selection.rows[0]
            cnpj_clicado = df_tabela.iloc[idx_selecionado]['cnpj_formatado']
            abrir_modal_tratamento(cnpj_clicado)

        total_paginas = (total_filtrado // registros_por_pagina) + (1 if total_filtrado % registros_por_pagina > 0 else 0)
        st.caption(f"Página {pagina_atual} de {fmt_num(total_paginas)} • Exibindo {len(df_tabela)} registros nesta página.")

# ==========================================
# ABA 2: GESTÃO E PRODUTIVIDADE CIEE
# ==========================================
else:
    st.markdown("### 📊 Indicadores de Performance & Produtividade")
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
        st.markdown("#### 🏆 Ranking de Conversão por Consultor")
        if not df_gestao.empty:
            df_ranking = df_gestao.groupby("Responsável").agg(
                Total_Leads_Trabalhados=("total", "sum"),
                Conversoes_Efetivas=("total", lambda x: sum(df_gestao.loc[x.index, "total"][df_gestao.loc[x.index, "status_followup"].isin(["Lead Convertido", "Parceiro Ativo"])]))
            ).reset_index().sort_values(by="Conversoes_Efetivas", ascending=False)
            
            st.dataframe(df_ranking, hide_index=True, use_container_width=True)
        else:
            st.info("Nenhum dado comercial disponível no momento.")

    with col_g2:
        st.markdown("#### ❌ Principais Recusas de Clientes CIEE")
        motivos_contagem = {motivo: 0 for motivo in MOTIVOS_RECUSA_OPCOES}
        
        if not df_gestao.empty:
            for _, r in df_gestao.iterrows():
                obs = str(r['observacoes'])
                for motivo in MOTIVOS_RECUSA_OPCOES:
                    if motivo in obs:
                        motivos_contagem[motivo] += r['total']
        
        df_recusas = pd.DataFrame(list(motivos_contagem.items()), columns=["Motivo", "Quantidade"]).sort_values(by="Quantidade", ascending=False)
        
        if df_recusas["Quantidade"].sum() > 0:
            st.bar_chart(df_recusas.set_index("Motivo"), color="#DC2626")
        else:
            st.caption("Nenhum motivo de recusa registrado até o momento. Utilize o status 'Proposta Negada' no modal de prospecção para categorizar.")

    st.markdown("---")
    st.markdown("#### 📈 Distribuição Geral de Contatos Efetuados")
    q


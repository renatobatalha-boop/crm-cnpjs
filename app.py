import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import urllib.parse

# ==========================================
# 1. CONFIGURACAO GERAL DA PAGINA
# ==========================================
st.set_page_config(
    page_title="Painel Corporativo - Gestao de CNPJs | CIEE",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. CONEXAO COM O BANCO DE DADOS (NEONDB)
# ==========================================
try:
    if "connections" in st.secrets and "postgresql" in st.secrets["connections"]:
        POSTGRES_URI = st.secrets["connections"]["postgresql"]["url"]
    else:
        POSTGRES_URI = "postgresql+psycopg2://neondb_owner:npg_bNDxjo9L2giC@ep-empty-hall-b4zx7bew-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require"
except Exception:
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
# 3. FUNCOES UTILITARIAS E CONSTANTES
# ==========================================
def fmt_num(val):
    if val is None:
        return "0"
    return f"{int(val):,}".replace(",", ".")

STATUS_OFICIAIS = [
    "Lead Não Contatado",
    "Lead Contatado",
    "Contato Futuro",
    "Lead Convertido",
    "Parceiro Ativo",
    "Proposta Negada"
]

# ==========================================
# 4. IDENTIDADE VISUAL INSTITUCIONAL CIEE
# ==========================================
st.markdown("""
    <style>
    header {visibility: hidden;}
    
    .stApp {
        background-color: #F4F6FB !important;
        color: #1E293B !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 3rem;
        max-width: 98%;
    }

    .ciee-top-bar {
        background: linear-gradient(90deg, #31006F 0%, #722282 60%, #005CB9 100%);
        border-radius: 12px;
        padding: 16px 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 18px;
        box-shadow: 0 4px 14px rgba(49, 0, 111, 0.18);
        color: #ffffff;
    }
    .ciee-title {
        font-size: 20px;
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
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 12px;
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

    .card-kpi {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 14px 16px;
        min-height: 105px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        border-top: 4px solid #CBD5E1;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .card-kpi:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
    }

    .border-total { border-top-color: #31006F; }
    .border-nao-contatado { border-top-color: #94A3B8; }
    .border-contatado { border-top-color: #005CB9; }
    .border-futuro { border-top-color: #722282; }
    .border-convertido { border-top-color: #FF5F00; }
    .border-ativo { border-top-color: #059669; }
    .border-negado { border-top-color: #DC2626; }

    .kpi-title {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #64748B;
    }
    .kpi-value {
        font-size: 24px;
        font-weight: 900;
        letter-spacing: -0.5px;
        line-height: 1.1;
        margin: 4px 0;
        color: #1E293B;
    }
    .kpi-sub {
        font-size: 11px;
        font-weight: 500;
        color: #94A3B8;
    }

    .summary-bar-ciee {
        background: linear-gradient(90deg, #F0F5FF 0%, #FAF5FF 100%);
        border: 1px solid #E0E7FF;
        border-left: 4px solid #FF5F00;
        padding: 12px 18px;
        border-radius: 8px;
        margin: 16px 0;
        font-size: 13.5px;
        color: #1E293B;
        line-height: 1.5;
    }

    div[data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03) !important;
    }
    div[data-testid="stExpander"] summary {
        background-color: #FFFFFF !important;
        color: #31006F !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
    }

    .stTextInput input, .stSelectbox [data-baseweb="select"], .stNumberInput input {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
    }
    .stTextInput label, .stSelectbox label, .stNumberInput label {
        color: #334155 !important;
        font-weight: 600 !important;
        font-size: 12px !important;
    }

    .stButton button {
        background-color: #FF5F00 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        padding: 8px 18px !important;
        box-shadow: 0 2px 8px rgba(255, 95, 0, 0.35) !important;
        transition: background-color 0.15s ease;
    }
    .stButton button:hover {
        background-color: #E05300 !important;
    }
    
    [data-testid="stDataFrame"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
        padding: 6px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 5. SESSAO DO CONSULTOR (BARRA LATERAL)
# ==========================================
st.sidebar.markdown("### 🏢 Gestão CIEE")
st.sidebar.markdown("Identifique-se abaixo para atribuir leads e registrar interações rapidamente em seu nome:")

if "usuario_ativo" not in st.session_state:
    st.session_state["usuario_ativo"] = "Consultor CIEE"

usuario_input = st.sidebar.text_input("👤 Seu Nome / Operador:", value=st.session_state["usuario_ativo"])
if usuario_input.strip():
    st.session_state["usuario_ativo"] = usuario_input.strip()

st.sidebar.success(f"Operador ativo:\n**{st.session_state['usuario_ativo']}**")
st.sidebar.markdown("---")
st.sidebar.caption("💡 **Dica:** Clique em qualquer empresa na tabela principal para abrir a ficha completa, traçar rota no Google Maps ou iniciar conversa no WhatsApp.")

# ==========================================
# 6. TOPO CORPORATIVO INSTITUCIONAL
# ==========================================
st.markdown(f"""
    <div class="ciee-top-bar">
        <div class="ciee-title">
            <span>🏛️ PROSPECÇÃO DE CNPJs</span>
            <span style="font-size: 14px; font-weight: 400; opacity: 0.9;">| Base Operacional SP</span>
        </div>
        <div class="ciee-badge-live">
            <span class="live-dot"></span>
            <span>Operador: {st.session_state['usuario_ativo']}</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 7. CARREGAMENTO DE RESPONSAVEIS DO BANCO
# ==========================================
@st.cache_data(ttl=120)
def get_responsaveis_cadastrados():
    query = """
        SELECT DISTINCT responsavel_tratamento 
        FROM empresas 
        WHERE responsavel_tratamento IS NOT NULL 
          AND TRIM(responsavel_tratamento) != ''
        ORDER BY responsavel_tratamento
    """
    try:
        with engine.connect() as conn:
            df_resp = pd.read_sql(text(query), conn)
            lista = df_resp["responsavel_tratamento"].dropna().tolist()
            return ["Todos", "Sem Responsável (Livres)"] + lista
    except Exception:
        return ["Todos", "Sem Responsável (Livres)"]

lista_responsaveis = get_responsaveis_cadastrados()

# ==========================================
# 8. FILTROS E PARAMETROS DE BUSCA
# ==========================================
with st.expander("🔍 FILTROS E PARÂMETROS DE BUSCA", expanded=True):
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    with col_f1:
        opcoes_filtro_status = ["Todos"] + STATUS_OFICIAIS
        filtro_status_sel = st.selectbox("Status de Follow-up:", opcoes_filtro_status, index=0)

    with col_f2:
        filtro_responsavel_sel = st.selectbox("Filtro por Responsável:", lista_responsaveis, index=0)

    with col_f3:
        lista_portes = [
            "Todos",
            "Micro Empresa (ME)",
            "Empresa de Pequeno Porte (EPP)",
            "Demais (Médio/Grande Porte)",
            "Não Informado"
        ]
        filtro_porte_sel = st.selectbox("Porte da Empresa:", lista_portes, index=0)

    with col_f4:
        busca_cep = st.text_input("CEP (ou prefixo de região):", "")

    col_f5, col_f6, col_f7, col_f8 = st.columns([2, 2, 1, 1])

    with col_f5:
        busca_bairro = st.text_input("Bairro:", "")

    with col_f6:
        busca_texto = st.text_input("Razão Social, Nome Fantasia ou CNPJ:", "")

    with col_f7:
        registros_por_pagina = st.selectbox(
            "Linhas por Página:",
            options=[50, 100, 250, 500],
            index=1
        )

    with col_f8:
        pagina_atual = st.number_input("Página:", min_value=1, value=1, step=1)

offset_val = (pagina_atual - 1) * registros_por_pagina

# ==========================================
# 9. QUERY DINAMICA SQL
# ==========================================
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
    if filtro_responsavel_sel == "Sem Responsável (Livres)":
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
    where_clauses.append("(razao_social ILIKE :txt OR nome_fantasia ILIKE :txt OR cnpj_formatado LIKE :txt)")
    params["txt"] = f"%{busca_texto.strip()}%"

sql_where = " WHERE " + " AND ".join(where_clauses)

# ==========================================
# 10. CONSULTA E CARDS DE KPIS
# ==========================================
query_kpis = f"""
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
    FROM empresas {sql_where}
"""

with engine.connect() as conn:
    kpi_res = conn.execute(text(query_kpis), params).fetchone()

total_cnpjs = kpi_res.total or 0
qtd_nao_contatados = kpi_res.nao_contatados or 0
qtd_contatados = kpi_res.contatados or 0
qtd_futuros = kpi_res.futuros or 0
qtd_convertidos = kpi_res.convertidos or 0
qtd_ativos = kpi_res.ativos or 0
qtd_negados = kpi_res.negados or 0

def calc_pct(val):
    return (val / total_cnpjs * 100) if total_cnpjs > 0 else 0.0

c_t, c_nc, c_c, c_cf, c_conv, c_pa, c_pn = st.columns(7)

with c_t:
    st.markdown(f"""
        <div class="card-kpi border-total">
            <div class="kpi-title">Total Base</div>
            <div class="kpi-value" style="color: #31006F;">{fmt_num(total_cnpjs)}</div>
            <div class="kpi-sub">CNPJs Filtrados</div>
        </div>
    """, unsafe_allow_html=True)

with c_nc:
    st.markdown(f"""
        <div class="card-kpi border-nao-contatado">
            <div class="kpi-title">Não Contatados</div>
            <div class="kpi-value" style="color: #64748B;">{fmt_num(qtd_nao_contatados)}</div>
            <div class="kpi-sub">{calc_pct(qtd_nao_contatados):.1f}% da base</div>
        </div>
    """, unsafe_allow_html=True)

with c_c:
    st.markdown(f"""
        <div class="card-kpi border-contatado">
            <div class="kpi-title">Contatados</div>
            <div class="kpi-value" style="color: #005CB9;">{fmt_num(qtd_contatados)}</div>
            <div class="kpi-sub">{calc_pct(qtd_contatados):.1f}% da base</div>
        </div>
    """, unsafe_allow_html=True)

with c_cf:
    st.markdown(f"""
        <div class="card-kpi border-futuro">
            <div class="kpi-title">Contato Futuro</div>
            <div class="kpi-value" style="color: #722282;">{fmt_num(qtd_futuros)}</div>
            <div class="kpi-sub">{calc_pct(qtd_futuros):.1f}% da base</div>
        </div>
    """, unsafe_allow_html=True)

with c_conv:
    st.markdown(f"""
        <div class="card-kpi border-convertido">
            <div class="kpi-title">Convertidos</div>
            <div class="kpi-value" style="color: #FF5F00;">{fmt_num(qtd_convertidos)}</div>
            <div class="kpi-sub">{calc_pct(qtd_convertidos):.1f}% da base</div>
        </div>
    """, unsafe_allow_html=True)

with c_pa:
    st.markdown(f"""
        <div class="card-kpi border-ativo">
            <div class="kpi-title">Parceiro Ativo</div>
            <div class="kpi-value" style="color: #059669;">{fmt_num(qtd_ativos)}</div>
            <div class="kpi-sub">{calc_pct(qtd_ativos):.1f}% da base</div>
        </div>
    """, unsafe_allow_html=True)

with c_pn:
    st.markdown(f"""
        <div class="card-kpi border-negado">
            <div class="kpi-title">Proposta Negada</div>
            <div class="kpi-value" style="color: #DC2626;">{fmt_num(qtd_negados)}</div>
            <div class="kpi-sub">{calc_pct(qtd_negados):.1f}% da base</div>
        </div>
    """, unsafe_allow_html=True)

total_trabalhado = qtd_contatados + qtd_futuros + qtd_convertidos + qtd_ativos + qtd_negados
taxa_sucesso = ((qtd_convertidos + qtd_ativos) / total_trabalhado * 100) if total_trabalhado > 0 else 0.0

st.markdown(f"""
    <div class="summary-bar-ciee">
        Dos <b>{fmt_num(total_cnpjs)}</b> CNPJs filtrados, <b>{fmt_num(qtd_nao_contatados)}</b> ainda aguardam primeira abordagem. 
        A equipe já trabalhou <b>{fmt_num(total_trabalhado)}</b> empresas, 
        resultando em <b>{fmt_num(qtd_convertidos)}</b> conversões e <b>{fmt_num(qtd_ativos)}</b> parceiros ativos 
        (Taxa de Efetividade nas Abordagens: <b>{taxa_sucesso:.1f}%</b>).
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 11. PAINEL GESTAO & FUNIL COMERCIAL NATIVO
# ==========================================
with st.expander("📊 PAINEL DE GESTÃO E PRODUTIVIDADE DA EQUIPE", expanded=False):
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("##### 📈 Distribuição de Status (Trabalhados)")
        df_status_chart = pd.DataFrame({
            "Status": ["Contatados", "Contato Futuro", "Convertidos", "Parceiro Ativo", "Proposta Negada"],
            "Total": [qtd_contatados, qtd_futuros, qtd_convertidos, qtd_ativos, qtd_negados]
        }).set_index("Status")
        st.bar_chart(df_status_chart, color="#FF5F00")

    with col_g2:
        st.markdown("##### 🏆 Ranking de Atuação por Responsável")
        query_ranking = f"""
            SELECT 
                COALESCE(NULLIF(TRIM(responsavel_tratamento), ''), 'Não Atribuído') AS "Responsável",
                COUNT(*) AS "Total Leads",
                COUNT(*) FILTER (WHERE status_followup IN ('Lead Convertido', 'Parceiro Ativo')) AS "Conversões"
            FROM empresas {sql_where}
            GROUP BY 1
            ORDER BY "Total Leads" DESC
            LIMIT 10
        """
        try:
            df_ranking = pd.read_sql(text(query_ranking), engine, params=params)
            st.dataframe(df_ranking, hide_index=True, use_container_width=True)
        except Exception:
            st.caption("Não foi possível carregar o ranking no momento.")

# ==========================================
# 12. JANELA MODAL DE TRATAMENTO / FOLLOW-UP
# ==========================================
@st.dialog("📝 Tratar Prospecção Comercial", width="large")
def abrir_modal_tratamento(cnpj):
    query_emp = "SELECT * FROM empresas WHERE cnpj_formatado = :cnpj"
    res_df = pd.read_sql(text(query_emp), engine, params={"cnpj": cnpj})
    
    if res_df.empty:
        st.error("Empresa não localizada.")
        return

    row = res_df.iloc[0]
    
    ddd = str(row.get("ddd1", "")).replace(".0", "").strip()
    tel = str(row.get("telefone1", "")).replace(".0", "").strip()
    tel_fmt = f"({ddd}) {tel}" if ddd and tel and ddd not in ["nan", "None"] else (tel or "Não informado")
    email_fmt = row.get("correio_eletronico") or "Não informado"
    nome_fantasia_val = str(row.get("nome_fantasia", "")).strip()
    nome_exibicao = nome_fantasia_val if nome_fantasia_val and nome_fantasia_val not in ["nan", "None", ""] else row.get("razao_social", "-")

    logradouro = str(row.get("logradouro") or "").strip()
    numero = str(row.get("numero") or "").strip()
    bairro = str(row.get("bairro") or "").strip()
    cep = str(row.get("cep") or "").strip()
    endereco_completo = f"{logradouro}, {numero} - {bairro}, São Paulo - SP, {cep}".strip(", -")
    query_maps = urllib.parse.quote(endereco_completo)
    maps_link = f"https://www.google.com/maps/search/?api=1&query={query_maps}"

    st.markdown(f"""
        <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-left: 5px solid #FF5F00; border-radius: 10px; padding: 16px; margin-bottom: 16px; box-shadow: 0 2px 6px rgba(0,0,0,0.03);">
            <div style="font-size: 17px; font-weight: 800; color: #31006F; margin-bottom: 8px;">🏢 {nome_exibicao}</div>
            <div style="font-size: 13px; color: #475569; display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                <div><b>Razão Social:</b> {row.get('razao_social', '-')}</div>
                <div><b>CNPJ:</b> <code style="background-color: #F1F5F9; color: #005CB9; font-weight: 700; padding: 2px 6px; border-radius: 4px;">{row.get('cnpj_formatado', '-')}</code></div>
                <div><b>Porte:</b> {row.get('porte_empresa', 'Não Informado')}</div>
                <div><b>Telefone:</b> {tel_fmt}</div>
                <div><b>E-mail:</b> {email_fmt}</div>
                <div><b>Endereço:</b> {endereco_completo}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    col_acao1, col_acao2 = st.columns(2)
    with col_acao1:
        st.link_button("📍 Ver Localização no Google Maps", maps_link, use_container_width=True)
    with col_acao2:
        digitos_tel = "".join(filter(str.isdigit, tel_fmt))
        if len(digitos_tel) >= 10:
            msg_whats = urllib.parse.quote(f"Olá! Sou {st.session_state['usuario_ativo']} do CIEE e gostaria de falar com o responsável de RH da {nome_exibicao} sobre programas de Estágio e Aprendizagem.")
            st.link_button("💬 Abordar via WhatsApp Web", f"https://wa.me/55{digitos_tel}?text={msg_whats}", use_container_width=True)
        else:
            st.button("💬 Telefone Inválido p/ WhatsApp", disabled=True, use_container_width=True)

    st.markdown("##### ⚙️ Atualização de Follow-up")
    
    status_banco = row.get("status_followup", "")
    idx_status = STATUS_OFICIAIS.index(status_banco) if status_banco in STATUS_OFICIAIS else 0

    col_st, col_rp = st.columns(2)
    with col_st:
        status_selecionado = st.selectbox(
            "📌 Status do Follow-up:",
            options=STATUS_OFICIAIS,
            index=idx_status,
            key=f"status_select_{cnpj}"
        )

    with col_rp:
        resp_banco = row.get("responsavel_tratamento", "") or ""
        valor_padrao_resp = resp_banco if resp_banco.strip() else st.session_state["usuario_ativo"]
        resp_atual = st.text_input(
            "👤 Responsável pelo Tratamento:",
            value=valor_padrao_resp,
            key=f"resp_input_{cnpj}"
        )

    ticket_conversao = ""
    if status_selecionado == "Lead Convertido":
        ticket_conversao = st.text_input(
            "🎟️ Número do Ticket / Protocolo de Venda:",
            placeholder="Ex: TCK-99482 / Contrato CIEE",
            key=f"ticket_{cnpj}"
        )

    obs_anterior = row.get("observacoes", "") or ""
    if obs_anterior.strip():
        st.markdown("**📜 Histórico Anterior Registrado:**")
        st.info(obs_anterior)

    with st.form(f"form_tratamento_{cnpj}"):
        nova_nota = st.text_area(
            "✍️ Registrar Nova Anotação (será adicionada ao histórico com data e hora):",
            placeholder="Digite o resumo da conversa, nome do contato na empresa, próximos passos...",
            height=90
        )
        
        manter_edicao_manual = st.expander("🔧 Editar histórico completo manualmente (Opcional)")
        with manter_edicao_manual:
            obs_manual = st.text_area("Histórico Bruto:", value=obs_anterior, height=80)

        btn_salvar = st.form_submit_button("💾 Salvar Tratamento", use_container_width=True)
        
        if btn_salvar:
            base_obs = obs_manual.strip()
            if nova_nota.strip():
                carimbo_tempo = datetime.now().strftime("%d/%m/%Y %H:%M")
                autor = resp_atual.strip() or st.session_state["usuario_ativo"]
                novo_bloco = f"[{carimbo_tempo} - {autor}]: {nova_nota.strip()}"
                base_obs = f"{novo_bloco}\n{base_obs}".strip() if base_obs else novo_bloco

            obs_final = base_obs
            if status_selecionado == "Lead Convertido" and ticket_conversao.strip():
                registro_ticket = f"[TICKET: {ticket_conversao.strip()}]"
                if registro_ticket not in obs_final:
                    obs_final = f"{registro_ticket} {obs_final}".strip()

            try:
                with engine.begin() as conn:
                    try:
                        conn.execute(text("""
                            UPDATE empresas 
                            SET responsavel_tratamento = :resp,
                                status_followup = :stat,
                                observacoes = :obs,
                                ticket_conversao = :ticket
                            WHERE cnpj_formatado = :cnpj
                        """), {
                            "resp": resp_atual.strip(),
                            "stat": status_selecionado,
                            "obs": obs_final,
                            "ticket": ticket_conversao.strip(),
                            "cnpj": cnpj
                        })
                    except Exception:
                        conn.execute(text("""
                            UPDATE empresas 
                            SET responsavel_tratamento = :resp,
                                status_followup = :stat,
                                observacoes = :obs
                            WHERE cnpj_formatado = :cnpj
                        """), {
                            "resp": resp_atual.strip(),
                            "stat": status_selecionado,
                            "obs": obs_final,
                            "cnpj": cnpj
                        })

                st.cache_data.clear()
                st.success("✅ Follow-up salvo com sucesso!")
                st.rerun()
            except Exception as err:
                st.error(f"Erro ao salvar: {err}")

# ==========================================
# 13. CONSULTA PAGINADA E TABELA PRINCIPAL
# ==========================================
query_dados = f"""
    SELECT 
        cnpj_formatado, razao_social, nome_fantasia, porte_empresa,
        COALESCE(responsavel_tratamento, '') AS responsavel_tratamento, 
        CASE 
            WHEN status_followup IN ('Lead Contatado', 'Contato Futuro', 'Lead Convertido', 'Parceiro Ativo', 'Proposta Negada') THEN status_followup
            ELSE 'Lead Não Contatado'
        END AS status_followup,
        cep, bairro, logradouro, numero,
        COALESCE(ddd1, '') AS ddd1, COALESCE(telefone1, '') AS telefone1,
        COALESCE(correio_eletronico, '') AS correio_eletronico, 
        COALESCE(observacoes, '') AS observacoes
    FROM empresas {sql_where}
    ORDER BY cnpj_formatado
    LIMIT {registros_por_pagina} OFFSET {offset_val}
"""

df_tabela = pd.read_sql(text(query_dados), engine, params=params)

def formatar_telefone(row):
    ddd = str(row.get("ddd1", "")).strip().replace(".0", "")
    tel = str(row.get("telefone1", "")).strip().replace(".0", "")
    if ddd and tel and ddd not in ["nan", "None"] and tel not in ["nan", "None"]:
        return f"({ddd}) {tel}"
    elif tel and tel not in ["nan", "None"]:
        return tel
    return "-"

if not df_tabela.empty:
    df_tabela["telefone_completo"] = df_tabela.apply(formatar_telefone, axis=1)
    df_tabela["correio_eletronico"] = df_tabela["correio_eletronico"].apply(
        lambda x: x if x and str(x).strip() not in ["nan", "None", ""] else "-"
    )
else:
    df_tabela["telefone_completo"] = []

col_titulo_tab, col_export = st.columns([4, 1])
with col_titulo_tab:
    st.markdown(f"#### 📋 Relação de Empresas ({fmt_num(total_cnpjs)} CNPJs localizados)")

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
    colunas_exibicao = [
        "cnpj_formatado",
        "razao_social",
        "nome_fantasia",
        "porte_empresa",
        "responsavel_tratamento",
        "status_followup",
        "telefone_completo",
        "correio_eletronico",
        "bairro",
        "cep",
        "observacoes"
    ]

    st.caption("👉 **Clique em qualquer linha** para abrir a janela de tratamento do Lead.")

    event = st.dataframe(
        df_tabela[colunas_exibicao],
        column_config={
            "cnpj_formatado": "CNPJ",
            "razao_social": "Razão Social",
            "nome_fantasia": "Nome Fantasia",
            "porte_empresa": "Porte",
            "responsavel_tratamento": "Responsável",
            "status_followup": "Status",
            "telefone_completo": "Telefone com DDD",
            "correio_eletronico": "E-mail",
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
        cnpj_clicado = df_tabela.iloc[idx_selecionado]["cnpj_formatado"]
        abrir_modal_tratamento(cnpj_clicado)

    total_paginas = (total_cnpjs // registros_por_pagina) + (1 if total_cnpjs % registros_por_pagina > 0 else 0)
    st.caption(f"Página {pagina_atual} de {fmt_num(total_paginas)} • Exibindo {len(df_tabela)} registros nesta página (Total: {fmt_num(total_cnpjs)} CNPJs).")


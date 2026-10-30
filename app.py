import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import plotly.express as px

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
# 2. CONEXÃO SEGURA COM O BANCO DE DADOS
# ==========================================
if "connections" in st.secrets and "postgresql" in st.secrets["connections"]:
    POSTGRES_URI = st.secrets["connections"]["postgresql"]["url"]
else:
    # Substitua pelas credenciais de secrets.toml em produção
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
# 3. IDENTIDADE VISUAL INSTITUCIONAL CIEE
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

    .stButton button {
        background-color: #FF5F00 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
    }
    </style>
""", unsafe_allow_html=True)

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
# 4. SESSÃO DO CONSULTOR (BARRA LATERAL)
# ==========================================
st.sidebar.image("https://portal.ciee.org.br/wp-content/themes/portal-ciee/assets/img/logo-ciee-novo.svg", width=160)
st.sidebar.markdown("### 👤 Operador Comercial")

if "usuario_ativo" not in st.session_state:
    st.session_state["usuario_ativo"] = "Consultor CIEE"

usuario_input = st.sidebar.text_input("Seu Nome / ID:", value=st.session_state["usuario_ativo"])
if usuario_input.strip():
    st.session_state["usuario_ativo"] = usuario_input.strip()

st.sidebar.info(f"Conectado como:\n**{st.session_state['usuario_ativo']}**")
st.sidebar.markdown("---")

# ==========================================
# 5. LISTAS E REGRAS DE BUSCA
# ==========================================
@st.cache_data(ttl=300)
def get_responsaveis_cadastrados():
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text("SELECT DISTINCT responsavel_tratamento FROM empresas WHERE responsavel_tratamento IS NOT NULL AND TRIM(responsavel_tratamento) != ''"), conn)
            return ["Todos", "Sem Responsável"] + sorted(df["responsavel_tratamento"].dropna().tolist())
    except Exception:
        return ["Todos", "Sem Responsável"]

lista_responsaveis = get_responsaveis_cadastrados()

# Topo
st.markdown(f"""
    <div class="ciee-top-bar">
        <div class="ciee-title">
            <span>🏛️ PROSPECÇÃO DE EMPRESAS SP</span>
            <span style="font-size: 14px; font-weight: 400; opacity: 0.9;">| Operação Comercial CIEE</span>
        </div>
        <div class="ciee-badge-live">
            <span class="live-dot"></span>
            <span>Operador: {st.session_state['usuario_ativo']}</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# Filtros Expansíveis
with st.expander("🔍 FILTROS AVANÇADOS E PROSPECÇÃO", expanded=True):
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        filtro_status_sel = st.selectbox("Status de Prospecção:", ["Todos"] + STATUS_OFICIAIS, index=0)
    with col_f2:
        filtro_responsavel_sel = st.selectbox("Responsável pelo Lead:", lista_responsaveis, index=0)
    with col_f3:
        lista_portes = ["Todos", "Micro Empresa (ME)", "Empresa de Pequeno Porte (EPP)", "Demais (Médio/Grande Porte)", "Não Informado"]
        filtro_porte_sel = st.selectbox("Porte da Empresa:", lista_portes, index=0)
    with col_f4:
        busca_cep = st.text_input("CEP:", "")

    col_f5, col_f6, col_f7, col_f8 = st.columns([2, 2, 1, 1])
    with col_f5:
        busca_bairro = st.text_input("Bairro ou Região:", "")
    with col_f6:
        busca_texto = st.text_input("Razão Social ou CNPJ:", "")
    with col_f7:
        registros_por_pagina = st.selectbox("Linhas/Pág:", [50, 100, 250, 500], index=1)
    with col_f8:
        pagina_atual = st.number_input("Página:", min_value=1, value=1, step=1)

offset_val = (pagina_atual - 1) * registros_por_pagina

# ==========================================
# 6. FILTROS E QUERIES SQL
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

sql_where = " WHERE " + " AND ".join(where_clauses)

# KPIs
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

pct = lambda val: (val / total_cnpjs * 100) if total_cnpjs > 0 else 0.0

# Cards
c_t, c_nc, c_c, c_cf, c_conv, c_pa, c_pn = st.columns(7)
with c_t:
    st.markdown(f'<div class="card-kpi border-total"><div class="kpi-title">Total Base</div><div class="kpi-value" style="color: #31006F;">{fmt_num(total_cnpjs)}</div><div class="kpi-sub">Filtrados</div></div>', unsafe_allow_html=True)
with c_nc:
    st.markdown(f'<div class="card-kpi border-nao-contatado"><div class="kpi-title">Não Contatados</div><div class="kpi-value" style="color: #64748B;">{fmt_num(qtd_nao_contatados)}</div><div class="kpi-sub">{pct(qtd_nao_contatados):.1f}%</div></div>', unsafe_allow_html=True)
with c_c:
    st.markdown(f'<div class="card-kpi border-contatado"><div class="kpi-title">Contatados</div><div class="kpi-value" style="color: #005CB9;">{fmt_num(qtd_contatados)}</div><div class="kpi-sub">{pct(qtd_contatados):.1f}%</div></div>', unsafe_allow_html=True)
with c_cf:
    st.markdown(f'<div class="card-kpi border-futuro"><div class="kpi-title">Contato Futuro</div><div class="kpi-value" style="color: #722282;">{fmt_num(qtd_futuros)}</div><div class="kpi-sub">{pct(qtd_futuros):.1f}%</div></div>', unsafe_allow_html=True)
with c_conv:
    st.markdown(f'<div class="card-kpi border-convertido"><div class="kpi-title">Convertidos</div><div class="kpi-value" style="color: #FF5F00;">{fmt_num(qtd_convertidos)}</div><div class="kpi-sub">{pct(qtd_convertidos):.1f}%</div></div>', unsafe_allow_html=True)
with c_pa:
    st.markdown(f'<div class="card-kpi border-ativo"><div class="kpi-title">Parceiro Ativo</div><div class="kpi-value" style="color: #059669;">{fmt_num(qtd_ativos)}</div><div class="kpi-sub">{pct(qtd_ativos):.1f}%</div></div>', unsafe_allow_html=True)
with c_pn:
    st.markdown(f'<div class="card-kpi border-negado"><div class="kpi-title">Prop. Negada</div><div class="kpi-value" style="color: #DC2626;">{fmt_num(qtd_negados)}</div><div class="kpi-sub">{pct(qtd_negados):.1f}%</div></div>', unsafe_allow_html=True)

# ==========================================
# 7. FUNIL DE VENDAS & PIPELINE VISUAL
# ==========================================
with st.expander("📊 VISUALIZAR FUNIL DE CONVERSÃO COMERCIAL", expanded=False):
    tab_funil, tab_taxas = st.tabs(["📉 Funil Visual", "📈 Métricas de Eficiência"])
    
    with tab_funil:
        dados_funil = pd.DataFrame({
            "Etapa": ["Total Mapeado", "Em Negociação", "Contato Futuro", "Convertidos / Ativos"],
            "Quantidade": [
                total_cnpjs, 
                qtd_contatados, 
                qtd_futuros, 
                (qtd_convertidos + qtd_ativos)
            ]
        })
        fig = px.funnel(
            dados_funil, 
            x="Quantidade", 
            y="Etapa", 
            color_discrete_sequence=["#31006F", "#005CB9", "#722282", "#FF5F00"]
        )
        fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=320)
        st.plotly_chart(fig, use_container_width=True)

    with tab_taxas:
        c_m1, c_m2, c_m3 = st.columns(3)
        taxa_abordagem = ((total_cnpjs - qtd_nao_contatados) / total_cnpjs * 100) if total_cnpjs > 0 else 0
        total_trabalhado = qtd_contatados + qtd_futuros + qtd_convertidos + qtd_ativos + qtd_negados
        taxa_conversao = ((qtd_convertidos + qtd_ativos) / total_trabalhado * 100) if total_trabalhado > 0 else 0
        
        c_m1.metric("Taxa de Abordagem", f"{taxa_abordagem:.1f}%", help="Empresas com pelo menos uma tentativa de contato")
        c_m2.metric("Conversão Efetiva", f"{taxa_conversao:.1f}%", help="Contratos fechados sobre os leads abordados")
        c_m3.metric("Leads Parados (Não Tratados)", f"{fmt_num(qtd_nao_contatados)}", help="Empresas livres para prospecção")

# ==========================================
# 8. MODAL DE TRATAMENTO DE LEADS
# ==========================================
@st.dialog("📝 Tratar Prospecção Comercial", width="large")
def abrir_modal_tratamento(cnpj):
    query_emp = "SELECT * FROM empresas WHERE cnpj_formatado = :cnpj"
    res_df = pd.read_sql(text(query_emp), engine, params={"cnpj": cnpj})
    
    if res_df.empty:
        st.error("Empresa não localizada.")
        return

    row = res_df.iloc[0]
    
    ddd = str(row.get('ddd1', '')).replace('.0', '').strip()
    tel = str(row.get('telefone1', '')).replace('.0', '').strip()
    tel_fmt = f"({ddd}) {tel}" if ddd and tel and ddd not in ['nan', 'None'] else (tel or "Não informado")
    email_fmt = row.get('correio_eletronico') or "Não informado"
    nome_exibicao = row.get('nome_fantasia') if row.get('nome_fantasia') and str(row.get('nome_fantasia')).strip() not in ['nan', 'None', ''] else row.get('razao_social')

    # Dados de endereço para Georreferenciamento
    logradouro = row.get('logradouro') or ""
    numero = row.get('numero') or ""
    bairro = row.get('bairro') or ""
    cep = row.get('cep') or ""
    endereco_completo = f"{logradouro}, {numero} - {bairro}, SP, {cep}"
    maps_link = f"https://www.google.com/maps/search/?api=1&query={endereco_completo.replace(' ', '+')}"

    # Cabeçalho da Empresa
    st.markdown(f"""
        <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-left: 5px solid #FF5F00; border-radius: 10px; padding: 16px; margin-bottom: 16px;">
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

    # Ações Rápidas (Maps & WhatsApp)
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.link_button("📍 Ver Rota no Google Maps", maps_link, use_container_width=True)
    with col_a2:
        if tel and tel != "Não informado":
            clean_tel = "".join(filter(str.isdigit, tel_fmt))
            st.link_button("💬 Abrir WhatsApp Comercial", f"https://wa.me/55{clean_tel}", use_container_width=True)

    st.markdown("---")
    
    # Atribuição de Responsável
    status_banco = row.get('status_followup', '')
    idx_status = STATUS_OFICIAIS.index(status_banco) if status_banco in STATUS_OFICIAIS else 0

    col_form_status, col_form_resp = st.columns(2)
    with col_form_status:
        status_selecionado = st.selectbox("📌 Status:", STATUS_OFICIAIS, index=idx_status, key=f"status_{cnpj}")

    with col_form_resp:
        resp_atual = row.get('responsavel_tratamento', '') or ''
        col_r1, col_r2 = st.columns([3, 2])
        with col_r1:
            novo_resp = st.text_input("👤 Responsável:", value=resp_atual, key=f"resp_{cnpj}")
        with col_r2:
            st.write("")
            st.write("")
            if st.button("🙋‍♂️ Atribuir a Mim", key=f"btn_me_{cnpj}", use_container_width=True):
                novo_resp = st.session_state["usuario_ativo"]
                st.session_state[f"resp_{cnpj}"] = novo_resp
                st.rerun()

    ticket_conversao = ""
    if status_selecionado == "Lead Convertido":
        ticket_conversao = st.text_input("🎟️ Protocolo / Ticket de Parceria CIEE:", placeholder="Ex: CIEE-SP-12345", key=f"ticket_{cnpj}")

    # Histórico de Atendimentos
    st.markdown("📜 **Histórico de Interações:**")
    obs_banco = row.get('observacoes', '') or ''
    if obs_banco:
        st.info(obs_banco)
    else:
        st.caption("Nenhum histórico registrado ainda.")

    nova_nota = st.text_area("✍️ Registrar Nova Interação Comercial:", placeholder="Descreva o retorno do contato, decisão da empresa, etc...", height=85)

    if st.button("💾 Salvar Tratamento", use_container_width=True, type="primary"):
        obs_formatada = obs_banco
        if nova_nota.strip():
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
            operador = novo_resp or st.session_state["usuario_ativo"]
            entrada_historico = f"[{timestamp} | {operador}]: {nova_nota.strip()}"
            obs_formatada = f"{entrada_historico}\n---\n{obs_banco}".strip()

        if status_selecionado == "Lead Convertido" and ticket_conversao.strip():
            reg_ticket = f"[CONTRATO: {ticket_conversao.strip()}]"
            if reg_ticket not in obs_formatada:
                obs_formatada = f"{reg_ticket} {obs_formatada}".strip()

        try:
            with engine.begin() as conn:
                conn.execute(text("""
                    UPDATE empresas 
                    SET responsavel_tratamento = :resp,
                        status_followup = :stat,
                        observacoes = :obs
                    WHERE cnpj_formatado = :cnpj
                """), {
                    "resp": novo_resp,
                    "stat": status_selecionado,
                    "obs": obs_formatada,
                    "cnpj": cnpj
                })
            st.success("✅ Lead atualizado com sucesso!")
            st.rerun()
        except Exception as err:
            st.error(f"Erro ao salvar: {err}")

# ==========================================
# 9. TABELA OPERACIONAL DE CNPJs
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
    ddd = str(row.get('ddd1', '')).strip().replace('.0', '')
    tel = str(row.get('telefone1', '')).strip().replace('.0', '')
    if ddd and tel and ddd not in ['nan', 'None'] and tel not in ['nan', 'None']:
        return f"({ddd}) {tel}"
    elif tel and tel not in ['nan', 'None']:
        return tel
    return "-"

if not df_tabela.empty:
    df_tabela['telefone_completo'] = df_tabela.apply(formatar_telefone, axis=1)
    df_tabela['correio_eletronico'] = df_tabela['correio_eletronico'].apply(
        lambda x: x if x and str(x).strip() not in ['nan', 'None', ''] else "-"
    )
else:
    df_tabela['telefone_completo'] = []

st.markdown(f"#### 📋 Relação de Empresas ({fmt_num(total_cnpjs)} CNPJs localizados)")

if df_tabela.empty:
    st.info("Nenhuma empresa encontrada com os parâmetros informados.")
else:
    colunas_exibicao = [
        'cnpj_formatado', 'razao_social', 'nome_fantasia', 'porte_empresa',
        'responsavel_tratamento', 'status_followup', 'telefone_completo', 
        'correio_eletronico', 'bairro', 'cep', 'observacoes'
    ]

    st.caption("👉 **Clique na linha da empresa** para abrir a janela de tratamento do Lead.")

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
            "bairro": "Bairro/Região",
            "cep": "CEP",
            "observacoes": "Última Nota / Histórico"
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

    total_paginas = (total_cnpjs // registros_por_pagina) + (1 if total_cnpjs % registros_por_pagina > 0 else 0)
    st.caption(f"Página {pagina_atual} de {fmt_num(total_paginas)} • Exibindo {len(df_tabela)} registros nesta página.")

            "status_followup": "Status",
            "telefone_completo": "Telefone com DDD",
            "correio_eletronico": "E-mail",
            "bairro": "Bairro",
            "cep": "CEP",
            "observacoes": "Observações"
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

    total_paginas = (total_cnpjs // registros_por_pagina) + (1 if total_cnpjs % registros_por_pagina > 0 else 0)
    st.caption(f"Página {pagina_atual} de {fmt_num(total_paginas)} • Exibindo {len(df_tabela)} registros nesta página (Total: {fmt_num(total_cnpjs)} CNPJs).")

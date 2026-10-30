import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# ==========================================
# CONFIGURAÇÃO GERAL DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Painel Corporativo - Gestão de CNPJs",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Conexão com o banco NeonDB
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
# FORMATAÇÃO NUMÉRICA (PADRÃO BR)
# ==========================================
def fmt_num(val):
    if val is None:
        return "0"
    return f"{int(val):,}".replace(",", ".")

# ==========================================
# TEMA DARK NEON ROXO COMPLETO (INCLUINDO TABELA)
# ==========================================
st.markdown("""
    <style>
    /* Ocultar barra superior padrão do Streamlit */
    header {visibility: hidden;}
    [data-testid="collapsedControl"] {display: none;}
    
    /* Fundo da aplicação */
    .stApp {
        background-color: #120722 !important;
        color: #f1f5f9 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 3rem;
        max-width: 98%;
    }

    /* Topo com gradiente escuro */
    .neon-top-bar {
        background: linear-gradient(135deg, #270d47 0%, #150929 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 18px 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    .neon-top-title {
        font-size: 22px;
        font-weight: 800;
        letter-spacing: 0.8px;
        color: #ffffff;
        text-transform: uppercase;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .neon-badge-live {
        background-color: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        border: 1px solid rgba(74, 222, 128, 0.3);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .live-dot {
        width: 8px;
        height: 8px;
        background-color: #4ade80;
        border-radius: 50%;
        box-shadow: 0 0 10px #4ade80;
    }

    /* Cards de Indicadores */
    .kpi-card {
        border-radius: 14px;
        padding: 16px 18px;
        min-height: 120px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        border: 1px solid rgba(255, 255, 255, 0.08);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
    }

    .kpi-total {
        background: linear-gradient(135deg, #a855f7 0%, #6b21a8 100%);
        color: #ffffff;
    }
    .kpi-nao-contatado {
        background: linear-gradient(135deg, #2b134d 0%, #1c0c33 100%);
        border: 1px solid rgba(255, 255, 255, 0.12);
        color: #cbd5e1;
    }
    .kpi-contatado {
        background: linear-gradient(135deg, #0284c7 0%, #034870 100%);
        color: #ffffff;
    }
    .kpi-futuro {
        background: linear-gradient(135deg, #ca8a04 0%, #713f12 100%);
        color: #ffffff;
    }
    .kpi-convertido {
        background: linear-gradient(135deg, #15803d 0%, #064e3b 100%);
        border: 1px solid rgba(74, 222, 128, 0.3);
        color: #ffffff;
    }
    .kpi-ativo {
        background: linear-gradient(135deg, #0d9488 0%, #115e59 100%);
        color: #ffffff;
    }
    .kpi-negado {
        background: linear-gradient(135deg, #be123c 0%, #881337 100%);
        color: #ffffff;
    }

    .kpi-title {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        opacity: 0.85;
    }
    .kpi-value {
        font-size: 26px;
        font-weight: 900;
        letter-spacing: -0.5px;
        line-height: 1.1;
        margin: 6px 0;
    }
    .kpi-sub {
        font-size: 12px;
        opacity: 0.75;
    }

    /* Faixa de Resumo */
    .neon-summary-bar {
        background: #1c0e35;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-left: 4px solid #a855f7;
        padding: 14px 20px;
        border-radius: 10px;
        margin: 18px 0;
        font-size: 14px;
        color: #e2e8f0;
    }

    /* Container de Expander dos Filtros */
    div[data-testid="stExpander"] {
        background-color: #1a0b30 !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 12px !important;
    }
    div[data-testid="stExpander"] summary {
        background-color: #1a0b30 !important;
        color: #f8fafc !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
    }

    /* Inputs e Caixas de Seleção */
    .stTextInput input, .stSelectbox [data-baseweb="select"], .stNumberInput input {
        background-color: #240e42 !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 8px !important;
    }
    .stTextInput label, .stSelectbox label, .stNumberInput label {
        color: #cbd5e1 !important;
        font-weight: 600 !important;
        font-size: 12px !important;
    }
    
    /* Customização do Dataframe / Tabela Escura */
    [data-testid="stDataFrame"] {
        background-color: #190a2e !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        padding: 6px !important;
    }
    [data-testid="stDataFrame"] canvas {
        filter: invert(0.92) hue-rotate(180deg) !important;
        border-radius: 8px !important;
    }
    [data-testid="stDataFrame"] div {
        color: #ffffff !important;
    }

    /* Botões */
    .stButton button {
        background: linear-gradient(90deg, #9333ea 0%, #7e22ce 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        padding: 8px 16px !important;
        box-shadow: 0 4px 14px rgba(147, 51, 234, 0.4) !important;
    }
    .stButton button:hover {
        background: linear-gradient(90deg, #a855f7 0%, #9333ea 100%) !important;
        transform: translateY(-1px);
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# HEADER PRINCIPAL
# ==========================================
st.markdown("""
    <div class="neon-top-bar">
        <div class="neon-top-title">
            <span>PAINEL DE PROSPECÇÃO DE CNPJS</span>
        </div>
        <div class="neon-badge-live">
            <span class="live-dot"></span>
            <span>Operação Ativa</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# STATUS OFICIAIS
# ==========================================
STATUS_OFICIAIS = [
    "Lead Não Contatado",
    "Lead Contatado",
    "Contato Futuro",
    "Lead Convertido",
    "Parceiro Ativo",
    "Proposta Negada"
]

# ==========================================
# FILTROS E PARÂMETROS DE BUSCA
# ==========================================
with st.expander("🔍 FILTROS E PARÂMETROS DE BUSCA", expanded=True):
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    with col_f1:
        opcoes_filtro_status = ["Todos"] + STATUS_OFICIAIS
        filtro_status_sel = st.selectbox("Status de Follow-up:", opcoes_filtro_status, index=0)

    with col_f2:
        busca_responsavel = st.text_input("Responsável pelo Tratamento:", "")

    with col_f3:
        lista_portes = ["Todos", "Micro Empresa (ME)", "Empresa de Pequeno Porte (EPP)", "Demais (Médio/Grande Porte)", "Não Informado"]
        filtro_porte_sel = st.selectbox("Porte da Empresa:", lista_portes, index=0)

    with col_f4:
        busca_cep = st.text_input("CEP (ou parte dele):", "")

    col_f5, col_f6, col_f7, col_f8 = st.columns([2, 2, 1, 1])
    with col_f5:
        busca_bairro = st.text_input("Bairro:", "")
    with col_f6:
        busca_texto = st.text_input("Razão Social ou CNPJ:", "")

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
# QUERY DINÂMICA SQL
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

if busca_responsavel.strip():
    if busca_responsavel.strip().lower() in ["sem responsável", "sem responsavel", "vazio"]:
        where_clauses.append("(responsavel_tratamento IS NULL OR TRIM(responsavel_tratamento) = '')")
    else:
        where_clauses.append("responsavel_tratamento ILIKE :resp")
        params["resp"] = f"%{busca_responsavel.strip()}%"

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

# Consulta de KPIs
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

# ==========================================
# CARDS DE INDICADORES (GRADIENTE NEON)
# ==========================================
c_t, c_nc, c_c, c_cf, c_conv, c_pa, c_pn = st.columns(7)

with c_t:
    st.markdown(f"""
        <div class="kpi-card kpi-total">
            <div class="kpi-title">Total Base</div>
            <div class="kpi-value">{fmt_num(total_cnpjs)}</div>
            <div class="kpi-sub">CNPJs Filtrados</div>
        </div>
    """, unsafe_allow_html=True)

with c_nc:
    st.markdown(f"""
        <div class="kpi-card kpi-nao-contatado">
            <div class="kpi-title">Não Contatados</div>
            <div class="kpi-value">{fmt_num(qtd_nao_contatados)}</div>
            <div class="kpi-sub">{pct(qtd_nao_contatados):.1f}% da base</div>
        </div>
    """, unsafe_allow_html=True)

with c_c:
    st.markdown(f"""
        <div class="kpi-card kpi-contatado">
            <div class="kpi-title">Contatados</div>
            <div class="kpi-value">{fmt_num(qtd_contatados)}</div>
            <div class="kpi-sub">{pct(qtd_contatados):.1f}% da base</div>
        </div>
    """, unsafe_allow_html=True)

with c_cf:
    st.markdown(f"""
        <div class="kpi-card kpi-futuro">
            <div class="kpi-title">Contato Futuro</div>
            <div class="kpi-value">{fmt_num(qtd_futuros)}</div>
            <div class="kpi-sub">{pct(qtd_futuros):.1f}% da base</div>
        </div>
    """, unsafe_allow_html=True)

with c_conv:
    st.markdown(f"""
        <div class="kpi-card kpi-convertido">
            <div class="kpi-title">Convertidos</div>
            <div class="kpi-value">{fmt_num(qtd_convertidos)}</div>
            <div class="kpi-sub">{pct(qtd_convertidos):.1f}% da base</div>
        </div>
    """, unsafe_allow_html=True)

with c_pa:
    st.markdown(f"""
        <div class="kpi-card kpi-ativo">
            <div class="kpi-title">Parceiro Ativo</div>
            <div class="kpi-value">{fmt_num(qtd_ativos)}</div>
            <div class="kpi-sub">{pct(qtd_ativos):.1f}% da base</div>
        </div>
    """, unsafe_allow_html=True)

with c_pn:
    st.markdown(f"""
        <div class="kpi-card kpi-negado">
            <div class="kpi-title">Proposta Negada</div>
            <div class="kpi-value">{fmt_num(qtd_negados)}</div>
            <div class="kpi-sub">{pct(qtd_negados):.1f}% da base</div>
        </div>
    """, unsafe_allow_html=True)

# Faixa de resumo textual
st.markdown(f"""
    <div class="neon-summary-bar">
        Dos <b>{fmt_num(total_cnpjs)}</b> CNPJs filtrados, <b>{fmt_num(qtd_nao_contatados)}</b> ainda aguardam primeiro contato.
        Já foram abordados <b>{fmt_num(qtd_contatados + qtd_futuros + qtd_convertidos + qtd_ativos + qtd_negados)}</b> leads,
        resultando em <b>{fmt_num(qtd_convertidos)}</b> conversões diretas e <b>{fmt_num(qtd_ativos)}</b> parceiros ativos na base.
    </div>
""", unsafe_allow_html=True)

# ==========================================
# CONSULTA PAGINADA
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
    return "Não informado"

if not df_tabela.empty:
    df_tabela['telefone_completo'] = df_tabela.apply(formatar_telefone, axis=1)
    df_tabela['correio_eletronico'] = df_tabela['correio_eletronico'].apply(
        lambda x: x if x and str(x).strip() not in ['nan', 'None', ''] else "Não informado"
    )
else:
    df_tabela['telefone_completo'] = []

# ==========================================
# JANELA MODAL DE TRATAMENTO / FOLLOW-UP
# ==========================================
@st.dialog("📝 Tratar Prospecção", width="large")
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

    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1f0b3b 0%, #130726 100%); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 10px; padding: 16px; margin-bottom: 15px; color: #f1f5f9;">
            <div style="font-size: 17px; font-weight: 800; color: #ffffff; margin-bottom: 8px;">🏢 {nome_exibicao}</div>
            <div style="font-size: 13px; color: #cbd5e1; display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                <div><b>Razão Social:</b> {row.get('razao_social', '-')}</div>
                <div><b>CNPJ:</b> <code style="background-color: #2e1055; color: #38bdf8; padding: 2px 6px; border-radius: 4px;">{row.get('cnpj_formatado', '-')}</code></div>
                <div><b>Porte:</b> {row.get('porte_empresa', 'Não Informado')}</div>
                <div><b>Telefone:</b> {tel_fmt}</div>
                <div style="grid-column: span 2;"><b>E-mail:</b> {email_fmt}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("##### Atualização de Follow-up")
    
    status_banco = row.get('status_followup', '')
    idx_status = STATUS_OFICIAIS.index(status_banco) if status_banco in STATUS_OFICIAIS else 0

    status_selecionado = st.selectbox(
        "📌 Status do Follow-up:",
        options=STATUS_OFICIAIS,
        index=idx_status,
        key=f"status_select_{cnpj}"
    )

    ticket_conversao = ""
    if status_selecionado == "Lead Convertido":
        ticket_conversao = st.text_input(
            "🎟️ Número do Ticket / Protocolo de Venda:",
            placeholder="Ex: TCK-99482 / Pedido 102",
            key=f"ticket_{cnpj}"
        )

    with st.form(f"form_tratamento_{cnpj}"):
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            resp_atual = st.text_input(
                "👤 Responsável pelo Tratamento:",
                value=row.get('responsavel_tratamento', '') or ''
            )

        obs_anterior = row.get('observacoes', '') or ''
        obs_nova = st.text_area(
            "💬 Observações do Atendimento:",
            value=obs_anterior,
            height=110
        )
        
        btn_salvar = st.form_submit_button("💾 Salvar Tratamento", use_container_width=True)
        
        if btn_salvar:
            obs_final = obs_nova
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
                            "resp": resp_atual,
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
                            "resp": resp_atual,
                            "stat": status_selecionado,
                            "obs": obs_final,
                            "cnpj": cnpj
                        })

                st.success("✅ Follow-up salvo com sucesso!")
                st.rerun()
            except Exception as err:
                st.error(f"Erro ao salvar: {err}")

# ==========================================
# RELAÇÃO DE EMPRESAS (TABELA ESCURA)
# ==========================================
st.markdown(f"#### 📋 Relação de Empresas ({fmt_num(total_cnpjs)} CNPJs localizados)")

if df_tabela.empty:
    st.info("Nenhuma empresa encontrada com os parâmetros informados.")
else:
    colunas_exibicao = [
        'cnpj_formatado', 'razao_social', 'nome_fantasia', 'porte_empresa',
        'responsavel_tratamento', 'status_followup', 'telefone_completo', 
        'correio_eletronico', 'bairro', 'cep', 'observacoes'
    ]

    st.caption("👉 **Dica:** Clique em qualquer linha para abrir a janela de tratamento do Lead.")

    # Dataframe escuro com seleção de linha
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

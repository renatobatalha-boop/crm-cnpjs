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
    initial_sidebar_state="expanded"
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
# ESTILIZAÇÃO CSS CUSTOMIZADA (LAYOUT DA IMAGEM)
# ==========================================
st.markdown("""
    <style>
    /* Oculta topo padrão do Streamlit */
    header {visibility: hidden;}
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }

    /* Barra Superior Corporativa */
    .top-header {
        background: linear-gradient(90deg, #4A154B 0%, #300A32 100%);
        padding: 14px 24px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        color: white;
        margin-bottom: 20px;
    }
    .top-title {
        font-size: 20px;
        font-weight: 800;
        letter-spacing: 0.5px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .badge-user {
        background-color: #ffffff;
        color: #4A154B;
        font-size: 12px;
        font-weight: 700;
        padding: 4px 12px;
        border-radius: 20px;
    }

    /* Painel de Filtros e Cards */
    .filter-box {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    /* Cards de Indicadores */
    .metric-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 14px 18px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        border-top: 4px solid #6c757d;
        margin-bottom: 12px;
    }
    .card-total { border-top-color: #4A154B; }
    .card-pendente { border-top-color: #d9534f; }
    .card-negado { border-top-color: #c9302c; }
    .card-agendado { border-top-color: #337ab7; }
    .card-tratado { border-top-color: #1a8a59; }

    .card-title {
        font-size: 12px;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
    }
    .card-value {
        font-size: 26px;
        font-weight: 800;
        margin: 4px 0;
    }
    .val-total { color: #4A154B; }
    .val-pendente { color: #d9534f; }
    .val-negado { color: #c9302c; }
    .val-agendado { color: #337ab7; }
    .val-tratado { color: #1a8a59; }

    .card-sub {
        font-size: 11px;
        color: #94a3b8;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# TOPO CORPORATIVO
# ==========================================
st.markdown("""
    <div class="top-header">
        <div class="top-title">
            <span>🏛️ PROSPECÇÃO DE CNPJs</span>
            <span style="font-size: 15px; font-weight: 400; opacity: 0.85;">| Base Operacional</span>
        </div>
        <div style="display: flex; gap: 10px; align-items: center;">
            <span class="badge-user">Editor</span>
            <span style="font-size: 13px; opacity: 0.9;">Equipe SP</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# MENU LATERAL
# ==========================================
with st.sidebar:
    st.markdown("### 📑 Menu")
    opcao_menu = st.radio(
        "Navegação:",
        ["📊 Relatórios e Carteira", "📋 Orientações e Regras", "⚙️ Configurações"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.caption("Sistema de Tratamento e CRM v2.0")

if opcao_menu != "📊 Relatórios e Carteira":
    st.info("Seção em desenvolvimento. Acesse a aba 'Relatórios e Carteira'.")
    st.stop()

# ==========================================
# SEÇÃO: CONSULTAS FREQUENTES (BOTÕES RÁPIDOS)
# ==========================================
st.markdown("##### ⚡ CONSULTAS FREQUENTES")
col_b1, col_b2, col_b3, col_b4, col_b5, col_b6 = st.columns(6)

if "quick_filter" not in st.session_state:
    st.session_state["quick_filter"] = "Todos"

with col_b1:
    if st.button("Ver Todos", use_container_width=True):
        st.session_state["quick_filter"] = "Todos"
with col_b2:
    if st.button("Apenas Pendentes", use_container_width=True):
        st.session_state["quick_filter"] = "Pendente"
with col_b3:
    if st.button("Negado Operação", use_container_width=True):
        st.session_state["quick_filter"] = "Negado Operacao"
with col_b4:
    if st.button("Agendados", use_container_width=True):
        st.session_state["quick_filter"] = "Agendado"
with col_b5:
    if st.button("Tratados", use_container_width=True):
        st.session_state["quick_filter"] = "Tratado"
with col_b6:
    if st.button("Sem Responsável", use_container_width=True):
        st.session_state["quick_filter"] = "SemResp"

# ==========================================
# GRID DE FILTROS NA PÁGINA PRINCIPAL
# ==========================================
with st.expander("🔍 FILTROS E PARÂMETROS DE BUSCA", expanded=True):
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    
    with col_f1:
        lista_status = ["Todos", "Pendente", "Negado Operacao", "Agendado", "Tratado", "Sem Interesse", "Em Contato"]
        def_status_idx = 0
        if st.session_state["quick_filter"] in lista_status:
            def_status_idx = lista_status.index(st.session_state["quick_filter"])
        filtro_status_sel = st.selectbox("Status de Follow-up:", lista_status, index=def_status_idx)

    with col_f2:
        busca_responsavel = st.text_input("Responsável pelo Tratamento:", value="Sem Responsável" if st.session_state["quick_filter"] == "SemResp" else "")

    with col_f3:
        lista_portes = ["Todos", "Micro Empresa (ME)", "Empresa de Pequeno Porte (EPP)", "Demais (Médio/Grande Porte)", "Não Informado"]
        filtro_porte_sel = st.selectbox("Porte da Empresa:", lista_portes, index=0)

    with col_f4:
        busca_cep = st.text_input("CEP (ou parte dele):", "")

    col_f5, col_f6, col_f7 = st.columns([2, 2, 1])
    with col_f5:
        busca_bairro = st.text_input("Bairro:", "")
    with col_f6:
        busca_texto = st.text_input("Razão Social ou CNPJ:", "")
    with col_f7:
        pagina_atual = st.number_input("Página:", min_value=1, value=1, step=1)

registros_por_pagina = 100
offset_val = (pagina_atual - 1) * registros_por_pagina

# ==========================================
# QUERY DINÂMICA SQL NO BANCO DE DADOS
# ==========================================
where_clauses = ["1=1"]
params = {}

if filtro_status_sel != "Todos":
    where_clauses.append("status_followup = :stat")
    params["stat"] = filtro_status_sel

if busca_responsavel.strip():
    if busca_responsavel.strip().lower() in ["sem responsável", "sem responsavel", "vazio"]:
        where_clauses.append("(responsavel_tratamento IS NULL OR responsavel_tratamento = '')")
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

# Consulta agregada de KPIs
query_kpis = f"""
    SELECT 
        COUNT(*) AS total,
        COUNT(*) FILTER (WHERE status_followup = 'Pendente') AS pendentes,
        COUNT(*) FILTER (WHERE status_followup = 'Negado Operacao') AS negados,
        COUNT(*) FILTER (WHERE status_followup = 'Agendado') AS agendados,
        COUNT(*) FILTER (WHERE status_followup = 'Tratado') AS tratados
    FROM empresas {sql_where}
"""

with engine.connect() as conn:
    kpi_res = conn.execute(text(query_kpis), params).fetchone()

total_cnpjs = kpi_res.total or 0
qtd_pendentes = kpi_res.pendentes or 0
qtd_negado = kpi_res.negados or 0
qtd_agendados = kpi_res.agendados or 0
qtd_tratados = kpi_res.tratados or 0

pct_pendente = (qtd_pendentes / total_cnpjs * 100) if total_cnpjs > 0 else 0.0
pct_negado = (qtd_negado / total_cnpjs * 100) if total_cnpjs > 0 else 0.0
pct_agendado = (qtd_agendados / total_cnpjs * 100) if total_cnpjs > 0 else 0.0
pct_tratado = (qtd_tratados / total_cnpjs * 100) if total_cnpjs > 0 else 0.0

# ==========================================
# CARDS DE INDICADORES (CONFORME SOLICITADO)
# ==========================================
col_c1, col_c2, col_c3, col_c4, col_c5 = st.columns(5)

with col_c1:
    st.markdown(f"""
        <div class="metric-card card-total">
            <div class="card-title">Total de CNPJs</div>
            <div class="card-value val-total">{total_cnpjs:,}</div>
            <div class="card-sub">Registros filtrados</div>
        </div>
    """, unsafe_allow_html=True)

with col_c2:
    st.markdown(f"""
        <div class="metric-card card-pendente">
            <div class="card-title">Pendentes</div>
            <div class="card-value val-pendente">{qtd_pendentes:,}</div>
            <div class="card-sub">{pct_pendente:.1f}% do total</div>
        </div>
    """, unsafe_allow_html=True)

with col_c3:
    st.markdown(f"""
        <div class="metric-card card-negado">
            <div class="card-title">Negado Operação</div>
            <div class="card-value val-negado">{qtd_negado:,}</div>
            <div class="card-sub">{pct_negado:.1f}% do total</div>
        </div>
    """, unsafe_allow_html=True)

with col_c4:
    st.markdown(f"""
        <div class="metric-card card-agendado">
            <div class="card-title">Agendados</div>
            <div class="card-value val-agendado">{qtd_agendados:,}</div>
            <div class="card-sub">{pct_agendado:.1f}% do total</div>
        </div>
    """, unsafe_allow_html=True)

with col_c5:
    st.markdown(f"""
        <div class="metric-card card-tratado">
            <div class="card-title">Tratados</div>
            <div class="card-value val-tratado">{qtd_tratados:,}</div>
            <div class="card-sub">{pct_tratado:.1f}% do total</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# CONSULTA PAGINADA DA TABELA
# ==========================================
query_dados = f"""
    SELECT 
        cnpj_formatado, razao_social, nome_fantasia, porte_empresa,
        COALESCE(responsavel_tratamento, '') AS responsavel_tratamento, 
        status_followup, cep, bairro, logradouro, numero,
        COALESCE(ddd1, '') AS ddd1, COALESCE(telefone1, '') AS telefone1,
        correio_eletronico, observacoes
    FROM empresas {sql_where}
    ORDER BY cnpj_formatado
    LIMIT {registros_por_pagina} OFFSET {offset_val}
"""

df_tabela = pd.read_sql(text(query_dados), engine, params=params)

# Formata telefone completo com DDD
df_tabela['ddd1'] = df_tabela['ddd1'].astype(str).str.strip().str.replace('.0', '', regex=False)
df_tabela['telefone1'] = df_tabela['telefone1'].astype(str).str.strip().str.replace('.0', '', regex=False)

def formatar_telefone(row):
    ddd = row['ddd1']
    tel = row['telefone1']
    if ddd and tel and ddd not in ['nan', 'None'] and tel not in ['nan', 'None']:
        return f"({ddd}) {tel}"
    elif tel and tel not in ['nan', 'None']:
        return tel
    return ""

df_tabela['telefone_completo'] = df_tabela.apply(formatar_telefone, axis=1)

# ==========================================
# JANELA MODAL DE TRATAMENTO / FOLLOW-UP
# ==========================================
@st.dialog("📝 Atualizar Follow-up / Tratamento de Empresa")
def abrir_modal_tratamento(cnpj):
    query_emp = "SELECT * FROM empresas WHERE cnpj_formatado = :cnpj"
    row = pd.read_sql(text(query_emp), engine, params={"cnpj": cnpj}).iloc[0]
    
    ddd = str(row.get('ddd1', '')).replace('.0', '').strip()
    tel = str(row.get('telefone1', '')).replace('.0', '').strip()
    tel_fmt = f"({ddd}) {tel}" if ddd and tel else tel
    
    st.markdown(f"**Empresa:** {row['razao_social']}")
    st.markdown(f"**CNPJ:** `{row['cnpj_formatado']}` | **CEP:** `{row['cep']}` | **Telefone:** `{tel_fmt}`")
    st.markdown("---")
    
    with st.form("form_tratamento_modal"):
        resp_atual = st.text_input("👤 Responsável pelo Tratamento:", value=row.get('responsavel_tratamento', '') or '')
        
        status_opcoes = ["Pendente", "Negado Operacao", "Agendado", "Tratado", "Sem Interesse", "Em Contato"]
        idx_status = status_opcoes.index(row['status_followup']) if row['status_followup'] in status_opcoes else 0
        status_novo = st.selectbox("📌 Status do Follow-up:", options=status_opcoes, index=idx_status)
        
        obs_nova = st.text_area("💬 Observações do Atendimento:", value=row.get('observacoes', '') or '', height=120)
        
        btn_salvar = st.form_submit_button("💾 Salvar Tratamento", use_container_width=True)
        
        if btn_salvar:
            with engine.begin() as conn:
                conn.execute(text("""
                    UPDATE empresas 
                    SET responsavel_tratamento = :resp,
                        status_followup = :stat,
                        observacoes = :obs
                    WHERE cnpj_formatado = :cnpj
                """), {"resp": resp_atual, "stat": status_novo, "obs": obs_nova, "cnpj": cnpj})
            st.success("✅ Follow-up salvo com sucesso!")
            st.rerun()

# ==========================================
# SEÇÃO DA TABELA E ABERTURA DE MODAL
# ==========================================
col_t1, col_t2 = st.columns([3, 1])

with col_t1:
    st.subheader(f"📋 Relação de Empresas ({total_cnpjs:,} localizadas)")

with col_t2:
    # Botão para exportação em CSV (semelhante ao Exportar da imagem)
    if not df_tabela.empty:
        csv_data = df_tabela.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Exportar Dados (CSV)",
            data=csv_data,
            file_name="empresas_filtradas.csv",
            mime="text/csv",
            use_container_width=True
        )

if df_tabela.empty:
    st.info("Nenhuma empresa encontrada com os parâmetros informados.")
else:
    # Abertura de tratamento por linha
    col_act1, col_act2 = st.columns([3, 1])
    with col_act1:
        empresa_para_tratar = st.selectbox(
            "⚡ Selecione a empresa que deseja tratar:",
            options=["-- Selecione uma empresa --"] + df_tabela['cnpj_formatado'].tolist(),
            format_func=lambda x: f"{x} - {df_tabela[df_tabela['cnpj_formatado']==x]['razao_social'].values[0]}" if x != "-- Selecione uma empresa --" else x
        )
    with col_act2:
        st.write(" ")
        st.write(" ")
        if empresa_para_tratar != "-- Selecione uma empresa --":
            if st.button("✏️ Abrir Tratamento", use_container_width=True):
                abrir_modal_tratamento(empresa_para_tratar)

    colunas_exibicao = [
        'cnpj_formatado', 'razao_social', 'nome_fantasia', 'porte_empresa',
        'responsavel_tratamento', 'status_followup', 'cep', 'bairro',
        'logradouro', 'numero', 'telefone_completo', 'correio_eletronico', 'observacoes'
    ]

    st.dataframe(
        df_tabela[colunas_exibicao],
        column_config={
            "cnpj_formatado": "CNPJ",
            "razao_social": "Razão Social",
            "nome_fantasia": "Nome Fantasia",
            "porte_empresa": "Porte",
            "responsavel_tratamento": "Tratado Por",
            "status_followup": "Status",
            "cep": "CEP",
            "bairro": "Bairro",
            "logradouro": "Logradouro",
            "numero": "Nº",
            "telefone_completo": "Telefone com DDD",
            "correio_eletronico": "E-mail",
            "observacoes": "Observações do Follow-up"
        },
        hide_index=True,
        use_container_width=True
    )

    total_paginas = (total_cnpjs // registros_por_pagina) + (1 if total_cnpjs % registros_por_pagina > 0 else 0)
    st.caption(f"Página {pagina_atual} de {total_paginas} • Exibindo {len(df_tabela)} registros nesta página.")

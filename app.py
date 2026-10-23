import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# ==========================================
# CONFIGURAÇÃO DA PÁGINA STREAMLIT
# ==========================================
st.set_page_config(
    page_title="Gestão e Prospecção de CNPJs",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URI de Conexão com o NeonDB
POSTGRES_URI = "postgresql+psycopg2://neondb_owner:npg_bNDxjo9L2giC@ep-empty-hall-b4zx7bew-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require"

@st.cache_resource
def get_db_engine():
    return create_engine(POSTGRES_URI, pool_pre_ping=True)

engine = get_db_engine()

# Estilização dos Cards do Dashboard
st.markdown("""
    <style>
    .metric-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-top: 4px solid #6c757d;
        margin-bottom: 15px;
    }
    .card-total { border-top-color: #2b3a4a; }
    .card-pendente { border-top-color: #d9534f; }
    .card-negado { border-top-color: #c9302c; }
    .card-agendado { border-top-color: #337ab7; }
    .card-tratado { border-top-color: #1a8a59; }
    
    .card-title {
        font-size: 13px;
        font-weight: 700;
        color: #4a5568;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .card-value {
        font-size: 32px;
        font-weight: 800;
        margin-bottom: 2px;
    }
    .val-total { color: #1a202c; }
    .val-pendente { color: #d9534f; }
    .val-negado { color: #c9302c; }
    .val-agendado { color: #337ab7; }
    .val-tratado { color: #1a8a59; }

    .card-sub {
        font-size: 11px;
        color: #718096;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Painel de Prospecção e Controle de Carteira")

# ==========================================
# PAINEL LATERAL DE FILTROS
# ==========================================
st.sidebar.header("🔍 Filtros de Seleção")

busca_responsavel = st.sidebar.text_input("👤 Responsável pelo Tratamento:", "").strip()

lista_status = ["Pendente", "Negado Operacao", "Agendado", "Tratado", "Sem Interesse", "Em Contato"]
filtro_status = st.sidebar.multiselect("📌 Status do Follow-up:", options=lista_status, default=[])

busca_bairro = st.sidebar.text_input("🏘️ Bairro (ou parte dele):", "").strip().upper()
busca_cep = st.sidebar.text_input("📮 CEP (ou parte dele):", "").strip()

lista_portes = ["Micro Empresa (ME)", "Empresa de Pequeno Porte (EPP)", "Demais (Médio/Grande Porte)", "Não Informado"]
filtro_porte = st.sidebar.multiselect("🏢 Porte da Empresa:", options=lista_portes, default=[])

busca_texto = st.sidebar.text_input("🔍 Buscar por Razão Social ou CNPJ:", "").strip().upper()

# Controles de Paginação
registros_por_pagina = 100
pagina_atual = st.sidebar.number_input("📄 Página:", min_value=1, value=1, step=1)
offset_val = (pagina_atual - 1) * registros_por_pagina

# ==========================================
# CONSTRUÇÃO DA CONSULTA SQL DINÂMICA
# ==========================================
where_clauses = ["1=1"]
params = {}

if busca_responsavel:
    where_clauses.append("responsavel_tratamento ILIKE :resp")
    params["resp"] = f"%{busca_responsavel}%"

if filtro_status:
    where_clauses.append("status_followup IN :status_list")
    params["status_list"] = tuple(filtro_status)

if busca_bairro:
    where_clauses.append("bairro ILIKE :bairro")
    params["bairro"] = f"%{busca_bairro}%"

if busca_cep:
    where_clauses.append("cep LIKE :cep")
    params["cep"] = f"%{busca_cep}%"

if filtro_porte:
    where_clauses.append("porte_empresa IN :portes")
    params["portes"] = tuple(filtro_porte)

if busca_texto:
    where_clauses.append("(razao_social ILIKE :texto OR cnpj_formatado LIKE :texto)")
    params["texto"] = f"%{busca_texto}%"

sql_where = " WHERE " + " AND ".join(where_clauses)

# Executa consulta leve de KPIs agregados diretamente no PostgreSQL
query_kpis = f"""
    SELECT 
        COUNT(*) AS total,
        COUNT(*) FILTER (WHERE status_followup = 'Pendente') AS pendentes,
        COUNT(*) FILTER (WHERE status_followup = 'Negado Operacao') AS negados,
        COUNT(*) FILTER (WHERE status_followup = 'Agendado') AS agendados,
        COUNT(*) FILTER (WHERE status_followup = 'Tratado') AS tratados
    FROM empresas {sql_where}
"""

try:
    with engine.connect() as conn:
        kpi_res = conn.execute(text(query_kpis), params).fetchone()
except Exception as e:
    st.error(f"Erro de conexão com o banco de dados: {e}")
    st.stop()

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
# DASHBOARD DE INDICADORES
# ==========================================
st.markdown("##### Indicadores dos filtros • Categorias separadas por equipe e Status")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
        <div class="metric-card card-total">
            <div class="card-title">Total de CNPJs</div>
            <div class="card-value val-total">{total_cnpjs:,}</div>
            <div class="card-sub">Registros distintos</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class="metric-card card-pendente">
            <div class="card-title">Pendentes</div>
            <div class="card-value val-pendente">{qtd_pendentes:,}</div>
            <div class="card-sub">{pct_pendente:.1f}% do total</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class="metric-card card-negado">
            <div class="card-title">Negado Operação</div>
            <div class="card-value val-negado">{qtd_negado:,}</div>
            <div class="card-sub">{pct_negado:.1f}% do total</div>
        </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
        <div class="metric-card card-agendado">
            <div class="card-title">Agendados</div>
            <div class="card-value val-agendado">{qtd_agendados:,}</div>
            <div class="card-sub">{pct_agendado:.1f}% do total</div>
        </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
        <div class="metric-card card-tratado">
            <div class="card-title">Tratados</div>
            <div class="card-value val-tratado">{qtd_tratados:,}</div>
            <div class="card-sub">{pct_tratado:.1f}% do total</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# CONSULTA PAGINADA
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

# Formatação de telefone
df_tabela['ddd1'] = df_tabela['ddd1'].astype(str).str.strip().str.replace('.0', '', regex=False)
df_tabela['telefone1'] = df_tabela['telefone1'].astype(str).str.strip().str.replace('.0', '', regex=False)

def formatar_telefone(row):
    ddd = row['ddd1']
    tel = row['telefone1']
    if ddd and tel and ddd != 'nan' and tel != 'nan' and ddd != 'None' and tel != 'None':
        return f"({ddd}) {tel}"
    elif tel and tel != 'nan' and tel != 'None':
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
        
        idx_status = lista_status.index(row['status_followup']) if row['status_followup'] in lista_status else 0
        status_novo = st.selectbox("📌 Status do Follow-up:", options=lista_status, index=idx_status)
        
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
# TABELA PRINCIPAL COM BOTÃO DE ABRIR MODAL
# ==========================================
st.subheader("📋 Relação de Empresas Filtradas")

if df_tabela.empty:
    st.info("Nenhuma empresa encontrada com os filtros selecionados.")
else:
    col_sel1, col_sel2 = st.columns([3, 1])

    with col_sel1:
        empresa_para_tratar = st.selectbox(
            "⚡ Clique para selecionar a empresa que deseja tratar:",
            options=["-- Selecione uma empresa para tratar --"] + df_tabela['cnpj_formatado'].tolist(),
            format_func=lambda x: f"{x} - {df_tabela[df_tabela['cnpj_formatado']==x]['razao_social'].values[0]}" if x != "-- Selecione uma empresa para tratar --" else x
        )

    with col_sel2:
        st.write(" ")
        st.write(" ")
        if empresa_para_tratar != "-- Selecione uma empresa para tratar --":
            if st.button("✏️ Abrir Janela de Tratamento", use_container_width=True):
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
    st.caption(f"Exibindo página {pagina_atual} de {total_paginas} (Mostrando {len(df_tabela)} registros nesta página de um total de {total_cnpjs:,} encontrados no banco).")

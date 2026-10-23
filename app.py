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

# Garante a estrutura completa de colunas no NeonDB
def inicializar_estrutura_crm():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS empresas (
                cnpj_formatado VARCHAR PRIMARY KEY,
                razao_social VARCHAR, nome_fantasia VARCHAR, porte_empresa VARCHAR, situacao_cadastral VARCHAR,
                matriz_filial VARCHAR, uf VARCHAR, municipio VARCHAR, cnae_principal VARCHAR, data_inicio_atividade VARCHAR,
                correio_eletronico VARCHAR, telefone1 VARCHAR, motivo_situacao VARCHAR, data_situacao VARCHAR,
                cidade_exterior VARCHAR, pais VARCHAR, cnae_secundario VARCHAR, tipo_logradouro VARCHAR, logradouro VARCHAR,
                numero VARCHAR, complemento VARCHAR, bairro VARCHAR, cep VARCHAR, ddd1 VARCHAR, ddd2 VARCHAR, telefone2 VARCHAR,
                ddd_fax VARCHAR, fax VARCHAR, situacao_especial VARCHAR, data_situacao_especial VARCHAR, capital_social VARCHAR,
                status_followup VARCHAR DEFAULT 'Pendente',
                observacoes TEXT DEFAULT '',
                responsavel_tratamento VARCHAR DEFAULT ''
            );
        """))
        conn.execute(text("ALTER TABLE empresas ADD COLUMN IF NOT EXISTS responsavel_tratamento VARCHAR DEFAULT '';"))

inicializar_estrutura_crm()

# Carrega os dados do banco
@st.cache_data(ttl=60)
def carregar_dados_empresas():
    query = """
        SELECT 
            cnpj_formatado, razao_social, nome_fantasia, porte_empresa, situacao_cadastral,
            matriz_filial, uf, municipio, cnae_principal, data_inicio_atividade,
            correio_eletronico, telefone1, bairro, cep, logradouro, numero, complemento,
            capital_social, status_followup, observacoes, COALESCE(responsavel_tratamento, '') AS responsavel_tratamento
        FROM empresas
    """
    return pd.read_sql(query, engine)

df_raw = carregar_dados_empresas()

# Estilização dos Cards do Dashboard (Estilo da Imagem)
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

if df_raw.empty:
    st.warning("⚠️ Nenhuma empresa encontrada no banco de dados NeonDB. Execute a carga inicial no servidor.")
    st.stop()

# ==========================================
# PAINEL LATERAL DE FILTROS
# ==========================================
st.sidebar.header("🔍 Filtros de Seleção")

# Filtro por Responsável pelo Tratamento
lista_responsaveis = sorted([r for r in df_raw['responsavel_tratamento'].unique() if r])
lista_responsaveis.insert(0, "Sem Responsável (NÃO ATRIBUÍDO)")

filtro_responsavel = st.sidebar.multiselect(
    "👤 Responsável pelo Tratamento:",
    options=lista_responsaveis,
    default=[]
)

# Filtro por Status de Follow-up
lista_status = ["Pendente", "Negado Operacao", "Agendado", "Tratado", "Sem Interesse", "Em Contato"]
filtro_status = st.sidebar.multiselect("📌 Status do Follow-up:", options=lista_status, default=[])

# Filtro por Bairro
lista_bairros = sorted([b for b in df_raw['bairro'].dropna().unique() if b])
filtro_bairro = st.sidebar.multiselect("🏘️ Bairro:", options=lista_bairros, default=[])

# Filtro por CEP
busca_cep = st.sidebar.text_input("📮 CEP (ou parte dele):", "").strip()

# Filtro por Porte
lista_portes = sorted([p for p in df_raw['porte_empresa'].dropna().unique() if p])
filtro_porte = st.sidebar.multiselect("🏢 Porte da Empresa:", options=lista_portes, default=[])

# Busca textual por Razão Social ou CNPJ
busca_texto = st.sidebar.text_input("🔍 Buscar por Razão Social ou CNPJ:", "").strip().upper()

# Limite de exibição
limite_linhas = st.sidebar.slider("🔢 Limite de exibição:", min_value=100, max_value=20000, value=2000, step=100)

# ==========================================
# APLICAÇÃO DOS FILTROS
# ==========================================
df_filtrado = df_raw.copy()

if filtro_responsavel:
    condicoes_resp = []
    if "Sem Responsável (NÃO ATRIBUÍDO)" in filtro_responsavel:
        condicoes_resp.append(df_filtrado['responsavel_tratamento'] == '')
    responsaveis_nominais = [r for r in filtro_responsavel if r != "Sem Responsável (NÃO ATRIBUÍDO)"]
    if responsaveis_nominais:
        condicoes_resp.append(df_filtrado['responsavel_tratamento'].isin(responsaveis_nominais))
    
    mask_final = condicoes_resp[0]
    for cond in condicoes_resp[1:]:
        mask_final = mask_final | cond
    df_filtrado = df_filtrado[mask_final]

if filtro_status:
    df_filtrado = df_filtrado[df_filtrado['status_followup'].isin(filtro_status)]

if filtro_bairro:
    df_filtrado = df_filtrado[df_filtrado['bairro'].isin(filtro_bairro)]

if busca_cep:
    df_filtrado = df_filtrado[df_filtrado['cep'].astype(str).str.contains(busca_cep, na=False)]

if filtro_porte:
    df_filtrado = df_filtrado[df_filtrado['porte_empresa'].isin(filtro_porte)]

if busca_texto:
    df_filtrado = df_filtrado[
        df_filtrado['razao_social'].astype(str).str.contains(busca_texto, na=False) |
        df_filtrado['cnpj_formatado'].astype(str).str.contains(busca_texto, na=False)
    ]

# ==========================================
# DASHBOARD DE INDICADORES (CONFORME A IMAGEM)
# ==========================================
st.markdown("##### Indicadores dos filtros • Categorias separadas por equipe e Status")

total_cnpjs = len(df_filtrado)
qtd_pendentes = len(df_filtrado[df_filtrado['status_followup'] == 'Pendente'])
qtd_negado = len(df_filtrado[df_filtrado['status_followup'] == 'Negado Operacao'])
qtd_agendados = len(df_filtrado[df_filtrado['status_followup'] == 'Agendado'])
qtd_tratados = len(df_filtrado[df_filtrado['status_followup'] == 'Tratado'])

pct_pendente = (qtd_pendentes / total_cnpjs * 100) if total_cnpjs > 0 else 0.0
pct_negado = (qtd_negado / total_cnpjs * 100) if total_cnpjs > 0 else 0.0
pct_agendado = (qtd_agendados / total_cnpjs * 100) if total_cnpjs > 0 else 0.0
pct_tratado = (qtd_tratados / total_cnpjs * 100) if total_cnpjs > 0 else 0.0

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
# JANELA MODAL DE TRATAMENTO / FOLLOW-UP (POP-UP)
# ==========================================
@st.dialog("📝 Atualizar Follow-up / Tratamento de Empresa")
def abrir_modal_tratamento(cnpj):
    row = df_raw[df_raw['cnpj_formatado'] == cnpj].iloc[0]
    
    st.markdown(f"**Empresa:** {row['razao_social']}")
    st.markdown(f"**CNPJ:** `{row['cnpj_formatado']}` | **CEP:** `{row['cep']}` | **Telefone:** `{row['telefone1']}`")
    st.markdown("---")
    
    with st.form("form_tratamento_modal"):
        resp_atual = st.text_input("👤 Responsável pelo Tratamento:", value=row['responsavel_tratamento'])
        
        idx_status = lista_status.index(row['status_followup']) if row['status_followup'] in lista_status else 0
        status_novo = st.selectbox("📌 Status do Follow-up:", options=lista_status, index=idx_status)
        
        obs_nova = st.text_area("💬 Observações do Atendimento:", value=row['observacoes'], height=120)
        
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
            st.cache_data.clear()
            st.rerun()

# ==========================================
# TABELA PRINCIPAL COM BOTÃO DE ABRIR MODAL
# ==========================================
st.subheader("📋 Relação de Empresas Filtradas")

df_tabela = df_filtrado.head(limite_linhas).copy()

# Seletor rápido para abrir a janela de tratamento
col_sel1, col_sel2 = st.columns([3, 1])

with col_sel1:
    empresa_para_tratar = st.selectbox(
        "⚡ Clique ou busque a empresa para abrir a janela de tratamento:",
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
    'logradouro', 'numero', 'telefone1', 'correio_eletronico', 'observacoes'
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
        "telefone1": "Telefone",
        "correio_eletronico": "E-mail",
        "observacoes": "Observações do Follow-up"
    },
    hide_index=True,
    use_container_width=True
)

st.caption(f"Exibindo os primeiros {len(df_tabela)} registros de {len(df_filtrado)} encontrados.")

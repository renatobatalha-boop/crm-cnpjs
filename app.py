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

# Garante que as colunas de CRM existam no NeonDB
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

# Carrega os dados brutos filtrados do banco na nuvem
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
    df = pd.read_sql(query, engine)
    return df

df_raw = carregar_dados_empresas()

# Estilização CSS para recriar os Cards de Indicadores da Imagem
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
    st.warning("⚠️ Nenhuma empresa encontrada no banco de dados NeonDB. Por favor, execute a carga inicial primeiro.")
    st.stop()

# ==========================================
# PAINEL LATERAL DE FILTROS
# ==========================================
st.sidebar.header("🔍 Filtros de Seleção")

# Filtro por Responsável do Tratamento
lista_responsaveis = sorted([r for r in df_raw['responsavel_tratamento'].unique() if r])
lista_responsaveis.insert(0, "Sem Responsável (NÃO ATRIBUÍDO)")

filtro_responsavel = st.sidebar.multiselect(
    "👤 Responsável pelo Tratamento:",
    options=lista_responsaveis,
    default=[]
)

# Filtro por Status de Follow-up
lista_status = ["Pendente", "Negado Operacao", "Agendado", "Tratado", "Sem Interesse", "Em Contato"]
filtro_status = st.sidebar.multiselect(
    "📌 Status do Follow-up:",
    options=lista_status,
    default=[]
)

# Filtro por Bairro
lista_bairros = sorted([b for b in df_raw['bairro'].dropna().unique() if b])
filtro_bairro = st.sidebar.multiselect("🏘️ Bairro:", options=lista_bairros, default=[])

# Filtro por CEP
busca_cep = st.sidebar.text_input("📮 CEP (ou parte dele):", "").strip()

# Filtro por Porte de Empresa
lista_portes = sorted([p for p in df_raw['porte_empresa'].dropna().unique() if p])
filtro_porte = st.sidebar.multiselect("🏢 Porte da Empresa:", options=lista_portes, default=[])

# Busca textual por Razão Social ou CNPJ
busca_texto = st.sidebar.text_input("🔍 Buscar por Razão Social ou CNPJ:", "").strip().upper()

# Limite de exibição para navegação fluida
limite_linhas = st.sidebar.slider("🔢 Limite de exibição na tabela:", min_value=100, max_value=20000, value=2000, step=100)

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
    
    # Combina as opções de filtro selecionadas
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
# PAINEL DE ATUALIZAÇÃO / TRATAMENTO DE REGISTRO
# ==========================================
with st.expander("📝 Atualizar Tratamento / Responsável de um CNPJ", expanded=False):
    col_cnp1, col_cnp2, col_cnp3 = st.columns([2, 2, 2])
    
    with col_cnp1:
        cnpj_selecionado = st.selectbox(
            "Selecione o CNPJ para atualizar:",
            options=df_filtrado['cnpj_formatado'].head(500).tolist()
        )
    
    if cnpj_selecionado:
        row_curr = df_filtrado[df_filtrado['cnpj_formatado'] == cnpj_selecionado].iloc[0]
        
        with col_cnp2:
            novo_resp = st.text_input("Responsável pelo Tratamento:", value=row_curr['responsavel_tratamento'])
        
        with col_cnp3:
            novo_status = st.selectbox(
                "Novo Status:",
                options=lista_status,
                index=lista_status.index(row_curr['status_followup']) if row_curr['status_followup'] in lista_status else 0
            )
            
        novas_obs = st.text_area("Observações do Atendimento:", value=row_curr['observacoes'])
        
        if st.button("💾 Salvar Alterações no Banco"):
            with engine.begin() as conn:
                conn.execute(text("""
                    UPDATE empresas 
                    SET responsavel_tratamento = :resp,
                        status_followup = :stat,
                        observacoes = :obs
                    WHERE cnpj_formatado = :cnpj
                """), {"resp": novo_resp, "stat": novo_status, "obs": novas_obs, "cnpj": cnpj_selecionado})
            st.success(f"✅ Tratamento atualizado com sucesso para {cnpj_selecionado}!")
            st.cache_data.clear()
            st.rerun()

# ==========================================
# TABELA PRINCIPAL DE DADOS COM CEP E RESPONSÁVEL
# ==========================================
st.subheader("📋 Relação de Empresas Filtradas")

colunas_exibicao = [
    'cnpj_formatado', 'razao_social', 'nome_fantasia', 'porte_empresa',
    'responsavel_tratamento', 'status_followup', 'cep', 'bairro',
    'logradouro', 'numero', 'telefone1', 'correio_eletronico', 'observacoes'
]

df_tabela = df_filtrado[colunas_exibicao].head(limite_linhas)

st.dataframe(
    df_tabela,
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

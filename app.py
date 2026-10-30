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
# Dica de segurança: Configure 'st.secrets["POSTGRES_URI"]' no Streamlit Cloud
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
# FUNÇÃO DE FORMATAÇÃO NUMÉRICA (PADRÃO BR)
# ==========================================
def fmt_num(val):
    if val is None:
        return "0"
    return f"{int(val):,}".replace(",", ".")

# ==========================================
# ESTILIZAÇÃO CSS CUSTOMIZADA
# ==========================================
st.markdown("""
    <style>
    header {visibility: hidden;}
    [data-testid="collapsedControl"] {display: none;}
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
    .card-nao-contatado { border-top-color: #64748b; }
    .card-contatado { border-top-color: #0284c7; }
    .card-futuro { border-top-color: #eab308; }
    .card-convertido { border-top-color: #16a34a; }
    .card-ativo { border-top-color: #10b981; }
    .card-negado { border-top-color: #dc2626; }

    .card-title {
        font-size: 11px;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }
    .card-value {
        font-size: 22px;
        font-weight: 800;
        margin: 4px 0;
    }
    .val-total { color: #4A154B; }
    .val-nao-contatado { color: #64748b; }
    .val-contatado { color: #0284c7; }
    .val-futuro { color: #ca8a04; }
    .val-convertido { color: #16a34a; }
    .val-ativo { color: #10b981; }
    .val-negado { color: #dc2626; }

    .card-sub {
        font-size: 11px;
        color: #94a3b8;
    }
    </style>
""", unsafe_allow_html=True)

# Topo Corporativo
st.markdown("""
    <div class="top-header">
        <div class="top-title">
            <span>🏛️ PROSPECÇÃO DE CNPJs</span>
            <span style="font-size: 15px; font-weight: 400; opacity: 0.85;">| Base Operacional de Leads</span>
        </div>
        <div style="display: flex; gap: 10px; align-items: center;">
            <span class="badge-user">Operação Ativa</span>
            <span style="font-size: 13px; opacity: 0.9;">Equipe Comercial</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# LISTA OFICIAL DE STATUS
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

# Consulta de KPIs com a nova taxonomia
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
# CARDS DE INDICADORES
# ==========================================
c_t, c_nc, c_c, c_cf, c_conv, c_pa, c_pn = st.columns(7)

with c_t:
    st.markdown(f"""
        <div class="metric-card card-total">
            <div class="card-title">Total Base</div>
            <div class="card-value val-total">{fmt_num(total_cnpjs)}</div>
            <div class="card-sub">CNPJs Filtrados</div>
        </div>
    """, unsafe_allow_html=True)

with c_nc:
    st.markdown(f"""
        <div class="metric-card card-nao-contatado">
            <div class="card-title">Não Contatados</div>
            <div class="card-value val-nao-contatado">{fmt_num(qtd_nao_contatados)}</div>
            <div class="card-sub">{pct(qtd_nao_contatados):.1f}% do total</div>
        </div>
    """, unsafe_allow_html=True)

with c_c:
    st.markdown(f"""
        <div class="metric-card card-contatado">
            <div class="card-title">Contatados</div>
            <div class="card-value val-contatado">{fmt_num(qtd_contatados)}</div>
            <div class="card-sub">{pct(qtd_contatados):.1f}% do total</div>
        </div>
    """, unsafe_allow_html=True)

with c_cf:
    st.markdown(f"""
        <div class="metric-card card-futuro">
            <div class="card-title">Contato Futuro</div>
            <div class="card-value val-futuro">{fmt_num(qtd_futuros)}</div>
            <div class="card-sub">{pct(qtd_futuros):.1f}% do total</div>
        </div>
    """, unsafe_allow_html=True)

with c_conv:
    st.markdown(f"""
        <div class="metric-card card-convertido">
            <div class="card-title">Convertidos</div>
            <div class="card-value val-convertido">{fmt_num(qtd_convertidos)}</div>
            <div class="card-sub">{pct(qtd_convertidos):.1f}% do total</div>
        </div>
    """, unsafe_allow_html=True)

with c_pa:
    st.markdown(f"""
        <div class="metric-card card-ativo">
            <div class="card-title">Parceiro Ativo</div>
            <div class="card-value val-ativo">{fmt_num(qtd_ativos)}</div>
            <div class="card-sub">{pct(qtd_ativos):.1f}% do total</div>
        </div>
    """, unsafe_allow_html=True)

with c_pn:
    st.markdown(f"""
        <div class="metric-card card-negado">
            <div class="card-title">Proposta Negada</div>
            <div class="card-value val-negado">{fmt_num(qtd_negados)}</div>
            <div class="card-sub">{pct(qtd_negados):.1f}% do total</div>
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
    df_tabela['correio_eletronico'] = df_tabela['correio_eletronico'].apply(lambda x: x if x and str(x).strip() not in ['nan', 'None', ''] else "Não informado")
else:
    df_tabela['telefone_completo'] = []

# ==========================================
# JANELA MODAL DE TRATAMENTO / FOLLOW-UP
# ==========================================
@st.dialog("📝 Atualizar Follow-up da Empresa", width="large")
def abrir_modal_tratamento(cnpj):
    query_emp = "SELECT * FROM empresas WHERE cnpj_formatado = :cnpj"
    res_df = pd.read_sql(text(query_emp), engine, params={"cnpj": cnpj})
    
    if res_df.empty:
        st.error("Empresa não encontrada.")
        return

    row = res_df.iloc[0]
    
    ddd = str(row.get('ddd1', '')).replace('.0', '').strip()
    tel = str(row.get('telefone1', '')).replace('.0', '').strip()
    tel_fmt = f"({ddd}) {tel}" if ddd and tel and ddd not in ['nan', 'None'] else (tel or "Não informado")
    email_fmt = row.get('correio_eletronico') or "Não informado"
    nome_exibicao = row.get('nome_fantasia') if row.get('nome_fantasia') and str(row.get('nome_fantasia')).strip() not in ['nan', 'None', ''] else row.get('razao_social')

    # Cartão de Informações Básicas da Empresa
    st.markdown(f"""
        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; margin-bottom: 15px;">
            <div style="font-size: 16px; font-weight: 700; color: #1e293b; margin-bottom: 6px;">🏢 {nome_exibicao}</div>
            <div style="font-size: 13px; color: #475569; display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                <div><b>Razão Social:</b> {row.get('razao_social', '-')}</div>
                <div><b>CNPJ:</b> <code>{row.get('cnpj_formatado', '-')}</code></div>
                <div><b>Porte:</b> {row.get('porte_empresa', 'Não Informado')}</div>
                <div><b>Telefone:</b> {tel_fmt}</div>
                <div style="grid-column: span 2;"><b>E-mail:</b> {email_fmt}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("##### Ação de Atendimento")
    
    status_banco = row.get('status_followup', '')
    idx_status = STATUS_OFICIAIS.index(status_banco) if status_banco in STATUS_OFICIAIS else 0

    # Usamos session_state para permitir renderização reativa do campo de Ticket
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
            # Se for convertido e preencheu ticket, garante o registro na observação
            obs_final = obs_nova
            if status_selecionado == "Lead Convertido" and ticket_conversao.strip():
                registro_ticket = f"[TICKET: {ticket_conversao.strip()}]"
                if registro_ticket not in obs_final:
                    obs_final = f"{registro_ticket} {obs_final}".strip()

            try:
                with engine.begin() as conn:
                    # Tenta atualizar com o campo ticket_conversao caso a coluna exista
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
                        # Fallback se a coluna ticket_conversao ainda não foi criada no banco
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
                st.error(f"Erro ao atualizar dados: {err}")

# ==========================================
# SEÇÃO DA TABELA
# ==========================================
st.subheader(f"📋 Relação de Empresas ({fmt_num(total_cnpjs)} CNPJs localizados)")

if df_tabela.empty:
    st.info("Nenhuma empresa encontrada com os parâmetros informados.")
else:
    colunas_exibicao = [
        'cnpj_formatado', 'razao_social', 'nome_fantasia', 'porte_empresa',
        'responsavel_tratamento', 'status_followup', 'telefone_completo', 
        'correio_eletronico', 'bairro', 'cep', 'observacoes'
    ]

    st.caption("👉 **Dica:** Clique em qualquer linha para abrir a janela de tratamento do Lead.")

    # Tabela com seleção interativa de linha
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

    # Dispara o pop-up ao clicar na linha
    if event and event.selection and event.selection.rows:
        idx_selecionado = event.selection.rows[0]
        cnpj_clicado = df_tabela.iloc[idx_selecionado]['cnpj_formatado']
        abrir_modal_tratamento(cnpj_clicado)

    total_paginas = (total_cnpjs // registros_por_pagina) + (1 if total_cnpjs % registros_por_pagina > 0 else 0)
    st.caption(f"Página {pagina_atual} de {fmt_num(total_paginas)} • Exibindo {len(df_tabela)} registros nesta página (Total: {fmt_num(total_cnpjs)} CNPJs).")

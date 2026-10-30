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
    
    /* Configuração de Largura Total e Redução de Margens Inúteis */
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

    .card-kpi {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 12px 14px;
        min-height: 95px;
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
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #64748B;
    }
    .kpi-value {
        font-size: 22px;
        font-weight: 900;
        letter-spacing: -0.5px;
        line-height: 1.1;
        margin: 4px 0;
        color: #1E293B;
    }
    .kpi-sub {
        font-size: 10px;
        font-weight: 500;
        color: #94A3B8;
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

# ==========================================
# 4. FUNÇÕES DE SUPORTE E CONSTANTES
# ==========================================
def fmt_num(val):
    if val is None:
        return "0"
    return f"{int(val):,}".replace(",", ".")

def eh_celular(numero_limpo):
    # Remove código do país se houver 55
    if len(numero_limpo) > 11 and numero_limpo.startswith('55'):
        numero_limpo = numero_limpo[2:]
    
    # Celulares no Brasil com DDD de 2 dígitos possuem 11 caracteres e o número começa com 9
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

# Lista padrão e fixa de operadores autorizados do CIEE
LISTA_OPERADORES_OFICIAIS = [
    "AGATHA CRUZ",
    "ALINE CRUZ",
    "ANY MORIMITSU",
    "BARBRA COSIELLO",
    "BRUNO SOUZA",
    "DIOGO VASCONCELOS",
    "DOUGLAS FRAGA",
    "ELAINE BORGES",
    "FABIANA LESSA MOLICA",
    "ISABELLY NOGUEIRA",
    "ITALO BERTI",
    "JEFFERSON ANDRADE",
    "LUCIANA PINA",
    "MATEUS LIMA",
    "MAYARA SOUZA",
    "RONALDO FERRAMOLA",
    "SANDRA MARA",
    "TAINA ZANELLATO",
    "THAYNA CRUZ",
    "THAYNA IBRAIM",
    "VINICIUS RODRIGUES",
    "VIVIANE VENAGLIA",
    "WILLIAM LIMA"
]

# ==========================================
# 5. MENU LATERAL (NAVEGAÇÃO)
# ==========================================
st.sidebar.image("https://portal.ciee.org.br/wp-content/themes/portal-ciee/assets/img/logo-ciee-novo.svg", width=150)
st.sidebar.markdown("### 🧭 MENU PRINCIPAL")
aba_selecionada = st.sidebar.radio(
    "Navegue pelo painel:",
    ["🔍 Prospecção de Leads", "📊 Gestão e Produtividade CIEE"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 👤 Operador Comercial")

# Seletor suspenso no menu lateral para selecionar o usuário logado
operador_logado = st.sidebar.selectbox(
    "Selecione seu nome:",
    options=LISTA_OPERADORES_OFICIAIS,
    index=1 # Default para Aline Cruz como exemplo de facilitação
)
st.session_state["usuario_ativo"] = operador_logado

st.sidebar.info(f"Conectado como:\n**{st.session_state['usuario_ativo']}**")

# ==========================================
# 6. OBTENÇÃO DA LISTA DE RESPONSÁVEIS ATIVOS DO BANCO
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
            # Retorna operadores que constam no banco + a lista estática para garantir integridade
            banco_lista = df["responsavel_tratamento"].dropna().tolist()
            return ["Todos", "Sem Responsável"] + sorted(list(set(banco_lista + LISTA_OPERADORES_OFICIAIS)))
    except Exception:
        return ["Todos", "Sem Responsável"] + LISTA_OPERADORES_OFICIAIS

lista_responsaveis_filtro = get_responsaveis_cadastrados()

# Cabeçalho Fixo do Topo
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

    # Caixa de Filtros Avançados
    with st.expander("🔍 FILTROS AVANÇADOS E PROSPECÇÃO", expanded=True):
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1:
            filtro_status_sel = st.selectbox("Status de Prospecção:", ["Todos"] + STATUS_OFICIAIS, index=0)
        with col_f2:
            filtro_responsavel_sel = st.selectbox("Responsável pelo Lead:", lista_responsaveis_filtro, index=0)
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

    # Construção da Cláusula WHERE Dinâmica
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

    # Consulta dos KPIs Gerais
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

    # Cards de Indicadores Simplificados no Topo da aba de Prospecção
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
    # MODAL DE TRATAMENTO DE LEADS (POP-UP)
    # ==========================================
    @st.dialog("📝 Tratar Prospecção Comercial", width="large")
    def abrir_modal_tratamento(cnpj):
        query_emp = "SELECT * FROM empresas WHERE cnpj_formatado = :cnpj"
        res_df = pd.read_sql(text(query_emp), engine, params={"cnpj": cnpj})
        
        if res_df.empty:
            st.error("Empresa não localizada.")
            return

        row = res_df.iloc[0]
        
        # Recuperação do CNPJ Completo (exibe no pop-up)
        cnpj_completo_exibicao = row.get('cnpj_formatado', 'Não Informado')
        
        ddd = str(row.get('ddd1', '')).replace('.0', '').strip()
        tel = str(row.get('telefone1', '')).replace('.0', '').strip()
        tel_fmt = f"({ddd}) {tel}" if ddd and tel and ddd not in ['nan', 'None'] else (tel or "Não informado")
        email_fmt = row.get('correio_eletronico') or "Não informado"
        
        nome_fantasia_val = str(row.get('nome_fantasia', '')).strip()
        nome_exibicao = nome_fantasia_val if nome_fantasia_val and nome_fantasia_val not in ['nan', 'None', ''] else row.get('razao_social', '-')

        # Dados de endereço para Georreferenciamento
        logradouro = row.get('logradouro') or ""
        numero = row.get('numero') or ""
        bairro = row.get('bairro') or ""
        cep = row.get('cep') or ""
        endereco_completo = f"{logradouro}, {numero} - {bairro}, SP, {cep}"
        maps_link = f"https://www.google.com/maps/search/?api=1&query={endereco_completo.replace(' ', '+')}"

        # Cabeçalho da Ficha com o CNPJ COMPLETO visível
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

        # Ações Rápidas (Maps & WhatsApp com validação inteligente de celular)
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            st.link_button("📍 Ver Rota no Google Maps", maps_link, use_container_width=True)
        with col_a2:
            clean_tel = "".join(filter(str.isdigit, tel_fmt))
            if clean_tel and eh_celular(clean_tel):
                # Mensagem de aproximação comercial CIEE
                msg_whats = urllib.parse.quote(f"Olá! Sou {st.session_state['usuario_ativo']} do CIEE e gostaria de falar com o responsável de RH da {nome_exibicao} sobre programas de Estágio e Aprendizagem.")
                st.link_button("💬 Abrir WhatsApp Comercial", f"https://wa.me/55{clean_tel}?text={msg_whats}", use_container_width=True)
            else:
                st.button("☎️ Contato é Telefone Fixo (WhatsApp indisponível)", disabled=True, use_container_width=True)

        st.markdown("---")
        st.markdown("##### ⚙️ Atualização de Follow-up")
        
        status_banco = row.get('status_followup', '')
        idx_status = STATUS_OFICIAIS.index(status_banco) if status_banco in STATUS_OFICIAIS else 0

        col_form_status, col_form_resp = st.columns(2)
        
        with col_form_status:
            status_selecionado = st.selectbox("📌 Novo Status:", STATUS_OFICIAIS, index=idx_status, key=f"status_{cnpj}")

        with col_form_resp:
            resp_banco = row.get('responsavel_tratamento', '') or ''
            # Se já houver responsável, pré-seleciona ele. Se não, pré-seleciona o operador ativo.
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

        # Botão de autoatribuição rápida integrado com a lista suspensa
        if st.button("🙋‍♂️ Atribuir a Mim (Preencher meu nome)", key=f"btn_me_{cnpj}"):
            st.session_state[f"resp_select_{cnpj}"] = st.session_state["usuario_ativo"]
            st.rerun()

        # Condição de Ticket de Conversão
        ticket_conversao = ""
        if status_selecionado == "Lead Convertido":
            ticket_conversao = st.text_input("🎟️ Protocolo / Ticket de Parceria CIEE:", placeholder="Ex: CIEE-SP-12345", key=f"ticket_{cnpj}")

        # Campo dinâmico para Motivo de Recusa (caso Proposta Negada)
        motivo_recusa_sel = ""
        if status_selecionado == "Proposta Negada":
            motivo_recusa_sel = st.selectbox("❌ Principal Motivo da Recusa:", MOTIVOS_RECUSA_OPCOES, key=f"recusa_{cnpj}")

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
            
            # Constrói nota estruturada com timestamp
            if nova_nota.strip():
                timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
                operador = novo_resp_selecionado or st.session_state["usuario_ativo"]
                entrada_historico = f"[{timestamp} | {operador}]: {nova_nota.strip()}"
                obs_formatada = f"{entrada_historico}\n---\n{obs_banco}".strip()

            if status_selecionado == "Lead Convertido" and ticket_conversao.strip():
                reg_ticket = f"[CONTRATO: {ticket_conversao.strip()}]"
                if reg_ticket not in obs_formatada:
                    obs_formatada = f"{reg_ticket} {obs_formatada}".strip()

            if status_selecionado == "Proposta Negada" and motivo_recusa_sel:
                reg_recusa = f"[MOTIVO NEGADO: {motivo_recusa_sel}]"
                if reg_recusa not in obs_formatada:
                    obs_formatada = f"{reg_recusa} {obs_formatada}".strip()

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
                        "obs": obs_formatada,
                        "cnpj": cnpj
                    })
                st.cache_data.clear() # Limpa o cache para recarregar o grid com os novos dados
                st.success("✅ Lead atualizado com sucesso!")
                st.rerun()
            except Exception as err:
                st.error(f"Erro ao salvar: {err}")

    # ==========================================
    # TABELA PRINCIPAL DE EMPRESAS (RELAÇÃO)
    # ==========================================
    # Query de listagem que executa a segmentação priorizando Varejo, e classifica setor Público/Privado
    query_dados = f"""
        SELECT 
            cnpj_formatado, razao_social, nome_fantasia, porte_empresa,
            COALESCE(bairro, 'Não Informado') AS bairro, cep,
            COALESCE(responsavel_tratamento, '') AS responsavel_tratamento,
            CASE 
                WHEN status_followup IN ('Lead Contatado', 'Contato Futuro', 'Lead Convertido', 'Parceiro Ativo', 'Proposta Negada') THEN status_followup
                ELSE 'Lead Não Contatado'
            END AS status_followup,
            CASE 
                WHEN razao_social ILIKE '%comercio%' OR razao_social ILIKE '%varejo%' OR nome_fantasia ILIKE '%loja%' OR nome_fantasia ILIKE '%supermercado%' THEN 'Varejo'
                ELSE 'Outros Serviços'
            END AS segmentacao,
            CASE 
                WHEN razao_social ILIKE '%publica%' OR razao_social ILIKE '%prefeitura%' OR razao_social ILIKE '%municip%' OR razao_social ILIKE '%federal%' THEN 'Público'
                ELSE 'Privado'
            END AS setor_tipo,
            COALESCE(observacoes, '') AS observacoes
        FROM empresas {sql_where}
        ORDER BY 
            CASE WHEN (razao_social ILIKE '%comercio%' OR razao_social ILIKE '%varejo%' OR nome_fantasia ILIKE '%loja%') THEN 0 ELSE 1 END,
            cnpj_formatado
        LIMIT {registros_por_pagina} OFFSET {offset_val}
    """

    df_tabela = pd.read_sql(text(query_dados), engine, params=params)

    st.markdown(f"#### 📋 Relação de Empresas ({fmt_num(total_cnpjs)} CNPJs localizados)")

    if df_tabela.empty:
        st.info("Nenhuma empresa encontrada com os parâmetros informados.")
    else:
        # Colunas com nova ordem requerida: Responsável, Status e Observações movidas para o fim da visualização
        # E-mail e Telefone totalmente retirados da tabela principal para visualização limpa
        colunas_exibicao = [
            'cnpj_formatado', 'razao_social', 'nome_fantasia', 'porte_empresa',
            'segmentacao', 'setor_tipo', 'bairro', 'cep',
            'responsavel_tratamento', 'status_followup', 'observacoes'
        ]

        st.caption("👉 **Clique na linha da empresa** para abrir a ficha completa do Lead e atualizar interações.")

        event = st.dataframe(
            df_tabela[colunas_exibicao],
            column_config={
                "cnpj_formatado": "CNPJ",
                "razao_social": "Razão Social",
                "nome_fantasia": "Nome Fantasia",
                "porte_empresa": "Porte",
                "segmentacao": "Segmentação",
                "setor_tipo": "Tipo de Setor",
                "bairro": "Bairro/Região",
                "cep": "CEP",
                "responsavel_tratamento": "Responsável",
                "status_followup": "Status",
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

# ==========================================
# ABA 2: GESTÃO E PRODUTIVIDADE CIEE
# ==========================================
else:
    st.markdown("### 📊 Indicadores de Performance & Produtividade")
    st.markdown("---")

    # Coleta de dados agregados do banco de dados para os rankings de gestão
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
            # Consolidação dos rankings comerciais de contatos efetuados vs conversões
            df_ranking = df_gestao.groupby("Responsável").agg(
                Total_Leads_Trabalhados=("total", "sum"),
                Conversoes_Efetivas=("total", lambda x: sum(df_gestao.loc[x.index, "total"][df_gestao.loc[x.index, "status_followup"].isin(["Lead Convertido", "Parceiro Ativo"])]))
            ).reset_index().sort_values(by="Conversoes_Efetivas", ascending=False)
            
            st.dataframe(df_ranking, hide_index=True, use_container_width=True)
        else:
            st.info("Nenhum dado comercial disponível no momento.")

    with col_g2:
        st.markdown("#### ❌ Principais Recusas de Clientes CIEE")
        # Analisa os motivos de recusa registrados nas observações da base
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
    # Gráfico de produtividade nativo
    query_total_status = "SELECT status_followup, COUNT(*) as qtd FROM empresas WHERE status_followup IS NOT NULL GROUP BY 1"
    try:
        df_status = pd.read_sql(text(query_total_status), engine)
        if not df_status.empty:
            st.bar_chart(df_status.set_index("status_followup"), color="#005CB9")
        else:
            st.caption("Sem dados de interações cadastrados na base.")
    except Exception:
        st.caption("Aguardando novas interações para renderização do gráfico.")

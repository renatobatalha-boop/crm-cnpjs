import streamlit as st
import pandas as pd
import requests
import psycopg2

st.set_page_config(page_title="CRM de CNPJs - Acesso Equipe", layout="wide")

# ==========================================
# 1. AUTENTICAÇÃO SIMPLES (LOGIN & SENHA)
# ==========================================
USUARIO_CORRETO = st.secrets.get("USER_LOGIN", "admin")
SENHA_CORRETA = st.secrets.get("USER_PASSWORD", "senha123")

def verificar_login():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False

    if not st.session_state["autenticado"]:
        st.markdown("<h2 style='text-align: center;'>🔒 Acesso ao CRM de CNPJs</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            if st.button("Entrar", use_container_width=True):
                if usuario == USUARIO_CORRETO and senha == SENHA_CORRETA:
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
        return False
    return True

if not verificar_login():
    st.stop()

# Botão de Logout na Sidebar
if st.sidebar.button("🚪 Sair do Sistema"):
    st.session_state["autenticado"] = False
    st.rerun()

# ==========================================
# 2. CONEXÃO COM O BANCO DE DADOS EM NUVEM
# ==========================================
def get_db_connection():
    return psycopg2.connect(st.secrets["POSTGRES_URL"])

def obter_colunas_tabela():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'empresas'")
    colunas = [row[0] for row in cursor.fetchall()]
    conn.close()
    return colunas

def carregar_dados(filtro_bairro, filtro_porte, filtro_status, busca):
    conn = get_db_connection()
    query = "SELECT * FROM empresas WHERE 1=1"
    params = []

    if filtro_bairro != "Todos":
        query += " AND bairro = %s"
        params.append(filtro_bairro)

    if filtro_porte != "Todos":
        query += " AND porte_empresa = %s"
        params.append(filtro_porte)
        
    if filtro_status != "Todos":
        query += " AND status_followup = %s"
        params.append(filtro_status)

    if busca:
        query += " AND (cnpj_formatado ILIKE %s OR razao_social ILIKE %s OR nome_fantasia ILIKE %s OR cnae_principal ILIKE %s)"
        params.extend([f"%{busca}%", f"%{busca}%", f"%{busca}%", f"%{busca}%"])

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def atualizar_followup(cnpj, novo_status, obs):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE empresas 
        SET status_followup = %s, observacoes = %s 
        WHERE cnpj_formatado = %s
    """, (novo_status, obs, cnpj))
    conn.commit()
    conn.close()

# ==========================================
# 3. INTERFACE DO PAINEL CRM
# ==========================================
st.title("🏢 Painel de Gestão e Follow-up de Vendas")

st.sidebar.header("🔍 Filtros de Busca")

colunas_existentes = obter_colunas_tabela()

conn = get_db_connection()
bairros_disponiveis = ["Todos"] + list(pd.read_sql_query("SELECT DISTINCT bairro FROM empresas WHERE bairro IS NOT NULL AND bairro != '' ORDER BY bairro", conn)['bairro'])

if "porte_empresa" in colunas_existentes:
    portes_disponiveis = ["Todos"] + list(pd.read_sql_query("SELECT DISTINCT porte_empresa FROM empresas WHERE porte_empresa IS NOT NULL AND porte_empresa != '' ORDER BY porte_empresa", conn)['porte_empresa'])
else:
    portes_disponiveis = ["Todos"]
conn.close()

sel_bairro = st.sidebar.selectbox("Bairro:", bairros_disponiveis)
sel_porte = st.sidebar.selectbox("Porte da Empresa:", portes_disponiveis)
sel_status = st.sidebar.selectbox("Status Follow-up:", ["Todos", "Pendente", "Em Contato", "Agendado", "Concluído", "Sem Interesse"])

busca_texto = st.sidebar.text_input("Buscar por CNPJ, Razão, Fantasia ou CNAE:")

df_exibicao = carregar_dados(sel_bairro, sel_porte, sel_status, busca_texto)

st.write(f"📊 **{len(df_exibicao)}** empresas encontradas.")

if not df_exibicao.empty:
    col_tabela, col_detalhes = st.columns([1.8, 1.2])

    with col_tabela:
        st.subheader("📋 Lista de Empresas")
        
        cols_resumo = ['cnpj_formatado', 'razao_social', 'porte_empresa', 'bairro', 'status_followup', 'telefone1']
        cols_presentes = [c for c in cols_resumo if c in df_exibicao.columns]
        
        selecao = st.dataframe(
            df_exibicao[cols_presentes],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )

    with col_detalhes:
        st.subheader("📍 Detalhes Completos da Empresa")
        rows = selecao.selection.rows if selecao else []
        
        if rows:
            empresa = df_exibicao.iloc[rows[0]]

            st.markdown(f"### {empresa.get('razao_social', '')}")
            if pd.notna(empresa.get('nome_fantasia')) and str(empresa.get('nome_fantasia')).strip():
                st.caption(f"**Nome Fantasia:** {empresa.get('nome_fantasia')}")

            tab_cad, tab_end, tab_cont, tab_datas = st.tabs(["🏛️ Cadastro", "📍 Endereço", "📞 Contato", "📅 Situação"])

            with tab_cad:
                st.write(f"**CNPJ:** {empresa.get('cnpj_formatado', '')}")
                st.write(f"**Porte da Empresa:** {empresa.get('porte_empresa', 'Não Informado')}")
                st.write(f"**Matriz / Filial:** {empresa.get('matriz_filial', '')}")
                st.write(f"**Capital Social:** R$ {empresa.get('capital_social', '0,00')}")
                st.write(f"**CNAE Principal:** {empresa.get('cnae_principal', '')}")
                if pd.notna(empresa.get('cnae_secundario')) and str(empresa.get('cnae_secundario')).strip():
                    st.write(f"**CNAE Secundário:** {empresa.get('cnae_secundario')}")

            with tab_end:
                tipo_log = f"{empresa.get('tipo_logradouro', '')} ".strip() if pd.notna(empresa.get('tipo_logradouro')) else ""
                logr = str(empresa.get('logradouro', '')).strip() if pd.notna(empresa.get('logradouro')) else ""
                num = str(empresa.get('numero', '')).strip() if pd.notna(empresa.get('numero')) else ""
                comp = f" - {empresa.get('complemento')}" if pd.notna(empresa.get('complemento')) and str(empresa.get('complemento')).strip() else ""
                bairro = str(empresa.get('bairro', '')).strip() if pd.notna(empresa.get('bairro')) else ""
                muni = str(empresa.get('municipio', '')).strip() if pd.notna(empresa.get('municipio')) else ""
                uf = str(empresa.get('uf', '')).strip() if pd.notna(empresa.get('uf')) else ""
                cep = str(empresa.get('cep', '')).strip() if pd.notna(empresa.get('cep')) else ""

                st.write(f"**Logradouro:** {tipo_log}{logr}, {num}")
                if comp:
                    st.write(f"**Complemento:** {empresa.get('complemento')}")
                st.write(f"**Bairro:** {bairro}")
                st.write(f"**Cidade / UF:** {muni} / {uf}")
                st.write(f"**CEP:** {cep}")

                endereco_query = f"{logr}, {num}, {bairro}, {muni} - {uf}, {cep}, Brasil"
                url_maps = f"https://www.google.com/maps/search/?api=1&query={requests.utils.quote(endereco_query)}"
                st.link_button("🗺️ Ver Local Exato no Google Maps", url_maps, use_container_width=True)

            with tab_cont:
                ddd1 = str(empresa.get('ddd1', '')).strip() if pd.notna(empresa.get('ddd1')) else ""
                tel1 = str(empresa.get('telefone1', '')).strip() if pd.notna(empresa.get('telefone1')) else ""
                ddd2 = str(empresa.get('ddd2', '')).strip() if pd.notna(empresa.get('ddd2')) else ""
                tel2 = str(empresa.get('telefone2', '')).strip() if pd.notna(empresa.get('telefone2')) else ""
                ddd_fax = str(empresa.get('ddd_fax', '')).strip() if pd.notna(empresa.get('ddd_fax')) else ""
                fax = str(empresa.get('fax', '')).strip() if pd.notna(empresa.get('fax')) else ""
                email = str(empresa.get('correio_eletronico', '')).strip() if pd.notna(empresa.get('correio_eletronico')) else ""

                st.write(f"**Telefone 1:** ({ddd1}) {tel1}" if ddd1 or tel1 else f"**Telefone 1:** {tel1}")
                if tel2:
                    st.write(f"**Telefone 2:** ({ddd2}) {tel2}" if ddd2 else f"**Telefone 2:** {tel2}")
                if fax:
                    st.write(f"**Fax:** ({ddd_fax}) {fax}" if ddd_fax else f"**Fax:** {fax}")
                st.write(f"**E-mail:** {email if email else 'Não Informado'}")

            with tab_datas:
                st.write(f"**Data Início Atividade:** {empresa.get('data_inicio_atividade', '')}")
                st.write(f"**Situação Cadastral:** {empresa.get('situacao_cadastral', '')}")
                st.write(f"**Data da Situação:** {empresa.get('data_situacao', '')}")
                st.write(f"**Motivo da Situação:** {empresa.get('motivo_situacao', 'SEM MOTIVO')}")
                if pd.notna(empresa.get('situacao_especial')) and str(empresa.get('situacao_especial')).strip():
                    st.write(f"**Situação Especial:** {empresa.get('situacao_especial')}")
                    st.write(f"**Data Situação Especial:** {empresa.get('data_situacao_especial')}")

            st.divider()

            st.write("📝 **Registrar Follow-up:**")
            opcoes_status = ["Pendente", "Em Contato", "Agendado", "Concluído", "Sem Interesse"]
            st_atual = empresa.get('status_followup', 'Pendente')
            idx_st = opcoes_status.index(st_atual) if st_atual in opcoes_status else 0
            novo_st = st.selectbox("Status:", opcoes_status, index=idx_st)
            
            obs_atual = empresa.get('observacoes', '')
            novas_obs = st.text_area("Observações:", value=obs_atual if pd.notna(obs_atual) else "")

            if st.button("💾 Salvar Follow-up", use_container_width=True):
                atualizar_followup(empresa['cnpj_formatado'], novo_st, novas_obs)
                st.success("Salvo com sucesso!")
                st.rerun()
        else:
            st.info("👆 Clique em uma linha da tabela para ver a localização e todos os detalhes.")
else:
    st.warning("Nenhuma empresa encontrada com os filtros selecionados.")

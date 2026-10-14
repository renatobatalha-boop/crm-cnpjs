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

def carregar_dados(filtro_bairro, filtro_status, busca):
    conn = get_db_connection()
    query = "SELECT * FROM empresas WHERE 1=1"
    params = []

    if filtro_bairro != "Todos":
        query += " AND bairro = %s"
        params.append(filtro_bairro)
        
    if filtro_status != "Todos":
        query += " AND status_followup = %s"
        params.append(filtro_status)

    if busca:
        query += " AND (cnpj_formatado ILIKE %s OR razao_social ILIKE %s OR nome_fantasia ILIKE %s)"
        params.extend([f"%{busca}%", f"%{busca}%", f"%{busca}%"])

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

st.sidebar.header("🔍 Filtros")

conn = get_db_connection()
bairros_disponiveis = ["Todos"] + list(pd.read_sql_query("SELECT DISTINCT bairro FROM empresas WHERE bairro IS NOT NULL ORDER BY bairro", conn)['bairro'])
conn.close()

sel_bairro = st.sidebar.selectbox("Bairro:", bairros_disponiveis)
sel_status = st.sidebar.selectbox("Status:", ["Todos", "Pendente", "Em Contato", "Agendado", "Concluído", "Sem Interesse"])
busca_texto = st.sidebar.text_input("Buscar por CNPJ / Razão Social:")

df_exibicao = carregar_dados(sel_bairro, sel_status, busca_texto)

st.write(f"📊 **{len(df_exibicao)}** empresas encontradas.")

if not df_exibicao.empty:
    col_tabela, col_detalhes = st.columns([2, 1])

    with col_tabela:
        st.subheader("📋 Lista de Empresas")
        selecao = st.dataframe(
            df_exibicao[['cnpj_formatado', 'razao_social', 'bairro', 'status_followup', 'telefone1', 'correio_eletronico']],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )

    with col_detalhes:
        st.subheader("📍 Detalhes & Região")
        rows = selecao.selection.rows if selecao else []
        
        if rows:
            empresa = df_exibicao.iloc[rows[0]]

            st.markdown(f"### {empresa['razao_social']}")
            st.write(f"**CNPJ:** {empresa['cnpj_formatado']}")
            st.write(f"**Fantasia:** {empresa['nome_fantasia']}")
            st.write(f"**Endereço:** {empresa['logradouro']}, {empresa['numero']} - {empresa['bairro']}")
            st.write(f"**CEP:** {empresa['cep']}")
            st.write(f"**Telefone:** {empresa['telefone1']}")
            st.write(f"**E-mail:** {empresa['correio_eletronico']}")

            # Formatação precisa para localizar o pino exato no Google Maps
            logr = str(empresa['logradouro']).strip() if pd.notna(empresa['logradouro']) else ""
            num = str(empresa['numero']).strip() if pd.notna(empresa['numero']) else ""
            bairro = str(empresa['bairro']).strip() if pd.notna(empresa['bairro']) else ""
            muni = str(empresa['municipio']).strip() if pd.notna(empresa['municipio']) else ""
            uf = str(empresa['uf']).strip() if pd.notna(empresa['uf']) else ""
            cep = str(empresa['cep']).strip() if pd.notna(empresa['cep']) else ""

            # Constrói o texto completo do endereço sem falhas de formatação
            endereco_completo = f"{logr}, {num}, {bairro}, {muni} - {uf}, {cep}, Brasil"
            url_maps = f"https://www.google.com/maps/search/?api=1&query={requests.utils.quote(endereco_completo)}"
            
            st.link_button("🗺️ Ver Local Exato no Google Maps", url_maps)

            st.divider()

            st.write("📝 **Registrar Follow-up:**")
            opcoes_status = ["Pendente", "Em Contato", "Agendado", "Concluído", "Sem Interesse"]
            idx_st = opcoes_status.index(empresa['status_followup']) if empresa['status_followup'] in opcoes_status else 0
            novo_st = st.selectbox("Status:", opcoes_status, index=idx_st)
            
            novas_obs = st.text_area("Observações:", value=empresa['observacoes'] if empresa['observacoes'] else "")

            if st.button("💾 Salvar Follow-up", use_container_width=True):
                atualizar_followup(empresa['cnpj_formatado'], novo_st, novas_obs)
                st.success("Salvo com sucesso!")
                st.rerun()
        else:
            st.info("👆 Clique em uma linha da tabela para ver a localização e atualizar o status.")
else:
    st.warning("Nenhuma empresa encontrada com os filtros selecionados.")

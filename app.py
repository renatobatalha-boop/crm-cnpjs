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


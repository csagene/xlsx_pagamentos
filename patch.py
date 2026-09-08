import os

with open("app_dashboard.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. CSS
css = """st.set_page_config(page_title="Sistema de Relatórios INAS", page_icon="📊", layout="wide")

st.markdown('''
    <style>
    header[data-testid="stHeader"] { display: none !important; }
    section[data-testid="stSidebar"] { background-color: #0d0d0d !important; }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3,
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] .stRadio label,
    section[data-testid="stSidebar"] div[role="radiogroup"] div { color: #f0f0f0 !important; }
    .block-container { padding-bottom: 100px !important; }
    div[data-testid="stHorizontalBlock"]:has(~ div #nav-buttons-hook) {
        position: fixed; bottom: 0; left: 0; width: 100%;
        background-color: #ffffff; padding: 15px 30px; z-index: 999;
        border-top: 1px solid #e0e0e0; box-shadow: 0 -4px 6px -1px rgba(0,0,0,0.05); margin: 0;
    }
    @media (min-width: 50.625rem) {
        div[data-testid="stHorizontalBlock"]:has(~ div #nav-buttons-hook) { padding-left: 21rem; padding-right: 2rem; }
    }
    </style>
''', unsafe_allow_html=True)
"""
content = content.replace("st.set_page_config(page_title=\"Sistema de Relatórios INAS\", page_icon=\"📊\", layout=\"wide\")", css)


# 2. adicionar_linha_totais
old_func = """def adicionar_linha_totais(df_resultado, colunas_agrupamento):
    df_resultado = df_resultado.copy()
    if "Totais" not in df_resultado.columns:
        df_resultado.insert(0, "Totais", "")
        
    def extract_unique_items(series):
        unique_items = set()
        for val in series.dropna().astype(str):
            for item in val.split(','):
                item = item.strip()
                if item and item != "N/D" and item.lower() != "fonte_financiamento":
                    unique_items.add(item)
        lista = list(unique_items)
        try:
            lista.sort(key=float)
        except ValueError:
            lista.sort()
        return ", ".join(lista)
        
    col_fonte = None
    col_impl = None
    
    for col in df_resultado.columns:
        c_lower = str(col).lower()
        if "fonte" in c_lower:
            col_fonte = col
        if "implementador" in c_lower:
            col_impl = col
            
    if col_impl:
        df_resultado[col_impl] = "INAS"
        
    linhas_totais = []
    
    if col_fonte:
        fontes_unicas = df_resultado[col_fonte].dropna().astype(str).unique()
        for fonte in fontes_unicas:
            if not fonte.strip() or fonte == "N/D" or fonte == "FONTE_FINANCIAMENTO": continue
                
            df_fonte = df_resultado[df_resultado[col_fonte] == fonte]
            t_fonte = {}
            for col in df_resultado.columns:
                if col == "Totais":
                    t_fonte[col] = f"TOTAL - {fonte}"
                elif col == col_fonte:
                    t_fonte[col] = fonte
                elif col == col_impl:
                    t_fonte[col] = "INAS"
                elif pd.api.types.is_numeric_dtype(df_resultado[col]) and col not in colunas_agrupamento:
                    t_fonte[col] = df_fonte[col].sum()
                elif col in colunas_agrupamento:
                    t_fonte[col] = extract_unique_items(df_fonte[col])
                else:
                    t_fonte[col] = ""
            linhas_totais.append(t_fonte)
            
    t_geral = {}
    for col in df_resultado.columns:
        if col == "Totais":
            t_geral[col] = "TOTAL GERAL"
        elif col == col_impl:
            t_geral[col] = "INAS"
        elif pd.api.types.is_numeric_dtype(df_resultado[col]) and col not in colunas_agrupamento:
            t_geral[col] = df_resultado[col].sum()
        elif col in colunas_agrupamento:
            t_geral[col] = extract_unique_items(df_resultado[col])
        else:
            t_geral[col] = ""
            
    linhas_totais.append(t_geral)
    
    df_totais = pd.DataFrame(linhas_totais)
    return pd.concat([df_resultado, df_totais], ignore_index=True)"""

new_func = """def adicionar_linha_totais(df_resultado, colunas_agrupamento):
    df_resultado = df_resultado.copy()
    primeira_col = colunas_agrupamento[0] if colunas_agrupamento and colunas_agrupamento[0] in df_resultado.columns else df_resultado.columns[0]
        
    def extract_unique_items(series):
        unique_items = set()
        for val in series.dropna().astype(str):
            for item in val.split(','):
                item = item.strip()
                if item and item != "N/D" and item.lower() != "fonte_financiamento":
                    unique_items.add(item)
        lista = list(unique_items)
        try:
            lista.sort(key=float)
        except ValueError:
            lista.sort()
        return ", ".join(lista)
        
    col_fonte = None
    col_impl = None
    col_mes = None
    
    for col in df_resultado.columns:
        c_lower = str(col).lower()
        if "fonte" in c_lower:
            col_fonte = col
        if "implementador" in c_lower:
            col_impl = col
        if "mes" in c_lower or "mês" in c_lower:
            col_mes = col
            
    if col_impl:
        df_resultado[col_impl] = "INAS"
        
    linhas_totais = []
    
    if col_fonte:
        fontes_unicas = df_resultado[col_fonte].dropna().astype(str).unique()
        for fonte in fontes_unicas:
            if not fonte.strip() or fonte == "N/D" or fonte == "FONTE_FINANCIAMENTO": continue
                
            df_fonte = df_resultado[df_resultado[col_fonte] == fonte]
            t_fonte = {}
            for col in df_resultado.columns:
                if col == primeira_col:
                    t_fonte[col] = f"TOTAL - {fonte}"
                elif col == col_fonte and col != primeira_col:
                    t_fonte[col] = fonte
                elif col == col_impl and col != primeira_col:
                    t_fonte[col] = "INAS"
                elif pd.api.types.is_numeric_dtype(df_resultado[col]) and col not in colunas_agrupamento:
                    if str(col).endswith("_ACUM"):
                        if col_mes:
                            agrup_sem_mes = [c for c in colunas_agrupamento if c != col_mes and c in df_fonte.columns]
                            if agrup_sem_mes:
                                t_fonte[col] = df_fonte.groupby(agrup_sem_mes)[col].max().sum()
                            else:
                                t_fonte[col] = df_fonte[col].max()
                        else:
                            t_fonte[col] = df_fonte[col].max()
                    else:
                        t_fonte[col] = df_fonte[col].sum()
                elif col in colunas_agrupamento and col != primeira_col:
                    t_fonte[col] = extract_unique_items(df_fonte[col])
                else:
                    if col not in t_fonte: t_fonte[col] = ""
            linhas_totais.append(t_fonte)
            
    t_geral = {}
    for col in df_resultado.columns:
        if col == primeira_col:
            t_geral[col] = "TOTAL GERAL"
        elif col == col_impl and col != primeira_col:
            t_geral[col] = "INAS"
        elif pd.api.types.is_numeric_dtype(df_resultado[col]) and col not in colunas_agrupamento:
            if str(col).endswith("_ACUM"):
                if col_mes:
                    agrup_sem_mes = [c for c in colunas_agrupamento if c != col_mes and c in df_resultado.columns]
                    if agrup_sem_mes:
                        t_geral[col] = df_resultado.groupby(agrup_sem_mes)[col].max().sum()
                    else:
                        t_geral[col] = df_resultado[col].max()
                else:
                    t_geral[col] = df_resultado[col].max()
            else:
                t_geral[col] = df_resultado[col].sum()
        elif col in colunas_agrupamento and col != primeira_col:
            t_geral[col] = extract_unique_items(df_resultado[col])
        else:
            if col not in t_geral: t_geral[col] = ""
            
    linhas_totais.append(t_geral)
    
    df_totais = pd.DataFrame(linhas_totais)
    df_completo = pd.concat([df_resultado, df_totais], ignore_index=True)
    return df_completo, df_totais"""

content = content.replace(old_func, new_func)

# 3. Expander
old_expander = """    elif st.session_state.relatorio_final is not None:
        st.markdown("#### 🔍 Filtros em Cascata")
        st.markdown("Selecione opções abaixo para filtrar os detalhes. Os totais atualizarão automaticamente.")
        
        rel_display = st.session_state.relatorio_final.copy()
        rel_cumul_display = st.session_state.relatorio_cumulativo.copy()"""

new_expander = """    elif st.session_state.relatorio_final is not None:
        with st.expander("🔍 Filtros em Cascata (Selecione opções abaixo para filtrar os detalhes. Os totais atualizarão automaticamente.)", expanded=True):
            rel_display = st.session_state.relatorio_final.copy()
            rel_cumul_display = st.session_state.relatorio_cumulativo.copy()"""

content = content.replace(old_expander, new_expander)

# 4. Indent filters inside expander
old_filters = """        filtros_aplicados = []
        if len(st.session_state.col_agrupamento) > 0:
            # Criar um grid de 4 colunas horizontais
            col_filtros = st.columns(4)
            for i, col in enumerate(st.session_state.col_agrupamento):
                # Distribuir os filtros de forma equitativa pelas colunas
                with col_filtros[i % 4]:
                    is_mes = "mes" in str(col).lower() or "mês" in str(col).lower()
                    
                    if is_mes:
                        opcoes_brutas = rel_display[col].astype(str).dropna().tolist()
                        opcoes_lista = []
                        for op in opcoes_brutas:
                            opcoes_lista.extend([m.strip() for m in op.split(',') if m.strip() and m.strip() != "N/D"])
                        try:
                            opcoes = sorted(list(set(opcoes_lista)), key=float)
                        except:
                            opcoes = sorted(list(set(opcoes_lista)))
                    else:
                        opcoes = sorted(list(rel_display[col].astype(str).dropna().unique()))
                        
                    selecao = st.multiselect(f"Filtrar por {col}:", opcoes)
                    
                    if selecao:
                        if is_mes:
                            mask = rel_display[col].astype(str).apply(
                                lambda x: any(sel in [m.strip() for m in x.split(',')] for sel in selecao)
                            )
                            rel_display = rel_display[mask]
                            
                            mask_cumul = rel_cumul_display[col].astype(str).apply(
                                lambda x: any(sel in [m.strip() for m in x.split(',')] for sel in selecao)
                            )
                            rel_cumul_display = rel_cumul_display[mask_cumul]
                        else:
                            rel_display = rel_display[rel_display[col].astype(str).isin(selecao)]
                            rel_cumul_display = rel_cumul_display[rel_cumul_display[col].astype(str).isin(selecao)]
                            
                        filtros_aplicados.append(f"**{col}:** {', '.join(selecao)}")"""

new_filters = """            filtros_aplicados = []
            if len(st.session_state.col_agrupamento) > 0:
                # Criar um grid de 4 colunas horizontais
                col_filtros = st.columns(4)
                for i, col in enumerate(st.session_state.col_agrupamento):
                    # Distribuir os filtros de forma equitativa pelas colunas
                    with col_filtros[i % 4]:
                        is_mes = "mes" in str(col).lower() or "mês" in str(col).lower()
                        
                        if is_mes:
                            opcoes_brutas = rel_display[col].astype(str).dropna().tolist()
                            opcoes_lista = []
                            for op in opcoes_brutas:
                                opcoes_lista.extend([m.strip() for m in op.split(',') if m.strip() and m.strip() != "N/D"])
                            try:
                                opcoes = sorted(list(set(opcoes_lista)), key=float)
                            except:
                                opcoes = sorted(list(set(opcoes_lista)))
                        else:
                            opcoes = sorted(list(rel_display[col].astype(str).dropna().unique()))
                            
                        selecao = st.multiselect(f"Filtrar por {col}:", opcoes)
                        
                        if selecao:
                            if is_mes:
                                mask = rel_display[col].astype(str).apply(
                                    lambda x: any(sel in [m.strip() for m in x.split(',')] for sel in selecao)
                                )
                                rel_display = rel_display[mask]
                                
                                mask_cumul = rel_cumul_display[col].astype(str).apply(
                                    lambda x: any(sel in [m.strip() for m in x.split(',')] for sel in selecao)
                                )
                                rel_cumul_display = rel_cumul_display[mask_cumul]
                            else:
                                rel_display = rel_display[rel_display[col].astype(str).isin(selecao)]
                                rel_cumul_display = rel_cumul_display[rel_cumul_display[col].astype(str).isin(selecao)]
                                
                            filtros_aplicados.append(f"**{col}:** {', '.join(selecao)}")"""

content = content.replace(old_filters, new_filters)

# 5. UI logic
old_ui = """        st.session_state.relatorio_filtrado = rel_display
        st.session_state.relatorio_cumul_filtrado = rel_cumul_display
        st.session_state.filtros_aplicados_texto = filtros_aplicados
        
        rel_display_com_totais = adicionar_linha_totais(rel_display, st.session_state.col_agrupamento)
        num_totais = len(rel_display_com_totais) - len(rel_display)
        df_totais_so = rel_display_com_totais.tail(num_totais)
        
        def destacar_totais_isolados(row):
            # A primeira coluna (iloc[0]) agora é 'Totais'
            is_geral = (row.iloc[0] == "TOTAL GERAL")
            if is_geral:
                return ['font-weight: bold; background-color: #ffe6e6; border-top: 2px solid black'] * len(row)
            else:
                return [''] * len(row)
        
        def format_mt(val):
            if pd.isna(val) or val == "": return ""
            try:
                s = f"{float(val):,.2f}"
                s = s.replace(",", "X").replace(".", ",").replace("X", " ")
                return f"{s} MT"
            except:
                return str(val)
                
        format_dict = {col: format_mt for col in rel_display.columns if "valor" in str(col).lower() or "pago" in str(col).lower()}
        format_dict_cumul = {col: format_mt for col in rel_cumul_display.columns if "valor" in str(col).lower() or "pago" in str(col).lower()}
        
        tab1, tab2 = st.tabs(["📊 Tabela 1 — PAGAMENTOS MENSAL", "📈 Tabela 2 — PAGAMENTOS CUMULATIVO"])
        
        with tab1:
            styled_display = rel_display.style.format(format_dict)
            styled_totais = df_totais_so.style.apply(destacar_totais_isolados, axis=1).format(format_dict).hide(axis="index")
            
            st.dataframe(styled_display, height=400, use_container_width=True, hide_index=True)
            st.write("📌 **TOTAIS GERAIS DOS DADOS ACIMA:**")
            st.dataframe(styled_totais, use_container_width=True, hide_index=True)
            
            buffer1 = io.BytesIO()
            with pd.ExcelWriter(buffer1, engine='openpyxl') as writer:
                rel_display_com_totais.to_excel(writer, index=False, sheet_name='PAGAMENTOS_MENSAL')
            
            st.download_button(
                label="📥 Descarregar Tabela 1 (Mensal)",
                data=buffer1.getvalue(),
                file_name="PAGAMENTOS_MENSAL.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with tab2:
            styled_cumul = rel_cumul_display.style.format(format_dict_cumul)
            st.dataframe(styled_cumul, height=400, use_container_width=True, hide_index=True)
            st.info("ℹ️ A tabela cumulativa soma os valores progressivamente, respondendo: 'Até este mês, quanto já foi pago?'")
            
            buffer2 = io.BytesIO()
            with pd.ExcelWriter(buffer2, engine='openpyxl') as writer:
                rel_cumul_display.to_excel(writer, index=False, sheet_name='PAGAMENTOS_CUMULATIVO')
            
            st.download_button(
                label="📥 Descarregar Tabela 2 (Cumulativo)",
                data=buffer2.getvalue(),
                file_name="PAGAMENTOS_CUMULATIVO.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )"""

new_ui = """        st.session_state.relatorio_filtrado = rel_display
        st.session_state.relatorio_cumul_filtrado = rel_cumul_display
        st.session_state.filtros_aplicados_texto = filtros_aplicados
        
        rel_display_completo, rel_display_totais = adicionar_linha_totais(rel_display, st.session_state.col_agrupamento)
        rel_cumul_display_completo, rel_cumul_totais = adicionar_linha_totais(rel_cumul_display, st.session_state.col_agrupamento)
        
        def destacar_totais_isolados(row):
            is_geral = (row.iloc[0] == "TOTAL GERAL")
            if is_geral:
                return ['font-weight: bold; background-color: #ffe6e6; border-top: 2px solid black'] * len(row)
            else:
                return [''] * len(row)
        
        def format_mt(val):
            if pd.isna(val) or val == "": return ""
            try:
                s = f"{float(val):,.2f}"
                s = s.replace(",", "X").replace(".", ",").replace("X", " ")
                return f"{s} MT"
            except:
                return str(val)
                
        format_dict = {col: format_mt for col in rel_display.columns if "valor" in str(col).lower() or "pago" in str(col).lower()}
        format_dict_cumul = {col: format_mt for col in rel_cumul_display.columns if "valor" in str(col).lower() or "pago" in str(col).lower()}
        
        tab1, tab2 = st.tabs(["📊 Tabela 1 — PAGAMENTOS MENSAL", "📈 Tabela 2 — PAGAMENTOS CUMULATIVO"])
        
        with tab1:
            styled_display = rel_display.style.format(format_dict)
            styled_totais = rel_display_totais.style.apply(destacar_totais_isolados, axis=1).format(format_dict).hide(axis="index")
            
            st.dataframe(styled_display, height=400, use_container_width=True, hide_index=True)
            st.write("📌 **TOTAIS GERAIS DOS DADOS ACIMA:**")
            st.dataframe(styled_totais, use_container_width=True, hide_index=True)
            
            buffer1 = io.BytesIO()
            with pd.ExcelWriter(buffer1, engine='openpyxl') as writer:
                rel_display_completo.to_excel(writer, index=False, sheet_name='PAGAMENTOS_MENSAL')
            
            st.download_button(
                label="📥 Descarregar Tabela 1 Completa (Mensal)",
                data=buffer1.getvalue(),
                file_name="PAGAMENTOS_MENSAL.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with tab2:
            styled_cumul = rel_cumul_display.style.format(format_dict_cumul)
            styled_totais_cumul = rel_cumul_totais.style.apply(destacar_totais_isolados, axis=1).format(format_dict_cumul).hide(axis="index")
            
            st.dataframe(styled_cumul, height=400, use_container_width=True, hide_index=True)
            st.write("📌 **TOTAIS GERAIS DOS DADOS ACIMA:**")
            st.dataframe(styled_totais_cumul, use_container_width=True, hide_index=True)
            
            st.info("ℹ️ A tabela cumulativa soma os valores progressivamente, respondendo: 'Até este mês, quanto já foi pago?'")
            
            buffer2 = io.BytesIO()
            with pd.ExcelWriter(buffer2, engine='openpyxl') as writer:
                rel_cumul_display_completo.to_excel(writer, index=False, sheet_name='PAGAMENTOS_CUMULATIVO')
            
            st.download_button(
                label="📥 Descarregar Tabela 2 Completa (Cumulativo)",
                data=buffer2.getvalue(),
                file_name="PAGAMENTOS_CUMULATIVO.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )"""

content = content.replace(old_ui, new_ui)

# 6. nav-buttons-hook
content = content + "\n\nst.markdown(\"<div id='nav-buttons-hook'></div>\", unsafe_allow_html=True)\n"

with open("app_dashboard.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Success")

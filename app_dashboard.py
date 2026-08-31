import streamlit as st
import pandas as pd
import numpy as np
import io
import json
import os

# ---------------------------------------------------------
# CONFIGURAÇÃO GERAL
# ---------------------------------------------------------
st.set_page_config(page_title="Sistema de Relatórios INAS", page_icon="📊", layout="wide")

TEMPLATES_FILE = "templates.json"

DEFAULT_TEMPLATES = {
    "modelo de tabela globalizadovf_final_xls": {
        "colunas_agrupamento": ["Ano ", "Mês", "Província", "Delegação", "Distrito", "Fonte", "Programa", "Implementador", "Provedor  servico"],
        "colunas_metricas": ["F", "M", "Benef. Distintos", "1x", "2x", "3x", "4+", "Pagamentos", "Valor Pago"]
    }
}

def carregar_templates():
    if not os.path.exists(TEMPLATES_FILE):
        with open(TEMPLATES_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_TEMPLATES, f, ensure_ascii=False, indent=4)
        return DEFAULT_TEMPLATES
    
    with open(TEMPLATES_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return DEFAULT_TEMPLATES

def guardar_templates(templates):
    with open(TEMPLATES_FILE, "w", encoding="utf-8") as f:
        json.dump(templates, f, ensure_ascii=False, indent=4)

if "templates" not in st.session_state:
    st.session_state.templates = carregar_templates()

# Inicializar variáveis na memória
if "df" not in st.session_state:
    st.session_state.df = None
if "df_editado" not in st.session_state:
    st.session_state.df_editado = None
if "relatorio_final" not in st.session_state:
    st.session_state.relatorio_final = None
if "col_agrupamento" not in st.session_state:
    st.session_state.col_agrupamento = []

# ---------------------------------------------------------
# MENU DE NAVEGAÇÃO LATERAL
# ---------------------------------------------------------
PAGINAS = [
    "📥 1. Carregar & Editar Dados", 
    "📑 2. Gerar Relatório", 
    "📈 3. Dashboard Visual"
]

if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = PAGINAS[0]

def ir_proximo():
    idx = PAGINAS.index(st.session_state.pagina_atual)
    if idx < len(PAGINAS) - 1:
        st.session_state.pagina_atual = PAGINAS[idx + 1]

def ir_anterior():
    idx = PAGINAS.index(st.session_state.pagina_atual)
    if idx > 0:
        st.session_state.pagina_atual = PAGINAS[idx - 1]

st.sidebar.title("🧭 Organização")
st.sidebar.markdown("Navegue entre as páginas da aplicação:")
pagina = st.sidebar.radio("", PAGINAS, key="pagina_atual")

st.sidebar.divider()
if st.session_state.df_editado is not None:
    st.sidebar.success(f"✅ Dados carregados ({len(st.session_state.df_editado)} registos)")
else:
    st.sidebar.warning("⚠️ Nenhum dado carregado")

def adicionar_linha_totais(df_resultado, colunas_agrupamento):
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
    return pd.concat([df_resultado, df_totais], ignore_index=True)

import unicodedata

def processar_relatorio(df, template):
    colunas_df = df.columns.tolist()
    col_agrupamento = template["colunas_agrupamento"]
    col_metricas = template["colunas_metricas"]
    
    if not col_agrupamento:
        raise ValueError("O template deve ter pelo menos uma coluna de agrupamento.")
        
    def normalize_text(text):
        if not isinstance(text, str):
            return ""
        text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
        return text.lower().strip()

    aliases = {
        "ano": ["ano_pagamento", "ano", "year"],
        "mês": ["meses_pagamento", "mes", "mês", "meses", "month"],
        "província": ["provincia", "província", "province"],
        "delegação": ["delegacao", "delegação"],
        "distrito": ["distrito", "district"],
        "fonte": ["fonte_financiamento", "fonte", "source"],
        "programa": ["programa_social", "programa"],
        "implementador": ["implementador", "ps_name", "implementer"],  
        "provedor": ["psp_name", "provedor", "operador"]
    }
        
    col_agrupamento_reais = []
    for col_temp in col_agrupamento:
        temp_norm = normalize_text(col_temp)
        col_encontrada = None
        
        # 1. Exact match (normalized)
        for col in colunas_df:
            if normalize_text(col) == temp_norm:
                col_encontrada = col
                break
                
        # 2. Alias match
        if not col_encontrada:
            for key, alias_list in aliases.items():
                if key in temp_norm:
                    for alias in alias_list:
                        for col in colunas_df:
                            if alias == normalize_text(col):
                                col_encontrada = col
                                break
                        if col_encontrada: break
                if col_encontrada: break
                
        # 3. Substring match
        if not col_encontrada:
            for col in colunas_df:
                col_norm = normalize_text(col)
                if len(temp_norm) >= 3 and temp_norm in col_norm:
                    col_encontrada = col
                    break

        if col_encontrada:
            col_agrupamento_reais.append(col_encontrada)
        else:
            df[col_temp] = "N/D"
            col_agrupamento_reais.append(col_temp)
            
    def detetar_coluna(lista_colunas, palavras_chave):
        for col in lista_colunas:
            if str(col).lower().strip() in palavras_chave: return col
        for col in lista_colunas:
            for p in palavras_chave:
                if p in str(col).lower(): return col
        return None
        
    col_beneficiario = detetar_coluna(colunas_df, ['id', 'código', 'codigo', 'beneficiario', 'beneficiário', 'bi', 'nuit'])
    col_sexo = detetar_coluna(colunas_df, ['sexo', 'genero', 'género', 'sex'])
    col_valor = detetar_coluna(colunas_df, ['valor', 'pago', 'montante', 'dinheiro', 'total', 'unnamed'])
    
    if not col_beneficiario: col_beneficiario = colunas_df[0]
    if not col_valor: col_valor = colunas_df[-1]
    
    # Agrupamento básico
    resumo_basico = df.groupby(col_agrupamento_reais).agg(
        Pagamentos=(col_beneficiario, 'count'),
        Valor_Pago=(col_valor, 'sum'),
        Benef_Distintos=(col_beneficiario, 'nunique')
    )
    
    resumo_basico = resumo_basico.rename(columns={'Valor_Pago': 'Valor Pago', 'Benef_Distintos': 'Benef. Distintos'})
    
    if col_sexo:
        df_sexo_base = df.copy()
        df_sexo_base[col_sexo] = df_sexo_base[col_sexo].fillna("SEM_GENERO").replace("", "SEM_GENERO")
        agrupamento_sexo = list(dict.fromkeys(col_agrupamento_reais + [col_beneficiario, col_sexo]))
        df_sexo = df_sexo_base.drop_duplicates(subset=agrupamento_sexo)
        sexo_pivot = pd.pivot_table(df_sexo, index=col_agrupamento_reais, columns=col_sexo, values=col_beneficiario, aggfunc='nunique', fill_value=0)
        
        for sexo_col in sexo_pivot.columns:
            val = str(sexo_col).strip().upper()
            if val == 'F':
                resumo_basico['F'] = sexo_pivot[sexo_col]
            elif val == 'M':
                resumo_basico['M'] = sexo_pivot[sexo_col]
            else:
                nome_col = f"Sexo_{val}" if val != "SEM_GENERO" else "Sem_Gênero"
                resumo_basico[nome_col] = sexo_pivot[sexo_col]
                
    agrupamento_freq = list(dict.fromkeys(col_agrupamento_reais + [col_beneficiario]))
    freq_df = df.groupby(agrupamento_freq).size().reset_index(name='vezes')
    freq_df['categoria_vezes'] = np.where(freq_df['vezes'] >= 4, '4+', freq_df['vezes'].astype(str) + 'x')
    freq_pivot = pd.pivot_table(freq_df, index=col_agrupamento_reais, columns='categoria_vezes', values=col_beneficiario, aggfunc='nunique', fill_value=0)
    
    relatorio_final = resumo_basico.join(freq_pivot).fillna(0).reset_index()
    
    rename_dict = dict(zip(col_agrupamento_reais, col_agrupamento))
    relatorio_final = relatorio_final.rename(columns=rename_dict)
    
    for metrica in col_metricas:
        if metrica not in relatorio_final.columns:
            relatorio_final[metrica] = 0
            
    ordem_final = col_agrupamento + [m for m in col_metricas if m in relatorio_final.columns]
    relatorio_final = relatorio_final[ordem_final]
    
    for col in relatorio_final.columns:
        if "ano" in str(col).lower():
            # Converter para string e remover '.0' de floats para não aparecer com vírgulas/decimais na UI
            relatorio_final[col] = relatorio_final[col].astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '')
            
    return relatorio_final

# =========================================================
# PÁGINA 1: CARREGAR & EDITAR DADOS
# =========================================================
if pagina == PAGINAS[0]:
    st.title("📥 1. Carregar Dados")
    st.markdown("Faça o upload do ficheiro Excel com os dados em bruto. Pode visualizar a informação importada antes de gerar o relatório.")
    
    uploaded_file = st.file_uploader("Carregue o ficheiro Excel", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        if st.session_state.get('last_file_name') != uploaded_file.name:
            with st.spinner("⏳ A analisar o ficheiro"):
                try:
                    uploaded_file.seek(0)
                    df_preview = pd.read_excel(uploaded_file, header=None, nrows=30)
                    linha_cabecalho = 0
                    for i, row in df_preview.iterrows():
                        non_nulls = row.dropna()
                        if len(non_nulls) >= 3:
                            strings = [x for x in non_nulls if isinstance(x, str)]
                            if len(strings) >= len(non_nulls) * 0.5:
                                linha_cabecalho = i
                                break
                    
                    uploaded_file.seek(0)
                    df = pd.read_excel(uploaded_file, header=linha_cabecalho)
                    
                    novas_colunas = []
                    vistos = {}
                    for col in df.columns:
                        nome_limpo = str(col).replace(":", "_").strip()
                        if nome_limpo in vistos:
                            vistos[nome_limpo] += 1
                            novas_colunas.append(f"{nome_limpo}_{vistos[nome_limpo]}")
                        else:
                            vistos[nome_limpo] = 0
                            novas_colunas.append(nome_limpo)
                    df.columns = novas_colunas
                    
                    st.session_state.df = df
                    st.session_state.df_editado = df.copy()
                    st.session_state.relatorio_final = None 
                    st.session_state.last_file_name = uploaded_file.name
                except Exception as e:
                    st.error(f"Erro ao ler o ficheiro: {e}")
                    
    if st.session_state.df_editado is not None:
        st.success("✅ Dados em bruto importados com sucesso! (Modo de Apenas Leitura)")
        st.dataframe(st.session_state.df_editado, use_container_width=True, height=500, hide_index=True)

# =========================================================
# PÁGINA 2: GERAR RELATÓRIO
# =========================================================
elif pagina == PAGINAS[1]:
    st.title("📑 2. Gerar Relatório")
    
    if st.session_state.df_editado is None:
        st.warning("⚠️ Volte à primeira página e carregue um ficheiro Excel.")
    else:
        st.subheader("🛠️ 1. Selecione ou Crie um Modelo/Template")
        
        lista_templates = list(st.session_state.templates.keys())
        
        template_principal = "modelo de tabela globalizadovf_final_xls"
        if template_principal in lista_templates:
            lista_templates.remove(template_principal)
            lista_templates.insert(0, template_principal)
            
        template_selecionado = st.selectbox("Selecione o Modelo/Template:", lista_templates)
        
        with st.expander("➕ Criar Novo Template ou Editar Atual"):
            col1, col2 = st.columns(2)
            with col1:
                novo_nome = st.text_input("Nome do Template (altere para criar um novo)", value=template_selecionado)
                colunas_disponiveis = st.session_state.df_editado.columns.tolist()
                agrupamento_atual = st.session_state.templates[template_selecionado]["colunas_agrupamento"]
                todas_opcoes_agrup = list(set(colunas_disponiveis + agrupamento_atual))
                
                novo_agrupamento = st.multiselect(
                    "Colunas de Agrupamento (Organização / Linhas):", 
                    options=todas_opcoes_agrup,
                    default=agrupamento_atual
                )
            with col2:
                metricas_disponiveis = ["F", "M", "Sem_Gênero", "Benef. Distintos", "1x", "2x", "3x", "4+", "Pagamentos", "Valor Pago"]
                metricas_atuais = st.session_state.templates[template_selecionado]["colunas_metricas"]
                todas_opcoes_metr = list(set(metricas_disponiveis + metricas_atuais))
                
                novas_metricas = st.multiselect(
                    "Colunas de Métricas (Cálculos / Valores):",
                    options=todas_opcoes_metr,
                    default=metricas_atuais
                )
            
            if st.button("💾 Guardar Modelo", type="primary"):
                if novo_nome:
                    st.session_state.templates[novo_nome] = {
                        "colunas_agrupamento": novo_agrupamento,
                        "colunas_metricas": novas_metricas
                    }
                    guardar_templates(st.session_state.templates)
                    st.success(f"✅ Template '{novo_nome}' guardado com sucesso!")
                    st.rerun()
                else:
                    st.error("O nome do template não pode estar vazio.")

        st.divider()
        st.subheader("⚙️ 2. Gerar e Filtrar Relatório")
        if st.button("🚀 Processar e Gerar Relatório"):
            with st.spinner("A gerar tabela baseada no template..."):
                try:
                    template = st.session_state.templates[template_selecionado]
                    df_base = st.session_state.df_editado.copy()
                    
                    relatorio = processar_relatorio(df_base, template)
                    
                    st.session_state.relatorio_final = relatorio
                    st.session_state.col_agrupamento = template["colunas_agrupamento"]
                    st.success("Tabela gerada e guardada em memória!")
                except Exception as e:
                    st.error(f"Erro ao processar: {e}")

        if st.session_state.relatorio_final is not None:
            st.divider()
            st.markdown("### 🔍 Filtros em Cascata")
            st.markdown("Selecione opções abaixo para filtrar os detalhes. Os totais atualizarão automaticamente.")
            
            rel_display = st.session_state.relatorio_final.copy()
            
            filtros_aplicados = []
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
                            else:
                                rel_display = rel_display[rel_display[col].astype(str).isin(selecao)]
                                
                            filtros_aplicados.append(f"**{col}:** {', '.join(selecao)}")
                            
            st.session_state.relatorio_filtrado = rel_display
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
            
            styled_display = rel_display.style.format(format_dict)
            styled_totais = df_totais_so.style.apply(destacar_totais_isolados, axis=1).format(format_dict).hide(axis="index")
            
            st.subheader("Tabela de Resultados (De acordo com o Template)")
            
            st.dataframe(styled_display, height=400, use_container_width=False, hide_index=True)
            
            st.write("📌 **TOTAIS GERAIS DOS DADOS ACIMA:**")
            st.dataframe(styled_totais, use_container_width=False, hide_index=True)
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                rel_display_com_totais.to_excel(writer, index=False, sheet_name='Relatorio_INAS')
            
            st.download_button(
                label="📥 Exportar Esta Tabela para Excel",
                data=buffer.getvalue(),
                file_name="relatorio_final_detalhado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# =========================================================
# PÁGINA 3: DASHBOARD VISUAL
# =========================================================
elif pagina == PAGINAS[2]:
    st.title("📈 3. Dashboard Visual")
    
    if st.session_state.relatorio_final is None:
        st.warning("⚠️ Primeiro, vá à secção 'Gerar Relatório' e processe a tabela.")
    else:
        if "relatorio_filtrado" in st.session_state and st.session_state.relatorio_filtrado is not None:
            rel_viz = st.session_state.relatorio_filtrado.copy()
        else:
            rel_viz = st.session_state.relatorio_final.copy()
            
        st.write("*(Nota: Os gráficos respondem aos filtros aplicados na página anterior.)*")
        
        filtros_txt = st.session_state.get('filtros_aplicados_texto', [])
        if filtros_txt:
            st.info("🎯 **Filtros Ativos:** " + " | ".join(filtros_txt))
        else:
            st.info("🎯 **Filtros Ativos:** Nenhum (A mostrar todos os dados)")
            
        st.divider()
        
        kpi1, kpi2, kpi3 = st.columns(3)
        total_valor = pd.to_numeric(rel_viz['Valor Pago'], errors='coerce').sum() if 'Valor Pago' in rel_viz.columns else 0
        total_benef = pd.to_numeric(rel_viz['Benef. Distintos'], errors='coerce').sum() if 'Benef. Distintos' in rel_viz.columns else 0
        total_pags = pd.to_numeric(rel_viz['Pagamentos'], errors='coerce').sum() if 'Pagamentos' in rel_viz.columns else 0
        
        def formata_mt_kpi(val):
            s = f"{float(val):,.2f}"
            return s.replace(",", "X").replace(".", ",").replace("X", " ") + " MT"
            
        kpi1.metric("💰 Valor Distribuído", formata_mt_kpi(total_valor))
        kpi2.metric("👥 Beneficiários Únicos", f"{float(total_benef):,.0f}")
        kpi3.metric("💳 Ficheiros / Transações", f"{float(total_pags):,.0f}")
        
        st.write("")
        
        kpi_m, kpi_f, kpi_o = st.columns(3)
        total_m = pd.to_numeric(rel_viz['M'], errors='coerce').sum() if 'M' in rel_viz.columns else 0
        total_f = pd.to_numeric(rel_viz['F'], errors='coerce').sum() if 'F' in rel_viz.columns else 0
        
        total_outros = 0
        for col in rel_viz.columns:
            if col.startswith("Sexo_") or col == "Sem_Gênero":
                total_outros += pd.to_numeric(rel_viz[col], errors='coerce').sum()
                
        kpi_m.metric("👨 Homens (M)", f"{float(total_m):,.0f}")
        kpi_f.metric("👩 Mulheres (F)", f"{float(total_f):,.0f}")
        kpi_o.metric("👤 Genero Não Informados", f"{float(total_outros):,.0f}")
        
        st.divider()
        
        c1, c2 = st.columns(2)
        with c1:
            if 'F' in rel_viz.columns or 'M' in rel_viz.columns or 'Sem_Gênero' in rel_viz.columns:
                st.write("**Proporção de Sexo**")
                labels_sexo = []
                valores_sexo = []
                if 'F' in rel_viz.columns:
                    labels_sexo.append('Mulheres (F)')
                    valores_sexo.append(pd.to_numeric(rel_viz['F'], errors='coerce').sum())
                if 'M' in rel_viz.columns:
                    labels_sexo.append('Homens (M)')
                    valores_sexo.append(pd.to_numeric(rel_viz['M'], errors='coerce').sum())
                if 'Sem_Gênero' in rel_viz.columns:
                    labels_sexo.append('Sem Gênero')
                    valores_sexo.append(pd.to_numeric(rel_viz['Sem_Gênero'], errors='coerce').sum())
                    
                for col in rel_viz.columns:
                    if col.startswith("Sexo_") and col not in ['F', 'M', 'Sem_Gênero']:
                        labels_sexo.append(col.replace("Sexo_", ""))
                        valores_sexo.append(pd.to_numeric(rel_viz[col], errors='coerce').sum())
                        
                sexo_data = pd.DataFrame({
                    'Categoria': labels_sexo,
                    'Total': valores_sexo
                }).set_index('Categoria')
                
                st.bar_chart(sexo_data, color="#FF4B4B")
                
        with c2:
            freq_cols = [c for c in ['1x', '2x', '3x', '4+'] if c in rel_viz.columns]
            if freq_cols:
                st.write("**Frequência de Pagamentos**")
                freq_data = pd.DataFrame({
                    'Vezes': freq_cols,
                    'Total': [pd.to_numeric(rel_viz[c], errors='coerce').sum() for c in freq_cols]
                }).set_index('Vezes')
                st.bar_chart(freq_data, color="#0083B8")
                
        if st.session_state.col_agrupamento:
            eixo_x = st.session_state.col_agrupamento[-1]
            for col in st.session_state.col_agrupamento:
                if "distrito" in col.lower() or "deleg" in col.lower():
                    eixo_x = col
                    break
            
            colunas_genero = []
            if 'F' in rel_viz.columns: colunas_genero.append('F')
            if 'M' in rel_viz.columns: colunas_genero.append('M')
            if 'Sem_Gênero' in rel_viz.columns: colunas_genero.append('Sem_Gênero')
            
            for col in rel_viz.columns:
                if col.startswith("Sexo_") and col not in colunas_genero:
                    colunas_genero.append(col)
                    
            if len(colunas_genero) > 0:
                st.write(f"**Distribuição por: {eixo_x} (Desagregado por Sexo)**")
                for c in colunas_genero:
                    rel_viz[c] = pd.to_numeric(rel_viz[c], errors='coerce').fillna(0)
                graf_distrito = rel_viz.groupby(eixo_x)[colunas_genero].sum()
                st.bar_chart(graf_distrito)
            else:
                st.write(f"**Beneficiários Únicos por: {eixo_x}**")
                if 'Benef. Distintos' in rel_viz.columns:
                    rel_viz['Benef. Distintos'] = pd.to_numeric(rel_viz['Benef. Distintos'], errors='coerce').fillna(0)
                    graf_distrito = rel_viz.groupby(eixo_x)[['Benef. Distintos']].sum()
                    st.bar_chart(graf_distrito)

# =========================================================
# BOTÕES DE NAVEGAÇÃO DE PÁGINA (Fixos em baixo)
# =========================================================
st.markdown("""
    <style>
    /* Espaço para o rodapé não sobrepor a tabela ou gráficos */
    .block-container {
        padding-bottom: 100px !important;
    }
    
    /* Fixar a última linha de colunas (nossos botões) ao fundo da janela */
    div[data-testid="stHorizontalBlock"]:last-of-type {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #ffffff;
        padding: 15px 30px;
        z-index: 999;
        border-top: 1px solid #e0e0e0;
        box-shadow: 0 -4px 6px -1px rgba(0,0,0,0.05);
        margin: 0;
    }
    
    /* Ajustar largura caso a sidebar lateral esteja visível */
    @media (min-width: 50.625rem) {
        div[data-testid="stHorizontalBlock"]:last-of-type {
            padding-left: 21rem; /* Margem para afastar da sidebar */
            padding-right: 2rem;
        }
    }
    </style>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns([1, 4, 1])

with c1:
    if st.session_state.pagina_atual != PAGINAS[0]:
        st.button("⬅️ Voltar", on_click=ir_anterior, use_container_width=True)

with c3:
    if st.session_state.pagina_atual != PAGINAS[-1]:
        pode_avancar = True
        if st.session_state.pagina_atual == PAGINAS[0] and st.session_state.df_editado is None:
            pode_avancar = False
        elif st.session_state.pagina_atual == PAGINAS[1] and st.session_state.relatorio_final is None:
            pode_avancar = False
            
        st.button("Avançar ➡️", on_click=ir_proximo, use_container_width=True, type="primary", disabled=not pode_avancar)

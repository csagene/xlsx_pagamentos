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
    .block-container { padding-bottom: 100px !important; padding-top: 1rem !important; }
    div[data-testid="stHorizontalBlock"]:has(~ div #nav-buttons-hook) {
        position: fixed; bottom: 0; left: 0; width: 100%;
        background-color: #ffffff; padding: 15px 30px; z-index: 999;
        border-top: 1px solid #e0e0e0; box-shadow: 0 -4px 6px -1px rgba(0,0,0,0.05); margin: 0;
    }
    @media (min-width: 50.625rem) {
        div[data-testid="stHorizontalBlock"]:has(~ div #nav-buttons-hook) { padding-left: 21rem; padding-right: 2rem; }
    }
    
    /* Make the filters expander sticky at the top */
    div[data-testid="stExpander"]:has(#filters-sticky-hook) {
        position: sticky;
        top: 0.5rem; /* adjusted for smaller padding */
        z-index: 99999;
        background-color: #ffffff;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        border-radius: 0.5rem;
        overflow: visible !important;
    }
    div[data-testid="stExpander"]:has(#filters-sticky-hook) > div {
        overflow: visible !important;
    }
    div[data-testid="stExpanderDetails"] {
        overflow: visible !important;
    }
    </style>
''', unsafe_allow_html=True)


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
    if st.session_state.pagina_atual in PAGINAS:
        idx = PAGINAS.index(st.session_state.pagina_atual)
        if idx < len(PAGINAS) - 1:
            st.session_state.pagina_atual = PAGINAS[idx + 1]

def ir_anterior():
    if st.session_state.pagina_atual in PAGINAS:
        idx = PAGINAS.index(st.session_state.pagina_atual)
        if idx > 0:
            st.session_state.pagina_atual = PAGINAS[idx - 1]

st.sidebar.markdown("### 🧭 Organização")
st.sidebar.markdown("Navegue entre as páginas da aplicação:")

idx = PAGINAS.index(st.session_state.pagina_atual) if st.session_state.pagina_atual in PAGINAS else 0
pagina = st.sidebar.radio("", PAGINAS, index=idx)

if pagina != st.session_state.pagina_atual:
    st.session_state.pagina_atual = pagina
    st.rerun()

st.sidebar.divider()
if st.session_state.df_editado is not None:
    st.sidebar.success(f"✅ Dados carregados ({len(st.session_state.df_editado)} registos)")
else:
    st.sidebar.warning("⚠️ Nenhum dado carregado")

def adicionar_linha_totais(df_resultado, colunas_agrupamento, is_cumulativo=False, df_bruto=None, meta=None):
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
                    if is_cumulativo:
                        if col_mes:
                            agrup_sem_mes = [c for c in colunas_agrupamento if c != col_mes and c in df_fonte.columns]
                            if agrup_sem_mes:
                                t_fonte[col] = df_fonte.groupby(agrup_sem_mes)[col].max().sum()
                            else:
                                t_fonte[col] = df_fonte[col].max()
                        else:
                            t_fonte[col] = df_fonte[col].max()
                    else:
                        if df_bruto is not None and meta is not None:
                            col_b = meta['col_beneficiario']
                            col_s = meta['col_sexo']
                            df_bruto_fonte = df_bruto[df_bruto[col_fonte] == fonte]
                            c_lower = str(col).strip().lower()
                            val = str(col).strip().upper()
                            if "benef" in c_lower:
                                t_fonte[col] = df_bruto_fonte[col_b].nunique()
                            elif val.startswith('F') and col_s:
                                t_fonte[col] = df_bruto_fonte[df_bruto_fonte[col_s].astype(str).str.upper().str.startswith('F')][col_b].nunique()
                            elif val.startswith('M') and col_s:
                                t_fonte[col] = df_bruto_fonte[df_bruto_fonte[col_s].astype(str).str.upper().str.startswith('M')][col_b].nunique()
                            elif val.endswith('X'):
                                t_fonte[col] = df_bruto_fonte[df_bruto_fonte['categoria_vezes'] == val][col_b].nunique()
                            else:
                                t_fonte[col] = df_fonte[col].sum()
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
            if is_cumulativo:
                if col_mes:
                    agrup_sem_mes = [c for c in colunas_agrupamento if c != col_mes and c in df_resultado.columns]
                    if agrup_sem_mes:
                        t_geral[col] = df_resultado.groupby(agrup_sem_mes)[col].max().sum()
                    else:
                        t_geral[col] = df_resultado[col].max()
                else:
                    t_geral[col] = df_resultado[col].max()
            else:
                if df_bruto is not None and meta is not None:
                    col_b = meta['col_beneficiario']
                    col_s = meta['col_sexo']
                    c_lower = str(col).strip().lower()
                    val = str(col).strip().upper()
                    if "benef" in c_lower:
                        t_geral[col] = df_bruto[col_b].nunique()
                    elif val.startswith('F') and col_s:
                        t_geral[col] = df_bruto[df_bruto[col_s].astype(str).str.upper().str.startswith('F')][col_b].nunique()
                    elif val.startswith('M') and col_s:
                        t_geral[col] = df_bruto[df_bruto[col_s].astype(str).str.upper().str.startswith('M')][col_b].nunique()
                    elif val.endswith('X'):
                        t_geral[col] = df_bruto[df_bruto['categoria_vezes'] == val][col_b].nunique()
                    else:
                        t_geral[col] = df_resultado[col].sum()
                else:
                    t_geral[col] = df_resultado[col].sum()
        elif col in colunas_agrupamento and col != primeira_col:
            t_geral[col] = extract_unique_items(df_resultado[col])
        else:
            if col not in t_geral: t_geral[col] = ""
            
    linhas_totais.append(t_geral)
    
    df_totais = pd.DataFrame(linhas_totais)
    df_completo = pd.concat([df_resultado, df_totais], ignore_index=True)
    return df_completo, df_totais
import unicodedata

def normalize_text(text):
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    return text.lower().strip()

def processar_relatorio(df, template):
    colunas_df = df.columns.tolist()
    col_agrupamento = template["colunas_agrupamento"]
    col_metricas = template["colunas_metricas"]
    
    if not col_agrupamento:
        raise ValueError("O template deve ter pelo menos uma coluna de agrupamento.")
        
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
        PAGAMENTOS=(col_beneficiario, 'count'),
        VALOR_PAGO=(col_valor, 'sum'),
        BENEF_DISTINTOS=(col_beneficiario, 'nunique')
    )
    
    if col_sexo:
        df_sexo_base = df.copy()
        df_sexo_base[col_sexo] = df_sexo_base[col_sexo].fillna("SEM_GENERO").replace("", "SEM_GENERO")
        agrupamento_sexo = list(dict.fromkeys(col_agrupamento_reais + [col_beneficiario, col_sexo]))
        df_sexo = df_sexo_base.drop_duplicates(subset=agrupamento_sexo)
        sexo_pivot = pd.pivot_table(df_sexo, index=col_agrupamento_reais, columns=col_sexo, values=col_beneficiario, aggfunc='nunique', fill_value=0)
        
        for sexo_col in sexo_pivot.columns:
            val = str(sexo_col).strip().upper()
            if val.startswith('F'):
                resumo_basico['F'] = sexo_pivot[sexo_col]
            elif val.startswith('M'):
                resumo_basico['M'] = sexo_pivot[sexo_col]
            else:
                nome_col = f"Sexo_{val}" if val != "SEM_GENERO" else "Sem_Gênero"
                resumo_basico[nome_col] = sexo_pivot[sexo_col]
                
    # Abordagem 1: Frequência Progressiva (Parcelas)
    df_freq = df.copy()
    colunas_ordenacao = [c for c in col_agrupamento_reais if any(k in normalize_text(c) for k in ["ano", "mes", "mês", "data"])]
    if colunas_ordenacao:
        df_freq = df_freq.sort_values(by=colunas_ordenacao)
        
    df_freq['vezes'] = df_freq.groupby(col_beneficiario).cumcount() + 1
    df_freq['categoria_vezes'] = df_freq['vezes'].astype(str) + 'X'
    freq_pivot = pd.pivot_table(df_freq, index=col_agrupamento_reais, columns='categoria_vezes', values=col_beneficiario, aggfunc='nunique', fill_value=0)
    
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
            
    df_mensal = relatorio_final.copy()
    df_cumulativo = relatorio_final.copy()
    
    col_mes = None
    for col in col_agrupamento:
        if 'mes' in col.lower() or 'mês' in col.lower():
            col_mes = col
            break
            
    if col_mes:
        def extract_num(val):
            try:
                import re
                val_str = str(val).lower()
                # 1. Tentar encontrar números (ex: "1-Janeiro")
                nums = re.findall(r'\d+', val_str)
                if nums:
                    return float(nums[0])
                
                # 2. Se não tiver números (ex: "Junho, Julho, Agosto"), procurar o nome do mês
                meses_map = {
                    'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6,
                    'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12
                }
                for mes_chave, num in meses_map.items():
                    if mes_chave in val_str:
                        return float(num)
                        
                return 0.0
            except:
                return 0.0
                
        df_cumulativo['_sort_mes'] = df_cumulativo[col_mes].apply(extract_num)
        
        col_agrup_sem_mes = [c for c in col_agrupamento if c != col_mes]
        numeric_cols = [c for c in df_cumulativo.columns if c in col_metricas and pd.api.types.is_numeric_dtype(df_cumulativo[c])]
        
        # Ordenar pelos agrupamentos base e depois pelo mês, para o cumsum fazer sentido!
        df_cumulativo = df_cumulativo.sort_values(by=col_agrup_sem_mes + ['_sort_mes'])
        
        df_cumulativo[numeric_cols] = df_cumulativo.groupby(col_agrup_sem_mes)[numeric_cols].cumsum()
        df_cumulativo = df_cumulativo.drop(columns=['_sort_mes'])
        
        # Renomear adicionando _ACUM como pedido pelo utilizador
        rename_acum = {c: f"{c}_ACUM" for c in numeric_cols}
        df_cumulativo = df_cumulativo.rename(columns=rename_acum)
    
    df_freq_renomeado = df_freq.rename(columns=rename_dict)
    meta_info = {
        'col_beneficiario': rename_dict.get(col_beneficiario, col_beneficiario),
        'col_sexo': rename_dict.get(col_sexo, col_sexo) if col_sexo else None
    }
    return df_mensal, df_cumulativo, df_freq_renomeado, meta_info

# =========================================================
# PÁGINA 1: CARREGAR & EDITAR DADOS
# =========================================================
if pagina == PAGINAS[0]:
    st.markdown("### " + "📥 1. Carregar Dados")
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
                    
                    template_name = "modelo de tabela globalizadovf_final_xls"
                    if template_name not in st.session_state.templates:
                        template_name = list(st.session_state.templates.keys())[0]
                    template = st.session_state.templates[template_name]
                    
                    df_mensal, df_cumulativo, df_bruto_mapeado, meta_info = processar_relatorio(st.session_state.df_editado.copy(), template)
                    st.session_state.relatorio_final = df_mensal
                    st.session_state.relatorio_cumulativo = df_cumulativo
                    st.session_state.col_agrupamento = template["colunas_agrupamento"]
                    st.session_state.df_bruto_mapeado = df_bruto_mapeado
                    st.session_state.meta_info = meta_info
                    
                    st.success("Ficheiro processado e pronto para relatório!")
                except Exception as e:
                    st.error(f"Erro ao ler e processar o ficheiro: {e}")
                    
    if st.session_state.df_editado is not None:
        st.success("✅ Dados em bruto importados com sucesso! (Modo de Apenas Leitura)")
        st.dataframe(st.session_state.df_editado, use_container_width=True, height=500, hide_index=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Avançar para Relatórios ➡️", use_container_width=True, type="primary"):
                st.session_state.pagina_atual = PAGINAS[1]
                st.rerun()

# =========================================================
# PÁGINA 2: GERAR RELATÓRIO
# =========================================================
elif pagina == PAGINAS[1]:
    st.markdown("### 📑 Relatórios de Pagamentos")
    
    if st.session_state.df_editado is None:
        st.warning("⚠️ Volte à primeira página e carregue um ficheiro Excel.")
    elif st.session_state.relatorio_final is not None:
        with st.expander("🔍 Filtros de Relatório", expanded=True):
            st.markdown("<span id='filters-sticky-hook'></span>", unsafe_allow_html=True)
            rel_display = st.session_state.relatorio_final.copy()
            rel_cumul_display = st.session_state.relatorio_cumulativo.copy()
            df_bruto_filtrado = st.session_state.df_bruto_mapeado.copy() if hasattr(st.session_state, 'df_bruto_mapeado') else None
            meta_info = st.session_state.meta_info if hasattr(st.session_state, 'meta_info') else None
        
            filtros_aplicados = []
            if len(st.session_state.col_agrupamento) > 0:
                agrupamentos = st.session_state.col_agrupamento
                cols_per_row = 3
                
                for i in range(0, len(agrupamentos), cols_per_row):
                    row_cols = st.columns(cols_per_row)
                    for j, col in enumerate(agrupamentos[i:i+cols_per_row]):
                        with row_cols[j]:
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
                                
                            selecao = st.multiselect(f"{col}", opcoes, placeholder="Seleccionar...")
                            
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
                                    
                                    if df_bruto_filtrado is not None:
                                        mask_bruto = df_bruto_filtrado[col].astype(str).apply(
                                            lambda x: any(sel in [m.strip() for m in x.split(',')] for sel in selecao)
                                        )
                                        df_bruto_filtrado = df_bruto_filtrado[mask_bruto]
                                else:
                                    rel_display = rel_display[rel_display[col].astype(str).isin(selecao)]
                                    rel_cumul_display = rel_cumul_display[rel_cumul_display[col].astype(str).isin(selecao)]
                                    if df_bruto_filtrado is not None:
                                        df_bruto_filtrado = df_bruto_filtrado[df_bruto_filtrado[col].astype(str).isin(selecao)]
                                    
                                filtros_aplicados.append(f"**{col}:** {', '.join(selecao)}")
                        
        st.session_state.relatorio_filtrado = rel_display
        st.session_state.relatorio_cumul_filtrado = rel_cumul_display
        st.session_state.filtros_aplicados_texto = filtros_aplicados
        
        rel_display_completo, rel_display_totais = adicionar_linha_totais(
            rel_display, 
            st.session_state.col_agrupamento, 
            is_cumulativo=False, 
            df_bruto=df_bruto_filtrado if 'df_bruto_filtrado' in locals() else None, 
            meta=meta_info if 'meta_info' in locals() else None
        )
        
        # Tabela Cumulativa usa os mesmos totais da Mensal, mas precisamos de garantir que os nomes das colunas
        # batem certo porque a tabela cumulativa tem o sufixo _ACUM.
        rel_cumul_totais = rel_display_totais.copy()
        
        rename_acum_totais = {}
        for c in rel_cumul_totais.columns:
            if c not in st.session_state.col_agrupamento and c != rel_cumul_totais.columns[0]:
                rename_acum_totais[c] = f"{c}_ACUM"
                
        rel_cumul_totais = rel_cumul_totais.rename(columns=rename_acum_totais)
        
        rel_cumul_display_completo = pd.concat([rel_cumul_display, rel_cumul_totais], ignore_index=True)
        
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
        
        def formatar_excel(writer, df_to_write, sheet_name, filtros):
            df_to_write.to_excel(writer, index=False, sheet_name=sheet_name)
            worksheet = writer.sheets[sheet_name]
            
            # Fixar cabeçalho
            worksheet.freeze_panes = 'A2'
            
            # Destacar linha de totais (a última linha)
            try:
                from openpyxl.styles import PatternFill, Font
                fill_totais = PatternFill(start_color="FFE6E6", end_color="FFE6E6", fill_type="solid")
                font_totais = Font(bold=True)
                
                max_row = worksheet.max_row
                for col in range(1, worksheet.max_column + 1):
                    cell = worksheet.cell(row=max_row, column=col)
                    cell.fill = fill_totais
                    cell.font = font_totais
            except:
                pass
                
            # Adicionar filtros numa aba separada se não existir
            if filtros and "Filtros" not in writer.sheets:
                df_filtros = pd.DataFrame({"Filtros Aplicados": filtros})
                df_filtros.to_excel(writer, index=False, sheet_name="Filtros")
                try:
                    ws_filtros = writer.sheets["Filtros"]
                    ws_filtros.column_dimensions['A'].width = 100
                except:
                    pass

        tab1, tab2 = st.tabs(["📊 Tabela 1 — PAGAMENTOS MENSAL", "📈 Tabela 2 — PAGAMENTOS CUMULATIVO"])
        
        with tab1:
            styled_display = rel_display.style.format(format_dict)
            styled_totais = rel_display_totais.style.apply(destacar_totais_isolados, axis=1).format(format_dict).hide(axis="index")
            
            st.dataframe(styled_display, height=400, use_container_width=True, hide_index=True)
            st.write("📌 **TOTAIS GERAIS DOS DADOS ACIMA:**")
            st.dataframe(styled_totais, use_container_width=True, hide_index=True)
            
            buffer1 = io.BytesIO()
            with pd.ExcelWriter(buffer1, engine='openpyxl') as writer:
                formatar_excel(writer, rel_display_completo, 'PAGAMENTOS_MENSAL', st.session_state.get('filtros_aplicados_texto', []))
            
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
            
            
            buffer2 = io.BytesIO()
            with pd.ExcelWriter(buffer2, engine='openpyxl') as writer:
                formatar_excel(writer, rel_cumul_display_completo, 'PAGAMENTOS_CUMULATIVO', st.session_state.get('filtros_aplicados_texto', []))
            
            st.download_button(
                label="📥 Descarregar Tabela 2 Completa (Cumulativo)",
                data=buffer2.getvalue(),
                file_name="PAGAMENTOS_CUMULATIVO.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# =========================================================
# PÁGINA 3: DASHBOARD VISUAL
# =========================================================
elif pagina == PAGINAS[2]:
    st.markdown("### " + "📈 3. Dashboard Visual")
    
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
        total_valor = pd.to_numeric(rel_viz['VALOR_PAGO'], errors='coerce').sum() if 'VALOR_PAGO' in rel_viz.columns else 0
        total_benef = pd.to_numeric(rel_viz['BENEF_DISTINTOS'], errors='coerce').sum() if 'BENEF_DISTINTOS' in rel_viz.columns else 0
        total_pags = pd.to_numeric(rel_viz['PAGAMENTOS'], errors='coerce').sum() if 'PAGAMENTOS' in rel_viz.columns else 0
        
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
            freq_cols = [c for c in ['1X', '2X', '3X', '4X', '5X', '6X', '7X', '8X', '9X', '10X', '11X', '12X'] if c in rel_viz.columns]
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
                if 'BENEF_DISTINTOS' in rel_viz.columns:
                    rel_viz['BENEF_DISTINTOS'] = pd.to_numeric(rel_viz['BENEF_DISTINTOS'], errors='coerce').fillna(0)
                    graf_distrito = rel_viz.groupby(eixo_x)[['BENEF_DISTINTOS']].sum()
                    st.bar_chart(graf_distrito)

# =========================================================
# BOTÕES DE NAVEGAÇÃO DE PÁGINA (Fixos em baixo)
# =========================================================


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


st.markdown("<div id='nav-buttons-hook'></div>", unsafe_allow_html=True)

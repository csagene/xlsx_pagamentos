import base64
with open("app_dashboard.py", "rb") as f:
    text = f.read().decode('utf-8')

import re
# We want to replace from def adicionar_linha_totais(df_resultado, colunas_agrupamento):
# up to import unicodedata

start = text.find("def adicionar_linha_totais(df_resultado, colunas_agrupamento):")
if start == -1:
    start = text.find("def adicionar_linha_totais(df_resultado")
end = text.find("import unicodedata")

new_func = """def adicionar_linha_totais(df_resultado, colunas_agrupamento, is_cumulativo=False):
    df_resultado = df_resultado.copy()
    if df_resultado.empty:
        return df_resultado, __import__('pandas').DataFrame()
        
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
                elif __import__('pandas').api.types.is_numeric_dtype(df_resultado[col]) and col not in colunas_agrupamento:
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
        elif __import__('pandas').api.types.is_numeric_dtype(df_resultado[col]) and col not in colunas_agrupamento:
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
                t_geral[col] = df_resultado[col].sum()
        elif col in colunas_agrupamento and col != primeira_col:
            t_geral[col] = extract_unique_items(df_resultado[col])
        else:
            if col not in t_geral: t_geral[col] = ""
            
    linhas_totais.append(t_geral)
    
    df_totais = __import__('pandas').DataFrame(linhas_totais)
    df_completo = __import__('pandas').concat([df_resultado, df_totais], ignore_index=True)
    return df_completo, df_totais

"""
text = text[:start] + new_func + text[end:]
with open("app_dashboard.py", "wb") as f:
    f.write(text.encode("utf-8"))

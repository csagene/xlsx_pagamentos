# -*- coding: utf-8 -*-
import sys

def main():
    with open("app_dashboard.py", "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update adicionar_linha_totais signature
    content = content.replace(
        "def adicionar_linha_totais(df_resultado, colunas_agrupamento, is_cumulativo=False):",
        "def adicionar_linha_totais(df_resultado, colunas_agrupamento, is_cumulativo=False, df_bruto=None, meta=None):"
    )
    
    # 2. Update logic for t_fonte
    fonte_target = """                elif pd.api.types.is_numeric_dtype(df_resultado[col]) and col not in colunas_agrupamento:
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
                        t_fonte[col] = df_fonte[col].sum()"""
                        
    fonte_replace = """                elif pd.api.types.is_numeric_dtype(df_resultado[col]) and col not in colunas_agrupamento:
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
                            t_fonte[col] = df_fonte[col].sum()"""
    
    content = content.replace(fonte_target, fonte_replace)
    
    # 3. Update logic for t_geral
    geral_target = """        elif pd.api.types.is_numeric_dtype(df_resultado[col]) and col not in colunas_agrupamento:
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
                t_geral[col] = df_resultado[col].sum()"""
                
    geral_replace = """        elif pd.api.types.is_numeric_dtype(df_resultado[col]) and col not in colunas_agrupamento:
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
                    t_geral[col] = df_resultado[col].sum()"""
                    
    content = content.replace(geral_target, geral_replace)
    
    # 4. Update processar_relatorio return
    processar_target = """    df_freq_renomeado = df_freq.rename(columns=rename_dict)
    return df_mensal, df_cumulativo, df_freq_renomeado"""
    
    processar_target_fallback = """    return df_mensal, df_cumulativo"""
    
    processar_replace = """    df_freq_renomeado = df_freq.rename(columns=rename_dict)
    meta_info = {
        'col_beneficiario': rename_dict.get(col_beneficiario, col_beneficiario),
        'col_sexo': rename_dict.get(col_sexo, col_sexo) if col_sexo else None
    }
    return df_mensal, df_cumulativo, df_freq_renomeado, meta_info"""
    
    if processar_target in content:
        content = content.replace(processar_target, processar_replace)
    else:
        content = content.replace(processar_target_fallback, processar_replace)
        
    # 5. Update call to processar_relatorio
    call_target = """                    df_mensal, df_cumulativo = processar_relatorio(st.session_state.df_editado.copy(), template)
                    st.session_state.relatorio_final = df_mensal
                    st.session_state.relatorio_cumulativo = df_cumulativo
                    st.session_state.col_agrupamento = template["colunas_agrupamento"]"""
                    
    call_replace = """                    df_mensal, df_cumulativo, df_bruto_mapeado, meta_info = processar_relatorio(st.session_state.df_editado.copy(), template)
                    st.session_state.relatorio_final = df_mensal
                    st.session_state.relatorio_cumulativo = df_cumulativo
                    st.session_state.col_agrupamento = template["colunas_agrupamento"]
                    st.session_state.df_bruto_mapeado = df_bruto_mapeado
                    st.session_state.meta_info = meta_info"""
                    
    content = content.replace(call_target, call_replace)
    
    # 6. Update PÁGINA 2 filtering to include df_bruto
    pag2_target = """            rel_display = st.session_state.relatorio_final.copy()
            rel_cumul_display = st.session_state.relatorio_cumulativo.copy()
        
            filtros_aplicados = []"""
            
    pag2_replace = """            rel_display = st.session_state.relatorio_final.copy()
            rel_cumul_display = st.session_state.relatorio_cumulativo.copy()
            df_bruto_filtrado = st.session_state.df_bruto_mapeado.copy() if hasattr(st.session_state, 'df_bruto_mapeado') else None
            meta_info = st.session_state.meta_info if hasattr(st.session_state, 'meta_info') else None
        
            filtros_aplicados = []"""
            
    content = content.replace(pag2_target, pag2_replace)
    
    filter1_target = """                                    mask_cumul = rel_cumul_display[col].astype(str).apply(
                                        lambda x: any(sel in [m.strip() for m in x.split(',')] for sel in selecao)
                                    )
                                    rel_cumul_display = rel_cumul_display[mask_cumul]
                                else:"""
                                
    filter1_replace = """                                    mask_cumul = rel_cumul_display[col].astype(str).apply(
                                        lambda x: any(sel in [m.strip() for m in x.split(',')] for sel in selecao)
                                    )
                                    rel_cumul_display = rel_cumul_display[mask_cumul]
                                    
                                    if df_bruto_filtrado is not None:
                                        mask_bruto = df_bruto_filtrado[col].astype(str).apply(
                                            lambda x: any(sel in [m.strip() for m in x.split(',')] for sel in selecao)
                                        )
                                        df_bruto_filtrado = df_bruto_filtrado[mask_bruto]
                                else:"""
                                
    content = content.replace(filter1_target, filter1_replace)
    
    filter2_target = """                                else:
                                    rel_display = rel_display[rel_display[col].astype(str).isin(selecao)]
                                    rel_cumul_display = rel_cumul_display[rel_cumul_display[col].astype(str).isin(selecao)]
                                    
                                filtros_aplicados.append(f"**{col}:** {', '.join(selecao)}")"""
                                
    filter2_replace = """                                else:
                                    rel_display = rel_display[rel_display[col].astype(str).isin(selecao)]
                                    rel_cumul_display = rel_cumul_display[rel_cumul_display[col].astype(str).isin(selecao)]
                                    if df_bruto_filtrado is not None:
                                        df_bruto_filtrado = df_bruto_filtrado[df_bruto_filtrado[col].astype(str).isin(selecao)]
                                    
                                filtros_aplicados.append(f"**{col}:** {', '.join(selecao)}")"""
                                
    content = content.replace(filter2_target, filter2_replace)
    
    call_totais_target = """        rel_display_completo, rel_display_totais = adicionar_linha_totais(rel_display, st.session_state.col_agrupamento, is_cumulativo=False)"""
    
    call_totais_replace = """        rel_display_completo, rel_display_totais = adicionar_linha_totais(
            rel_display, 
            st.session_state.col_agrupamento, 
            is_cumulativo=False, 
            df_bruto=df_bruto_filtrado if 'df_bruto_filtrado' in locals() else None, 
            meta=meta_info if 'meta_info' in locals() else None
        )"""
        
    content = content.replace(call_totais_target, call_totais_replace)

    with open("app_dashboard.py", "w", encoding="utf-8") as f:
        f.write(content)

    print("Substituições concluídas.")

if __name__ == "__main__":
    main()

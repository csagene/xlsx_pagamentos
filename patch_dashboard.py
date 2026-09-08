import re

with open("app_dashboard.py", "r", encoding="utf-8") as f:
    content = f.read()

# Define the new Dashboard section code
new_dashboard_code = '''elif pagina == PAGINAS[2]:
    st.markdown("### " + "📈 3. Dashboard Visual")
    
    import plotly.express as px
    import plotly.graph_objects as go
    
    if st.session_state.relatorio_cumulativo is None:
        st.warning("⚠️ Primeiro, vá à secção 'Gerar Relatório' e processe a tabela.")
    else:
        # 1. Obter Tabela Cumulativa (com ou sem filtros da Página 2)
        if "relatorio_cumul_filtrado" in st.session_state and st.session_state.relatorio_cumul_filtrado is not None:
            rel_viz = st.session_state.relatorio_cumul_filtrado.copy()
        else:
            rel_viz = st.session_state.relatorio_cumulativo.copy()
            
        st.write("*(Nota: Os gráficos respondem aos filtros aplicados na página '2. Gerar Relatório'.)*")
        
        filtros_txt = st.session_state.get('filtros_aplicados_texto', [])
        if filtros_txt:
            st.info("🎯 **Filtros Ativos:** " + " | ".join(filtros_txt))
        else:
            st.info("🎯 **Filtros Ativos:** Nenhum (A mostrar todos os dados acumulados)")
            
        st.divider()
        
        # 2. Calcular KPIs (Para dados cumulativos, o "Total" correto é o máximo de cada partição,
        # que é o que a função adicionar_linha_totais já faz por nós)
        df_bruto_atual = st.session_state.df_bruto_mapeado if hasattr(st.session_state, 'df_bruto_mapeado') else None
        meta_info = st.session_state.meta_info if hasattr(st.session_state, 'meta_info') else None
        
        # Garantir que temos col_agrupamento
        col_agrupamento = st.session_state.get('col_agrupamento', [])
        
        _, df_totais = adicionar_linha_totais(
            rel_viz, 
            col_agrupamento, 
            is_cumulativo=True, 
            df_bruto=df_bruto_atual, 
            meta=meta_info
        )
        
        # 3. Extrair Valores para os KPIs
        def extract_kpi(col_name):
            if col_name in df_totais.columns:
                val = df_totais[col_name].iloc[0]
                return pd.to_numeric(val, errors='coerce') if val != '' else 0
            return 0

        total_valor = extract_kpi('VALOR_PAGO_ACUM')
        total_benef = extract_kpi('BENEF_DISTINTOS_ACUM')
        total_pags = extract_kpi('PAGAMENTOS_ACUM')
        total_f = extract_kpi('F_ACUM')
        total_m = extract_kpi('M_ACUM')
        
        # Encontrar total outros generos (se existirem)
        total_outros = 0
        for col in df_totais.columns:
            if col.startswith("Sexo_") or col == "Sem_Gênero":
                total_outros += extract_kpi(col)
        
        # Formatador de MT
        def formata_mt_kpi(val):
            if pd.isna(val): return "0 MT"
            s = f"{float(val):,.2f}"
            return s.replace(",", "X").replace(".", ",").replace("X", " ") + " MT"
            
        # 4. Renderizar Cartões (KPIs)
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("💰 Valor Distribuído Acumulado", formata_mt_kpi(total_valor))
        kpi2.metric("👥 Beneficiários Únicos", f"{float(total_benef):,.0f}")
        kpi3.metric("💳 Pagamentos Efetuados", f"{float(total_pags):,.0f}")
        
        st.write("")
        
        kpi_m, kpi_f, kpi_o = st.columns(3)
        kpi_m.metric("👨 Homens (M)", f"{float(total_m):,.0f}")
        kpi_f.metric("👩 Mulheres (F)", f"{float(total_f):,.0f}")
        kpi_o.metric("👤 Gênero Não Informado", f"{float(total_outros):,.0f}")
        
        st.divider()
        
        # 5. Gráficos Plotly
        
        # Descobrir a coluna de Mês
        col_m = next((c for c in col_agrupamento if "mes" in str(c).lower() or "mês" in str(c).lower()), None)
        
        if col_m and not rel_viz.empty:
            # Ordenar temporariamente pelos meses para o gráfico de linha/área
            def _get_sort_m(val):
                val_str = str(val).lower()
                meses_map = {'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6, 'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12}
                for k, v in meses_map.items():
                    if k in val_str: return v
                return 0
                
            rel_viz['_sort_m'] = rel_viz[col_m].apply(_get_sort_m)
            graf_tempo = rel_viz.groupby([col_m, '_sort_m'])[['VALOR_PAGO_ACUM', 'PAGAMENTOS_ACUM']].sum().reset_index()
            graf_tempo = graf_tempo.sort_values('_sort_m')
            
            if not graf_tempo.empty:
                st.markdown("#### 📈 Evolução do Valor Pago (Acumulado)")
                fig_area = px.area(
                    graf_tempo, 
                    x=col_m, 
                    y='VALOR_PAGO_ACUM',
                    labels={'VALOR_PAGO_ACUM': 'Valor Distribuído (MT)', col_m: 'Mês'},
                    color_discrete_sequence=["#0083B8"]
                )
                fig_area.update_layout(margin=dict(l=0, r=0, t=30, b=0), xaxis_title=None)
                st.plotly_chart(fig_area, use_container_width=True)
                
        st.write("")
        
        # Gráficos Secundários
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("#### 🚻 Proporção por Gênero")
            labels_sexo = []
            valores_sexo = []
            
            if total_f > 0:
                labels_sexo.append('Mulheres (F)')
                valores_sexo.append(total_f)
            if total_m > 0:
                labels_sexo.append('Homens (M)')
                valores_sexo.append(total_m)
            if total_outros > 0:
                labels_sexo.append('Outros')
                valores_sexo.append(total_outros)
                
            if sum(valores_sexo) > 0:
                fig_pie = px.pie(
                    names=labels_sexo, 
                    values=valores_sexo, 
                    hole=0.4,
                    color_discrete_sequence=["#FF4B4B", "#0083B8", "#888888"]
                )
                fig_pie.update_layout(margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Sem dados de gênero para exibir.")
                
        with c2:
            freq_cols = [c for c in ['1X_ACUM', '2X_ACUM', '3X_ACUM', '4X_ACUM', '5X_ACUM', '6X_ACUM', '7X_ACUM', '8X_ACUM', '9X_ACUM', '10X_ACUM', '11X_ACUM', '12X_ACUM'] if c in df_totais.columns]
            if freq_cols:
                st.markdown("#### 🔄 Frequência de Pagamentos (Vezes)")
                freq_vals = [extract_kpi(c) for c in freq_cols]
                
                # Filtrar os que têm > 0
                freq_data = pd.DataFrame({'Vezes': [c.replace('_ACUM', '') for c in freq_cols], 'Total': freq_vals})
                freq_data = freq_data[freq_data['Total'] > 0]
                
                if not freq_data.empty:
                    fig_bar = px.bar(
                        freq_data, 
                        y='Vezes', 
                        x='Total', 
                        orientation='h',
                        text='Total',
                        color_discrete_sequence=["#28a745"]
                    )
                    fig_bar.update_layout(margin=dict(l=0, r=0, t=30, b=0), yaxis={'categoryorder':'total ascending'}, xaxis_title=None, yaxis_title=None)
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.info("Sem dados de frequência para exibir.")
                    
        st.write("")
        st.divider()
        
        # Treemap por Distrito / Província
        if col_agrupamento:
            eixo_x = col_agrupamento[-1]
            for col in col_agrupamento:
                if "distrito" in col.lower() or "deleg" in col.lower() or "prov" in col.lower():
                    eixo_x = col
                    break
                    
            st.markdown(f"#### 📍 Distribuição Geográfica de Pagamentos Acumulados ({eixo_x})")
            if not rel_viz.empty and 'VALOR_PAGO_ACUM' in rel_viz.columns:
                # Group by to find max value per district
                graf_geo = rel_viz.groupby(eixo_x)['VALOR_PAGO_ACUM'].max().reset_index()
                graf_geo = graf_geo[graf_geo['VALOR_PAGO_ACUM'] > 0]
                
                if not graf_geo.empty:
                    fig_tree = px.treemap(
                        graf_geo, 
                        path=[eixo_x], 
                        values='VALOR_PAGO_ACUM',
                        color='VALOR_PAGO_ACUM',
                        color_continuous_scale='Blues'
                    )
                    fig_tree.update_layout(margin=dict(l=0, r=0, t=30, b=0))
                    st.plotly_chart(fig_tree, use_container_width=True)
                else:
                    st.info("Sem dados geográficos para exibir.")

# =========================================================
# BOTÕES DE NAVEGAÇÃO DE PÁGINA (Fixos em baixo)
# ========================================================='''

# Find the start of Dashboard section
start_idx = content.find("elif pagina == PAGINAS[2]:")
end_idx = content.find("# =========================================================", start_idx + 1)
end_idx = content.find("# BOTÕES DE NAVEGAÇÃO DE PÁGINA", end_idx)

# Go back up to the start of the comment block for BOTÕES DE NAVEGAÇÃO
end_idx = content.rfind("# =========================================================", 0, end_idx)

if start_idx != -1 and end_idx != -1:
    new_content = content[:start_idx] + new_dashboard_code + content[end_idx:]
    with open("app_dashboard.py", "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Dashboard visual updated successfully!")
else:
    print("Could not find the target section to replace.")

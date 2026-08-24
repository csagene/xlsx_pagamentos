import streamlit as st
import pandas as pd
import numpy as np
import io

# ---------------------------------------------------------
# CONFIGURAÇÃO GERAL
# ---------------------------------------------------------
st.set_page_config(page_title="Sistema de Relatórios INAS", page_icon="📊", layout="wide")

# Inicializar variáveis na memória (Session State)
if "df" not in st.session_state:
    st.session_state.df = None
if "relatorio_final" not in st.session_state:
    st.session_state.relatorio_final = None
if "col_agrupamento" not in st.session_state:
    st.session_state.col_agrupamento = []

# ---------------------------------------------------------
# MENU DE NAVEGAÇÃO LATERAL
# ---------------------------------------------------------
PAGINAS = [
    "📥 1. Carregar Dados (Base)", 
    "📑 2. Relatório Detalhado", 
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
if st.session_state.df is not None:
    st.sidebar.success(f"✅ Dados carregados em memória ({len(st.session_state.df)} registos)")
else:
    st.sidebar.warning("⚠️ Nenhum dado carregado")

# Função útil para adicionar a linha do "TOTAL"
def adicionar_linha_totais(df_resultado, colunas_agrupamento):
    totais = {}
    for col in df_resultado.columns:
        # A primeira coluna de agrupamento recebe a palavra "TOTAL GERAL"
        if len(colunas_agrupamento) > 0 and col == colunas_agrupamento[0]:
            totais[col] = "TOTAL GERAL"
        # As restantes colunas de texto ficam em branco
        elif col in colunas_agrupamento:
            totais[col] = ""
        # As colunas numéricas são somadas
        elif pd.api.types.is_numeric_dtype(df_resultado[col]):
            totais[col] = df_resultado[col].sum()
        else:
            totais[col] = ""
    
    df_totais = pd.DataFrame([totais])
    return pd.concat([df_resultado, df_totais], ignore_index=True)


# =========================================================
# PÁGINA 1: CARREGAR DADOS
# =========================================================
if pagina == "📥 1. Carregar Dados (Base)":
    st.title("📥 Carregar Ficheiro de Pagamentos")
    
    uploaded_file = st.file_uploader("Carregue o ficheiro Excel", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        # Só processa se for um ficheiro novo para não repetir leituras desnecessárias
        if st.session_state.get('last_file_name') != uploaded_file.name:
            with st.spinner("⏳ A analisar o ficheiro"):
                try:
                    # 1. Ler as primeiras linhas para descobrir onde está o cabeçalho
                    uploaded_file.seek(0)
                    df_preview = pd.read_excel(uploaded_file, header=None, nrows=30)
                    
                    linha_cabecalho = 0
                    for i, row in df_preview.iterrows():
                        non_nulls = row.dropna()
                        # Uma linha de cabeçalho costuma ter várias colunas preenchidas com texto
                        if len(non_nulls) >= 3:
                            strings = [x for x in non_nulls if isinstance(x, str)]
                            if len(strings) >= len(non_nulls) * 0.5:
                                linha_cabecalho = i
                                break
                    
                    # 2. Ler o ficheiro a sério a partir da linha descoberta
                    uploaded_file.seek(0)
                    df = pd.read_excel(uploaded_file, header=linha_cabecalho)
                    
                    # Limpar nomes das colunas e garantir que não há duplicados
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
                    
                    # Guardar na memória
                    st.session_state.df = df
                    st.session_state.relatorio_final = None 
                    st.session_state.last_file_name = uploaded_file.name
                    
                except Exception as e:
                    st.error(f"Erro ao ler o ficheiro: {e}")
                    
        # Mostrar o sucesso imediatamente após o processamento (ou se já estiver em memória)
        if st.session_state.df is not None:
            st.success("✅ Ficheiro lido com sucesso!")
            st.subheader("Pré-visualização dos Dados (Primeiras Linhas)")
            st.dataframe(st.session_state.df.head(10), use_container_width=True)


# =========================================================
# PÁGINA 2: RELATÓRIO ESTRUTURADO
# =========================================================
elif pagina == "📑 2. Relatório Detalhado":
    st.title("📑 Relatório Organizado")
    
    if st.session_state.df is None:
        st.warning("⚠️ Volte à primeira página e carregue um ficheiro Excel.")
    else:
        df = st.session_state.df
        colunas = df.columns.tolist()
        # Mensagem informativa removida a pedido do utilizador
        
        colunas_padrao = ['Ano', 'Mês', 'Mes', 'Província', 'Provincia', 'Delegação', 'Delegacao', 'Distrito', 'Fonte', 'Programa', 'Implementador', 'Operador']
        default_agrupamento = [c for c in colunas if c in colunas_padrao or c.lower() in [p.lower() for p in colunas_padrao]]
        
        col_agrupamento = st.multiselect("1. Escolha as categorias principais (Agrupamento):", options=colunas, default=default_agrupamento)
        
        # Função para detetar colunas
        def detetar_coluna(lista_colunas, palavras_chave):
            for col in lista_colunas:
                if str(col).lower().strip() in palavras_chave: return col
            for col in lista_colunas:
                for p in palavras_chave:
                    if p in str(col).lower(): return col
            return None
            
        # Deteção invisível
        col_beneficiario = detetar_coluna(colunas, ['id', 'código', 'codigo', 'beneficiario', 'beneficiário', 'bi', 'nuit'])
        col_sexo = detetar_coluna(colunas, ['sexo', 'genero', 'género', 'sex'])
        col_valor = detetar_coluna(colunas, ['valor', 'pago', 'montante', 'dinheiro', 'total', 'unnamed'])
        
        # Proteção anti-falhas
        if not col_beneficiario: col_beneficiario = colunas[0]
        if not col_valor: col_valor = colunas[-1]
            
        if not col_agrupamento:
            st.error("Selecione pelo menos uma coluna de agrupamento.")
        else:
            with st.spinner("A organizar todos os cálculos em tempo real..."):
                try:
                    # 1. Agrupamento Básico
                    resumo_basico = df.groupby(col_agrupamento).agg(
                        Pagamentos=(col_beneficiario, 'count'),
                        Valor_Pago=(col_valor, 'sum'),
                        Benef_Distintos=(col_beneficiario, 'nunique')
                    )
                    
                    # 2. Sexo (Contar Mulheres, Homens e Sem Gênero)
                    colunas_geradas_sexo = []
                    if col_sexo:
                        df_sexo_base = df.copy()
                        # Preencher espaços vazios para não serem ignorados
                        df_sexo_base[col_sexo] = df_sexo_base[col_sexo].fillna("SEM_GENERO").replace("", "SEM_GENERO")
                        
                        agrupamento_sexo = list(dict.fromkeys(col_agrupamento + [col_beneficiario, col_sexo]))
                        df_sexo = df_sexo_base.drop_duplicates(subset=agrupamento_sexo)
                        sexo_pivot = pd.pivot_table(df_sexo, index=col_agrupamento, columns=col_sexo, values=col_beneficiario, aggfunc='nunique', fill_value=0)
                        
                        for sexo_col in sexo_pivot.columns:
                            val = str(sexo_col).strip().upper()
                            if val == 'F':
                                resumo_basico['F'] = sexo_pivot[sexo_col]
                                colunas_geradas_sexo.append('F')
                            elif val == 'M':
                                resumo_basico['M'] = sexo_pivot[sexo_col]
                                colunas_geradas_sexo.append('M')
                            else:
                                nome_col = f"Sexo_{val}" if val != "SEM_GENERO" else "Sem_Gênero"
                                resumo_basico[nome_col] = sexo_pivot[sexo_col]
                                colunas_geradas_sexo.append(nome_col)
                                
                    # 3. Frequência (1x, 2x, etc)
                    agrupamento_freq = list(dict.fromkeys(col_agrupamento + [col_beneficiario]))
                    freq_df = df.groupby(agrupamento_freq).size().reset_index(name='vezes')
                    freq_df['categoria_vezes'] = np.where(freq_df['vezes'] >= 4, '4+', freq_df['vezes'].astype(str) + 'x')
                    freq_pivot = pd.pivot_table(freq_df, index=col_agrupamento, columns='categoria_vezes', values=col_beneficiario, aggfunc='nunique', fill_value=0)
                    
                    # Junta tudo
                    relatorio_final = resumo_basico.join(freq_pivot).fillna(0).reset_index()
                    relatorio_final = relatorio_final.rename(columns={'Valor_Pago': 'Valor Pago', 'Benef_Distintos': 'Benef. Distintos'})
                    
                    for col in ['1x', '2x', '3x', '4+']:
                        if col not in relatorio_final.columns:
                            relatorio_final[col] = 0
                            
                    ordem_desejada = col_agrupamento + colunas_geradas_sexo + ['Benef. Distintos', '1x', '2x', '3x', '4+', 'Pagamentos', 'Valor Pago']
                    ordem_final = [c for c in ordem_desejada if c in relatorio_final.columns]
                    relatorio_final = relatorio_final[ordem_final]
                    
                    st.session_state.relatorio_final = relatorio_final
                    st.session_state.col_agrupamento = col_agrupamento
                    st.success("Tabela gerada e guardada em memória!")
                except Exception as e:
                    st.error(f"Erro ao processar: {e}")

        # Se o relatório já estiver gerado, apresentar Filtros e a Tabela
        if st.session_state.relatorio_final is not None:
            st.divider()
            st.subheader("🔍 Filtros em Cascata")
            st.markdown("Selecione opções abaixo para filtrar os detalhes. Os totais atualizarão automaticamente.")
            
            rel_display = st.session_state.relatorio_final.copy()
            
            # Criar até 4 caixas de filtros dinâmicos
            filtros_aplicados = []
            num_filtros = min(4, len(st.session_state.col_agrupamento))
            if num_filtros > 0:
                col_filtros = st.columns(num_filtros)
                for i, col in enumerate(st.session_state.col_agrupamento[:4]):
                    with col_filtros[i]:
                        # Opções limitam-se ao que já sobrou na tabela
                        opcoes = sorted(list(rel_display[col].astype(str).dropna().unique()))
                        selecao = st.multiselect(f"{col}:", opcoes)
                        if selecao:
                            rel_display = rel_display[rel_display[col].astype(str).isin(selecao)]
                            filtros_aplicados.append(f"**{col}:** {', '.join(selecao)}")
                            
            # Guardar a tabela filtrada no sistema para o Dashboard poder usá-la
            st.session_state.relatorio_filtrado = rel_display
            st.session_state.filtros_aplicados_texto = filtros_aplicados
            
            # Criar a linha de Totais Isolada
            df_totais_so = adicionar_linha_totais(rel_display, st.session_state.col_agrupamento).tail(1)
            
            # Formatação Visual para a Linha de Totais
            def destacar_totais_isolados(row):
                return ['font-weight: bold; background-color: #ffe6e6; border-top: 2px solid black'] * len(row)
            
            styled_totais = df_totais_so.style.apply(destacar_totais_isolados, axis=1)
            
            st.subheader("Tabela de Resultados")
            
            # 1. Tabela Principal (Com altura fixa para criar uma barra de scroll lateral)
            st.dataframe(rel_display, height=400, use_container_width=True)
            
            # 2. Linha de Totais Fixa (Aparece imediatamente abaixo, simulando um rodapé fixo)
            st.write("📌 **TOTAIS GERAIS DOS DADOS ACIMA:**")
            st.dataframe(styled_totais, use_container_width=True)
            
            # O Excel Exportado continua a ter a linha no fim, normalmente
            rel_display_com_totais = adicionar_linha_totais(rel_display, st.session_state.col_agrupamento)
            
            # Botão de Exportar
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
elif pagina == "📈 3. Dashboard Visual":
    st.title("📈 Visualizações e Gráficos")
    
    if st.session_state.relatorio_final is None:
        st.warning("⚠️ Primeiro, vá à secção de Relatório Detalhado e clique em 'Construir Tabela'.")
    else:
        # Puxar a tabela que foi gerada (e filtrada) no Passo 2
        if "relatorio_filtrado" in st.session_state and st.session_state.relatorio_filtrado is not None:
            rel_viz = st.session_state.relatorio_filtrado.copy()
        else:
            rel_viz = st.session_state.relatorio_final.copy()
            
        st.write("*(Nota: Os gráficos abaixo respondem automaticamente aos filtros que você aplicou na secção 'Relatório Organizado'.)*")
        
        filtros_txt = st.session_state.get('filtros_aplicados_texto', [])
        if filtros_txt:
            st.info("🎯 **Filtros Ativos:** " + " | ".join(filtros_txt))
        else:
            st.info("🎯 **Filtros Ativos:** Nenhum (A mostrar todos os dados)")
            
        st.divider()
        
        # 1. Indicadores Chave
        kpi1, kpi2, kpi3 = st.columns(3)
        total_valor = pd.to_numeric(rel_viz['Valor Pago'], errors='coerce').sum() if 'Valor Pago' in rel_viz.columns else 0
        total_benef = pd.to_numeric(rel_viz['Benef. Distintos'], errors='coerce').sum() if 'Benef. Distintos' in rel_viz.columns else 0
        total_pags = pd.to_numeric(rel_viz['Pagamentos'], errors='coerce').sum() if 'Pagamentos' in rel_viz.columns else 0
        
        kpi1.metric("💰 Valor Distribuído", f"{float(total_valor):,.2f}")
        kpi2.metric("👥 Beneficiários Únicos", f"{float(total_benef):,.0f}")
        kpi3.metric("💳 Ficheiros / Transações", f"{float(total_pags):,.0f}")
        
        st.write("") # Espaço em branco
        
        # KPIs Secundários (Género)
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
        
        # 2. Gráficos (Sexo e Frequência)
        c1, c2 = st.columns(2)
        with c1:
            if 'F' in rel_viz.columns or 'M' in rel_viz.columns or 'Sem_Gênero' in rel_viz.columns:
                st.write("**Proporção de Sexo (Incluindo não informados)**")
                
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
                    
                # Caso haja outras letras/erros na coluna de sexo no excel
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
                st.write("**Frequência de Pagamentos (Vezes que receberam)**")
                freq_data = pd.DataFrame({
                    'Vezes': freq_cols,
                    'Total': [pd.to_numeric(rel_viz[c], errors='coerce').sum() for c in freq_cols]
                }).set_index('Vezes')
                st.bar_chart(freq_data, color="#0083B8")
                
        # 3. Gráfico por Distrito / Delegação
        if st.session_state.col_agrupamento:
            eixo_x = st.session_state.col_agrupamento[-1]
            for col in st.session_state.col_agrupamento:
                if "distrito" in col.lower() or "deleg" in col.lower():
                    eixo_x = col
                    break
            
            # Descobrir quais as colunas de género disponíveis para o gráfico
            colunas_genero = []
            if 'F' in rel_viz.columns: colunas_genero.append('F')
            if 'M' in rel_viz.columns: colunas_genero.append('M')
            if 'Sem_Gênero' in rel_viz.columns: colunas_genero.append('Sem_Gênero')
            
            for col in rel_viz.columns:
                if col.startswith("Sexo_") and col not in colunas_genero:
                    colunas_genero.append(col)
                    
            if len(colunas_genero) > 0:
                st.write(f"**Distribuição de Beneficiários por: {eixo_x} (Desagregado por Sexo)**")
                # Garantir que os dados são numéricos para o gráfico não falhar/ficar vazio
                for c in colunas_genero:
                    rel_viz[c] = pd.to_numeric(rel_viz[c], errors='coerce').fillna(0)
                
                graf_distrito = rel_viz.groupby(eixo_x)[colunas_genero].sum()
                st.bar_chart(graf_distrito)
            else:
                st.write(f"**Análise de Beneficiários Únicos por: {eixo_x}**")
                rel_viz['Benef. Distintos'] = pd.to_numeric(rel_viz['Benef. Distintos'], errors='coerce').fillna(0)
                graf_distrito = rel_viz.groupby(eixo_x)[['Benef. Distintos']].sum()
                st.bar_chart(graf_distrito)


# =========================================================
# BOTÕES DE NAVEGAÇÃO DE PÁGINA (Fundo)
# =========================================================
st.write("") # Espaço extra
st.divider()
c1, c2, c3 = st.columns([1, 4, 1])

with c1:
    if st.session_state.pagina_atual != PAGINAS[0]:
        st.button("⬅️ Voltar", on_click=ir_anterior, use_container_width=True)

with c3:
    if st.session_state.pagina_atual != PAGINAS[-1]:
        # Lógica de bloqueio inteligente do botão
        pode_avancar = True
        if st.session_state.pagina_atual == PAGINAS[0] and st.session_state.df is None:
            pode_avancar = False
        elif st.session_state.pagina_atual == PAGINAS[1] and st.session_state.relatorio_final is None:
            pode_avancar = False
            
        st.button("Avançar ➡️", on_click=ir_proximo, use_container_width=True, type="primary", disabled=not pode_avancar)

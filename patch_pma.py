with open("app_dashboard.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update dropdown models
content = content.replace(
    'modelos_disponiveis = ["INAS"] # Outros modelos podem ser adicionados aqui no futuro',
    'modelos_disponiveis = ["INAS", "PMA"] # Outros modelos podem ser adicionados aqui no futuro'
)

# 2. Inject Pre-processing for PMA
# The code is right after df.columns = novas_colunas and before st.session_state.df = df
old_block = '''                    df.columns = novas_colunas
                    
                    st.session_state.df = df'''

new_block = '''                    df.columns = novas_colunas
                    
                    # --- PRÉ-PROCESSAMENTO PMA ---
                    if modelo_selecionado == "PMA":
                        # Mapeamento de colunas conhecidas no dump do PMA
                        pma_rename = {
                            'PI barcode': 'Beneficiario',
                            'Delegao ': 'Delegação',
                            'Valores_Pagos': 'Valor Pago',
                            'Datas_Pagamento': 'Data_Pagamento'
                        }
                        df.rename(columns=pma_rename, inplace=True)
                        
                        # Injetar Datas caso vazio, conforme regra do utilizador (01/01/2026)
                        if 'Data_Pagamento' not in df.columns:
                            df['Data_Pagamento'] = '01/01/2026'
                        else:
                            df['Data_Pagamento'] = df['Data_Pagamento'].fillna('01/01/2026').replace('NaT', '01/01/2026').replace('', '01/01/2026')
                            
                        # Extrair Ano e Mês (porque o processar_relatorio agrupa por essas dimensões)
                        # Assumimos que o formador é pelo menos reconhecível por pandas, ou injetamos fixo para '01/01/2026'
                        def extrair_ano(data):
                            try:
                                return pd.to_datetime(data, dayfirst=True).year
                            except:
                                return 2026
                                
                        def extrair_mes(data):
                            meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
                            try:
                                m = pd.to_datetime(data, dayfirst=True).month
                                return meses[m-1]
                            except:
                                return 'Janeiro'
                                
                        df['Ano '] = df['Data_Pagamento'].apply(extrair_ano)
                        df['Mês'] = df['Data_Pagamento'].apply(extrair_mes)
                        
                        # Forçar Implementador e Provedor
                        df['Implementador'] = 'PMA'
                        df['Provedor'] = 'Mpesa'
                    # -----------------------------
                    
                    st.session_state.df = df'''

content = content.replace(old_block, new_block)

# 3. Modify INAS post-processing block to include PMA logic too (output is the same)
old_post = '''                    if st.session_state.get('modelo_selecionado') == "INAS":
                        df_cumulativo["Fonte"] = "INAS"
                        df_mensal["Fonte"] = "INAS"
                        
                        if "Implementador" not in df_cumulativo.columns or df_cumulativo["Implementador"].astype(str).str.strip().eq("").all():
                            df_cumulativo["Implementador"] = ""'''

new_post = '''                    # O output do modelo PMA é 100% igual ao INAS
                    if st.session_state.get('modelo_selecionado') in ["INAS", "PMA"]:
                        # Para PMA a Fonte mantém-se INAS (como standardizado com o utilizador)
                        df_cumulativo["Fonte"] = "INAS"
                        df_mensal["Fonte"] = "INAS"
                        
                        # Se for PMA, forçar o implementador e provedor (apenas no caso do template não o ter feito)
                        if st.session_state.get('modelo_selecionado') == "PMA":
                            df_cumulativo["Implementador"] = "PMA"
                            df_mensal["Implementador"] = "PMA"
                            df_cumulativo["Provedor servico"] = "Mpesa"
                            df_mensal["Provedor servico"] = "Mpesa"
                        else:
                            if "Implementador" not in df_cumulativo.columns or df_cumulativo["Implementador"].astype(str).str.strip().eq("").all():
                                df_cumulativo["Implementador"] = ""'''

content = content.replace(old_post, new_post)

with open("app_dashboard.py", "w", encoding="utf-8") as f:
    f.write(content)

print("PMA logic patched!")

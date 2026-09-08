with open("app_dashboard.py", "r", encoding="utf-8") as f:
    content = f.read()

old_block = '''                    df.columns = novas_colunas
                    
                    # --- PRÉ-PROCESSAMENTO PMA ---'''

new_block = '''                    df.columns = novas_colunas
                    
                    # --- VALIDAÇÃO DE MODELO ---
                    colunas_upper = [str(c).upper().strip() for c in novas_colunas]
                    
                    if modelo_selecionado == "PMA":
                        if not any("PI BARCODE" in c for c in colunas_upper):
                            st.error("❌ ERRO DE VALIDAÇÃO: Selecionou o modelo 'PMA' mas o ficheiro não contém a estrutura esperada (falta a coluna 'PI barcode'). Verifique se selecionou o ficheiro e modelo corretos.")
                            st.session_state.last_file_name = None
                            st.stop()
                    elif modelo_selecionado == "INAS":
                        # Validar se o utilizador não carregou acidentalmente um ficheiro PMA no INAS
                        is_pma = any("PI BARCODE" in c for c in colunas_upper)
                        has_inas_structure = any("BENEFICIARIO" in c or "CÓDIGO" in c or "CODIGO" in c for c in colunas_upper)
                        
                        if is_pma and not has_inas_structure:
                            st.error("❌ ERRO DE VALIDAÇÃO: Selecionou o modelo 'INAS', mas o ficheiro carregado parece pertencer ao modelo 'PMA' (contém 'PI barcode'). Por favor, altere o seletor de Modelo para 'PMA' e tente novamente.")
                            st.session_state.last_file_name = None
                            st.stop()
                    # ----------------------------
                    
                    # --- PRÉ-PROCESSAMENTO PMA ---'''

content = content.replace(old_block, new_block)

with open("app_dashboard.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Validation logic patched!")

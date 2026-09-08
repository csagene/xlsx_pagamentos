# -*- coding: utf-8 -*-
with open("app_dashboard.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if "resumo_basico = df.groupby(col_agrupamento_reais).agg(" in line:
        new_lines.append(line)
        new_lines.append("        PAGAMENTOS=(col_beneficiario, 'count'),\n")
        new_lines.append("        VALOR_PAGO=(col_valor, 'sum'),\n")
        new_lines.append("        BENEF_DISTINTOS=(col_beneficiario, 'nunique')\n")
        new_lines.append("    )\n")
        
        # Inject dynamic aggregation for 1X..12X if they exist in original data
        new_lines.append("""
    # Adicionar agregações extras se existirem na tabela original (ex: 1X, 2X...)
    for metrica in col_metricas:
        if metrica not in ['PAGAMENTOS', 'VALOR_PAGO', 'BENEF_DISTINTOS', 'F', 'M']:
            for original_col in colunas_df:
                if normalize_text(original_col) == normalize_text(metrica):
                    df[original_col] = pd.to_numeric(df[original_col], errors='coerce').fillna(0)
                    temp_agg = df.groupby(col_agrupamento_reais)[original_col].sum().reset_index(name=metrica)
                    resumo_basico = pd.merge(resumo_basico.reset_index(), temp_agg, on=col_agrupamento_reais, how='left').set_index(col_agrupamento_reais)
                    break
""")
        skip = True
    elif skip and "    )" in line:
        skip = False
    elif not skip:
        new_lines.append(line)

with open("app_dashboard.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)
print("Success")

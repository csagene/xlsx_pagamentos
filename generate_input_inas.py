import pandas as pd
import numpy as np

# Column names
cols = [
    "ANO", "MES", "PROVINCIA", "DELEGACAO", "DISTRITO",
    "FONTE", "PROGRAMA", "IMPLEMENTADOR", "PROVEDOR_SERVICO",
    "CODIGO_BENEFICIARIO", "GENERO", "VALOR_PAGO"
]

data = []

# Base template for all rows
base = {
    "ANO": 2024,
    "PROVINCIA": "Nampula",
    "DELEGACAO": "Delegacao de Nampula",
    "DISTRITO": "Nacala Porto",
    "FONTE": "BM",
    "PROGRAMA": "PSSB",
    "IMPLEMENTADOR": "INAS",
    "PROVEDOR_SERVICO": "Vodacom"
}

# Beneficiary 1: Paid in 1 month
b1_meses = ["Janeiro"]
for m in b1_meses:
    row = base.copy()
    row.update({"MES": m, "CODIGO_BENEFICIARIO": "BENEF_001", "GENERO": "F", "VALOR_PAGO": 1080})
    data.append(row)

# Beneficiary 2: Paid in 2 months (e.g., received double payment in Abril)
b2_meses = ["Janeiro", "Abril"]
for m in b2_meses:
    row = base.copy()
    valor = 1080 if m == "Janeiro" else 2700
    row.update({"MES": m, "CODIGO_BENEFICIARIO": "BENEF_002", "GENERO": "M", "VALOR_PAGO": valor})
    data.append(row)

# Beneficiary 3: Paid in 3 months
b3_meses = ["Janeiro", "Fevereiro", "Março"]
for m in b3_meses:
    row = base.copy()
    row.update({"MES": m, "CODIGO_BENEFICIARIO": "BENEF_003", "GENERO": "F", "VALOR_PAGO": 1080})
    data.append(row)

# Beneficiary 4: Paid in 4 months
b4_meses = ["Janeiro", "Fevereiro", "Março", "Abril"]
for m in b4_meses:
    row = base.copy()
    row.update({"MES": m, "CODIGO_BENEFICIARIO": "BENEF_004", "GENERO": "M", "VALOR_PAGO": 1080})
    data.append(row)

# Add a different district to test grouping
base_cidade = base.copy()
base_cidade["DISTRITO"] = "Cidade de Nampula"

# Beneficiary 5 in Cidade de Nampula
b5_meses = ["Fevereiro", "Abril", "Maio"]
for m in b5_meses:
    row = base_cidade.copy()
    row.update({"MES": m, "CODIGO_BENEFICIARIO": "BENEF_005", "GENERO": "F", "VALOR_PAGO": 1620})
    data.append(row)

df = pd.DataFrame(data, columns=cols)
df.to_excel("input_INAS.xlsx", index=False)
print(f"Generated input_INAS.xlsx with {len(df)} rows.")

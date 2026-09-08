import pandas as pd
import numpy as np
import random

# Configuration
NUM_BENEFICIARIOS = 1000
NUM_MESES = 12
PROVINCIAS = ["Nampula", "Zambézia", "Cabo Delgado"]
DISTRITOS = {
    "Nampula": ["Nacala Porto", "Cidade de Nampula", "Mecuburi", "Ribaue"],
    "Zambézia": ["Quelimane", "Mocuba", "Gurue", "Alto Molocue"],
    "Cabo Delgado": ["Pemba", "Montepuez", "Mocimboa da Praia"]
}
DELEGACOES = ["Delegacao Norte", "Delegacao Centro", "Delegacao Sul"]
FONTES = ["BM", "INAS", "UNICEF"]
PROGRAMAS = ["PSSB", "PASP", "PASD"]
IMPLEMENTADORES = ["INAS", "ONG A", "ONG B"]
PROVEDORES = ["Vodacom", "Mpesa", "BCI", "BIM"]
GENEROS = ["F", "M"]
MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
VALORES = [540, 1080, 1620, 2160, 2700, 3240, 4860]

data = []

# Generate Base Beneficiaries
beneficiarios = []
for i in range(1, NUM_BENEFICIARIOS + 1):
    prov = random.choice(PROVINCIAS)
    dist = random.choice(DISTRITOS[prov])
    beneficiarios.append({
        "CODIGO_BENEFICIARIO": f"BENEF_{i:05d}",
        "PROVINCIA": prov,
        "DISTRITO": dist,
        "DELEGACAO": random.choice(DELEGACOES),
        "FONTE": random.choice(FONTES),
        "PROGRAMA": random.choice(PROGRAMAS),
        "IMPLEMENTADOR": random.choice(IMPLEMENTADORES),
        "PROVEDOR_SERVICO": random.choice(PROVEDORES),
        "GENERO": random.choice(GENEROS)
    })

# Generate Payments
# Each beneficiary will be paid in a random number of months (1 to 12)
for b in beneficiarios:
    num_pagamentos = random.randint(1, 12)
    meses_pagos = sorted(random.sample(range(12), num_pagamentos))
    
    for m_idx in meses_pagos:
        row = b.copy()
        row["ANO"] = 2024
        row["MES"] = MESES[m_idx]
        row["VALOR_PAGO"] = random.choice(VALORES)
        data.append(row)

# Create DataFrame
cols = [
    "ANO", "MES", "PROVINCIA", "DELEGACAO", "DISTRITO",
    "FONTE", "PROGRAMA", "IMPLEMENTADOR", "PROVEDOR_SERVICO",
    "CODIGO_BENEFICIARIO", "GENERO", "VALOR_PAGO"
]
df = pd.DataFrame(data, columns=cols)

# Shuffle the dataframe to make it realistic
df = df.sample(frac=1).reset_index(drop=True)

# Save to Excel
filename = "input_INAS_large.xlsx"
df.to_excel(filename, index=False)
print(f"Generated {filename} with {len(df)} rows.")

# -*- coding: utf-8 -*-
import pandas as pd

dados = [
    {
        "CODIGO_DO_BENEFICIARIO": "BEN-001",
        "ANO_PAGAMENTO": 2024,
        "MESES_PAGAMENTO": "1-Janeiro",
        "SEXO": "M",
        "PROVINCIA": "Maputo",
        "DELEGACAO": "Maputo Cidade",
        "DISTRITO": "KaMpfumo",
        "PROGRAMA_SOCIAL": "PASP",
        "IMPLEMENTADOR": "INAS",
        "PROVEDOR_SERVICO": "M-Pesa",
        "FONTE_FINANCIAMENTO": "Banco Mundial",
        "VALOR_PAGO": 1000.0
    },
    {
        "CODIGO_DO_BENEFICIARIO": "BEN-001",
        "ANO_PAGAMENTO": 2024,
        "MESES_PAGAMENTO": "2-Fevereiro",
        "SEXO": "M",
        "PROVINCIA": "Maputo",
        "DELEGACAO": "Maputo Cidade",
        "DISTRITO": "KaMpfumo",
        "PROGRAMA_SOCIAL": "PASP",
        "IMPLEMENTADOR": "INAS",
        "PROVEDOR_SERVICO": "M-Pesa",
        "FONTE_FINANCIAMENTO": "Banco Mundial",
        "VALOR_PAGO": 1000.0
    },
    {
        "CODIGO_DO_BENEFICIARIO": "BEN-002",
        "ANO_PAGAMENTO": 2024,
        "MESES_PAGAMENTO": "2-Fevereiro",
        "SEXO": "F",
        "PROVINCIA": "Maputo",
        "DELEGACAO": "Maputo Cidade",
        "DISTRITO": "KaMpfumo",
        "PROGRAMA_SOCIAL": "PASP",
        "IMPLEMENTADOR": "INAS",
        "PROVEDOR_SERVICO": "M-Pesa",
        "FONTE_FINANCIAMENTO": "Banco Mundial",
        "VALOR_PAGO": 1500.0
    },
    {
        "CODIGO_DO_BENEFICIARIO": "BEN-002",
        "ANO_PAGAMENTO": 2024,
        "MESES_PAGAMENTO": "3-Março",
        "SEXO": "F",
        "PROVINCIA": "Maputo",
        "DELEGACAO": "Maputo Cidade",
        "DISTRITO": "KaMpfumo",
        "PROGRAMA_SOCIAL": "PASP",
        "IMPLEMENTADOR": "INAS",
        "PROVEDOR_SERVICO": "M-Pesa",
        "FONTE_FINANCIAMENTO": "Banco Mundial",
        "VALOR_PAGO": 1500.0
    }
]

df = pd.DataFrame(dados)
df.to_excel("dados_teste_cumulativo.xlsx", index=False)
print("Ficheiro de teste gerado com sucesso!")

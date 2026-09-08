import pandas as pd

# Mock data
df = pd.DataFrame({
    'Beneficiario': ['A', 'B', 'C', 'A', 'B', 'A'],
    'Mês': ['Jan', 'Jan', 'Jan', 'Feb', 'Feb', 'Mar'],
    'mes_ordem': [1, 1, 1, 2, 2, 3]
})

df = df.sort_values(by=['Beneficiario', 'mes_ordem'])
df['vezes'] = df.groupby('Beneficiario').cumcount() + 1
df['freq_label'] = df['vezes'].astype(str) + "X"

print("Raw Data with Frequencies:")
print(df)

col_agrupamento = ['Mês']
freq_pivot = pd.pivot_table(
    df, 
    index=col_agrupamento, 
    columns='freq_label', 
    values='Beneficiario', 
    aggfunc='nunique', 
    fill_value=0
).reset_index()

print("\nPivot Table:")
print(freq_pivot)

print("\nTotals:")
print("1X Total:", freq_pivot['1X'].sum())
print("2X Total:", freq_pivot['2X'].sum())
print("3X Total:", freq_pivot['3X'].sum())

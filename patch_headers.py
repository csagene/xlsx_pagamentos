# -*- coding: utf-8 -*-
import os

with open("app_dashboard.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. CSS
content = content.replace(".block-container { padding-bottom: 100px !important; }", ".block-container { padding-bottom: 100px !important; padding-top: 1rem !important; }")

# 2. Make the expander stick higher up
content = content.replace("top: 2.875rem; /* streamlits default header height */", "top: 0.5rem; /* adjusted for smaller padding */")

# 3. Replace all st.header with st.markdown('### ...')
content = content.replace("st.header(\"📑 Relatórios de Pagamentos\")", "st.markdown(\"### 📑 Relatórios de Pagamentos\")")
content = content.replace("st.header(\"📈 3. Dashboard Visual\")", "st.markdown(\"### 📈 3. Dashboard Visual\")")
content = content.replace("st.header(\"📥 Carregar Novo Ficheiro Excel\")", "st.markdown(\"### 📥 Carregar Novo Ficheiro Excel\")")
content = content.replace("st.header(\"📝 Editar Colunas\")", "st.markdown(\"### 📝 Editar Colunas\")")
content = content.replace("st.title(", "st.markdown(\"### \" + ")

with open("app_dashboard.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Success")

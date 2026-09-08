# -*- coding: utf-8 -*-
with open("app_dashboard.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace metrics
content = content.replace("'Valor Pago'", "'VALOR_PAGO'")
content = content.replace("'Benef. Distintos'", "'BENEF_DISTINTOS'")
content = content.replace("'Pagamentos'", "'PAGAMENTOS'")

# Replace frequency columns list
old_freq = "['1x', '2x', '3x', '4+']"
new_freq = "['1X', '2X', '3X', '4X', '5X', '6X', '7X', '8X', '9X', '10X', '11X', '12X']"
content = content.replace(old_freq, new_freq)

with open("app_dashboard.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Success")

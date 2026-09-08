# -*- coding: utf-8 -*-
with open("app_dashboard.py", "r", encoding="utf-8") as f:
    content = f.read()

old_css = """    div[data-testid="stExpander"]:has(#filters-sticky-hook) {
        position: sticky;
        top: 0.5rem; /* adjusted for smaller padding */
        z-index: 990;
        background-color: #ffffff;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        border-radius: 0.5rem;
    }"""

new_css = """    div[data-testid="stExpander"]:has(#filters-sticky-hook) {
        position: sticky;
        top: 0.5rem; /* adjusted for smaller padding */
        z-index: 99999;
        background-color: #ffffff;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        border-radius: 0.5rem;
        overflow: visible !important;
    }
    div[data-testid="stExpander"]:has(#filters-sticky-hook) > div {
        overflow: visible !important;
    }
    div[data-testid="stExpanderDetails"] {
        overflow: visible !important;
    }"""

if old_css in content:
    content = content.replace(old_css, new_css)
else:
    print("Old CSS not found, trying with z-index 990 replacement")

with open("app_dashboard.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Success")

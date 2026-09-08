with open("app_dashboard.py", "r", encoding="utf-8") as f:
    content = f.read()

# Update heights for the charts
content = content.replace(
    'fig_area.update_layout(margin=dict(l=0, r=0, t=30, b=0), xaxis_title=None)',
    'fig_area.update_layout(margin=dict(l=0, r=0, t=30, b=0), xaxis_title=None, height=280)'
)

content = content.replace(
    'fig_pie.update_layout(margin=dict(l=0, r=0, t=30, b=0))',
    'fig_pie.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=250)'
)

content = content.replace(
    "fig_bar.update_layout(margin=dict(l=0, r=0, t=30, b=0), yaxis={'categoryorder':'total ascending'}, xaxis_title=None, yaxis_title=None)",
    "fig_bar.update_layout(margin=dict(l=0, r=0, t=30, b=0), yaxis={'categoryorder':'total ascending'}, xaxis_title=None, yaxis_title=None, height=250)"
)

content = content.replace(
    "fig_tree.update_layout(margin=dict(l=0, r=0, t=30, b=0))",
    "fig_tree.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=300)"
)

with open("app_dashboard.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Dashboard layout updated successfully!")

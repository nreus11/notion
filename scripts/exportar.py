import os
import requests
import plotly.express as px
import pandas as pd

# Variables de entorno
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# Obtener datos de Notion
url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
response = requests.post(url, headers=headers)
response.raise_for_status()
data = response.json()

# Parsear resultados
rows = []
for result in data["results"]:
    props = result["properties"]
    nombre = props["Nombre"]["title"][0]["plain_text"] if props["Nombre"]["title"] else ""
    cantidad = props["Cantidad"]["number"] or 0
    fecha = props["Fecha del gasto"]["date"]["start"] if props["Fecha del gasto"]["date"] else None
    cuenta = props["Cuenta"]["rich_text"][0]["plain_text"] if props["Cuenta"]["rich_text"] else ""
    categoria = props["Categoría"]["rich_text"][0]["plain_text"] if props["Categoría"]["rich_text"] else ""
    formula = props["Fórmula"]["formula"]["string"] if props["Fórmula"]["formula"]["string"] else ""
    
    rows.append({
        "Nombre": nombre,
        "Cantidad": cantidad,
        "Fecha": fecha,
        "Cuenta": cuenta,
        "Categoría": categoria,
        "Fórmula": formula
    })

df = pd.DataFrame(rows)

# Crear gráfico con Plotly
fig = px.bar(df, x="Categoría", y="Cantidad", color="Categoría",
             title="Gastos por Categoría", text_auto=True)

# Guardar HTML con gráfico
html_content = fig.to_html(full_html=True)

# Crear carpeta y guardar index.html
os.makedirs("site", exist_ok=True)
with open("site/index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("✅ Página generada con gráfico en site/index.html")

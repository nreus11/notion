import os
import requests
import pandas as pd
import plotly.express as px

# Variables de entorno (Notion API)
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")

# URL de la API de Notion
url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# Consultar Notion
response = requests.post(url, headers=headers)
data = response.json()

# Extraer datos (asumiendo que tienes propiedades "Nombre" y "Valor")
rows = []
for result in data["results"]:
    props = result["properties"]
    
    nombre = ""
    if props.get("Nombre") and props["Nombre"]["type"] == "title":
        if props["Nombre"]["title"]:
            nombre = props["Nombre"]["title"][0]["plain_text"]

    cantidad = None
    if props.get("Cantidad") and props["Cantidad"]["type"] == "number":
        cantidad = props["Cantidad"]["number"]

    fecha_gasto = ""
    if props.get("Fecha del gasto") and props["Fecha del gasto"]["type"] == "date":
        if props["Fecha del gasto"]["date"]:
            fecha_gasto = props["Fecha del gasto"]["date"]["start"]

    cuenta = ""
    if props.get("Cuenta") and props["Cuenta"]["type"] == "rich_text":
        if props["Cuenta"]["rich_text"]:
            cuenta = props["Cuenta"]["rich_text"][0]["plain_text"]

    categoria = ""
    if props.get("Categoría") and props["Categoría"]["type"] == "rich_text":
        if props["Categoría"]["rich_text"]:
            categoria = props["Categoría"]["rich_text"][0]["plain_text"]

    formula = ""
    if props.get("Fórmula") and props["Fórmula"]["type"] == "rich_text":
        if props["Fórmula"]["rich_text"]:
            formula = props["Fórmula"]["rich_text"][0]["plain_text"]

    rows.append({
        "Nombre": nombre,
        "Cantidad": cantidad,
        "Fecha del gasto": fecha_gasto,
        "Cuenta": cuenta,
        "Categoría": categoria,
        "Fórmula": formula
    })


df = pd.DataFrame(rows)

# Crear gráfico interactivo
df['Fecha del gasto'] = pd.to_datetime(df['Fecha del gasto'])  # Convertir a fecha real

fig = px.bar(df, 
             x='Fecha del gasto', 
             y='Cantidad', 
             color='Categoría', 
             title='Gastos por fecha y categoría')

fig.write_html("site/index.html", include_plotlyjs="cdn")

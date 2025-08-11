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
    nombre = props["Nombre"]["title"][0]["plain_text"] if props["Nombre"]["title"] else ""
    valor = props["Valor"]["number"]
    rows.append({"Nombre": nombre, "Valor": valor})

df = pd.DataFrame(rows)

# Crear gráfico interactivo
fig = px.bar(df, x="Nombre", y="Valor", title="Gráfico desde Notion")
fig.write_html("index.html", auto_open=False)

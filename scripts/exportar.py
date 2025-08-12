import os
import requests
import pandas as pd
import plotly.express as px

# ---------------------------
# 1. VARIABLES DE ENTORNO
# ---------------------------
# Debes configurarlas en GitHub como "Secrets"
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

# ---------------------------
# 2. CREAR CARPETA PARA PUBLICAR
# ---------------------------
os.makedirs("site", exist_ok=True)

# ---------------------------
# 3. FUNCIÓN PARA EXTRAER DATOS
# ---------------------------
def obtener_datos_notion():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers)
    response.raise_for_status()
    return response.json()

# ---------------------------
# 4. PROCESAR DATOS
# ---------------------------
def procesar_datos(data):
    rows = []
    for result in data["results"]:
        props = result["properties"]

        nombre = ""
        if props.get("Nombre") and props["Nombre"]["title"]:
            nombre = props["Nombre"]["title"][0]["plain_text"]

        cantidad = props.get("Cantidad", {}).get("number")

        fecha_gasto = ""
        if props.get("Fecha del gasto", {}).get("date"):
            fecha_gasto = props["Fecha del gasto"]["date"]["start"]

        cuenta = ""
        if props.get("Cuenta", {}).get("rich_text"):
            cuenta = props["Cuenta"]["rich_text"][0]["plain_text"]

        categoria = ""
        if props.get("Categoría", {}).get("rich_text"):
            categoria = props["Categoría"]["rich_text"][0]["plain_text"]

        formula = ""
        if props.get("Fórmula", {}).get("rich_text"):
            formula = props["Fórmula"]["rich_text"][0]["plain_text"]

        rows.append({
            "Nombre": nombre,
            "Cantidad": cantidad,
            "Fecha del gasto": fecha_gasto,
            "Cuenta": cuenta,
            "Categoría": categoria,
            "Fórmula": formula
        })

    return pd.DataFrame(rows)

# ---------------------------
# 5. CREAR GRÁFICO
# ---------------------------
def crear_grafico(df):
    df["Fecha del gasto"] = pd.to_datetime(df["Fecha del gasto"], errors="coerce")
    fig = px.bar(
        df,
        x="Fecha del gasto",
        y="Cantidad",
        color="Categoría",
        hover_data=["Nombre", "Cuenta", "Fórmula"],
        title="Gastos por fecha y categoría"
    )
    fig.write_html("site/index.html", include_plotlyjs="cdn")

# ---------------------------
# 6. EJECUCIÓN PRINCIPAL
# ---------------------------
if __name__ == "__main__":
    print("📡 Obteniendo datos desde Notion...")
    data = obtener_datos_notion()

    print("📊 Procesando datos...")
    df = procesar_datos(data)

    print("📈 Creando gráfico...")
    crear_grafico(df)

    print("✅ Listo. Archivo guardado en site/index.html")

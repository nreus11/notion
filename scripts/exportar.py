import os
import requests
import pandas as pd
import plotly.express as px
import hashlib  # Para verificar cambios

# ---------------------------
# 1. VARIABLES DE ENTORNO
# ---------------------------
# Mantengo exactamente como tenías
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
DATABASE_ID = os.environ.get("DATABASE_ID")

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
            
        cantidad = props.get("Cantidad").get("number")
        
        fecha_gasto = ""
        if props.get("Fecha del gasto").get("created_time"):
            fecha_gasto = props["Fecha del gasto"]["created_time"]

        cuenta = ""
        if props.get("Cuenta") and props["Cuenta"]["select"]:
            cuenta = props["Cuenta"]["select"]["name"]

        categoria = ""
        if props.get("Categoría") and props["Categoría"]["select"]:
            categoria = props["Categoría"]["select"]["name"]

        formula = ""
        if props.get("Fórmula") and props["Fórmula"]["formula"]:
            formula = props["Fórmula"]["formula"]["string"]

        rows.append({
            "Nombre": nombre,
            "Cantidad": cantidad,
            "Fecha_del_gasto": fecha_gasto,
            "Cuenta": cuenta,
            "Categoría": categoria,
            "Tipo_gasto": formula
        })

    return pd.DataFrame(rows)

# ---------------------------
# 5. HASH PARA DETECTAR CAMBIOS
# ---------------------------
def datos_cambiaron(df):
    data_string = df.to_json()
    data_hash = hashlib.md5(data_string.encode()).hexdigest()

    hash_file = "site/data_hash.txt"
    prev_hash = ""
    if os.path.exists(hash_file):
        with open(hash_file, "r") as f:
            prev_hash = f.read().strip()

    if data_hash == prev_hash:
        return False  # No hay cambios
    else:
        with open(hash_file, "w") as f:
            f.write(data_hash)
        return True

# ---------------------------
# 6. CREAR GRÁFICOS
# ---------------------------
def crear_dashboard(df):
    df["Fecha_del_gasto"] = pd.to_datetime(df["Fecha_del_gasto"], errors="coerce")

    # 1. Gastos por fecha y categoría
    fig1 = px.bar(
        df,
        x="Fecha_del_gasto",
        y="Cantidad",
        color="Categoría",
        hover_data=["Nombre", "Cuenta", "Tipo_gasto"],
        title="Gastos por fecha y categoría"
    )
    fig1.write_html("site/gastos_por_fecha.html", include_plotlyjs="cdn")

    # 2. Gastos por cuenta (pie chart)
    fig2 = px.pie(
        df,
        names="Cuenta",
        values="Cantidad",
        title="Distribución de gastos por cuenta"
    )
    fig2.write_html("site/gastos_por_cuenta.html", include_plotlyjs="cdn")

    # 3. Gastos por categoría (pie chart)
    fig3 = px.pie(
        df,
        names="Categoría",
        values="Cantidad",
        title="Distribución de gastos por categoría"
    )
    fig3.write_html("site/gastos_por_categoria.html", include_plotlyjs="cdn")

# ---------------------------
# 7. EJECUCIÓN PRINCIPAL
# ---------------------------
if __name__ == "__main__":
    print("📡 Obteniendo datos desde Notion...")
    data = obtener_datos_notion()

    print("📊 Procesando datos...")
    df = procesar_datos(data)

    if not datos_cambiaron(df):
        print("🔹 No hay cambios en los datos. No se actualiza dashboard.")
    else:
        print("📈 Creando dashboard...")
        crear_dashboard(df)
        print("✅ Dashboard actualizado en site/index.html")

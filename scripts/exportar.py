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
            fecha_gasto = pd.to_datetime(fecha_gasto, errors="coerce")

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
            "Fecha del gasto": fecha_gasto,
            "Cuenta": cuenta,
            "Categoría": categoria,
            "Tipo gasto": formula
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
def info_mes(df):
    def aplicar_estilo(fig, tipo='bar'):
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            title_font_size=20,
            font=dict(family="Arial", size=12, color="white")
        )
    
        if tipo == 'bar':
            fig.update_yaxes(tickprefix="$", tickformat=",")
            fig.update_traces(texttemplate='%{y}', textposition='outside')
            fig.update_layout(bargap=0.2)
        elif tipo == 'pie':
            fig.update_traces(textinfo='percent+label')
        return fig
    
    df["Fecha del gasto"] = df["Fecha del gasto"].dt.tz_convert(None)
    ultimo_mes = df["Fecha del gasto"].dt.to_period("M").max()
    ultimo_mes_nombre = ultimo_mes.strftime("%B %Y").capitalize()
    # Filtrar solo los datos de ese mes
    df_ultimo_mes = df[df["Fecha del gasto"].dt.to_period("M") == ultimo_mes]
    df_ultimo_mes["Mes"] = df_ultimo_mes["Fecha del gasto"].dt.to_period("M").astype(str)

    #agrupados
    df_agrupado_cat = df_ultimo_mes.groupby(["Mes", "Categoría"], as_index=False)["Cantidad"].sum()
    df_agrupado_cat = df_agrupado_cat.sort_values(by="Cantidad", ascending=False)
    df_agrupado_tipo = df_ultimo_mes.groupby(["Mes", "Tipo gasto"], as_index=False)["Cantidad"].sum()
    df_agrupado_cuenta = df_ultimo_mes.groupby(["Mes", "Cuenta"], as_index=False)["Cantidad"].sum()

    # 1. Gastos por fecha y categoría
    fig1 = px.bar(
        df_agrupado_cat,
        x="Categoría",
        y="Cantidad",
        color="Categoría",
        title=f"Gastos del mes {ultimo_mes_nombre} agrupados por categoría"
    )
    fig1 = aplicar_estilo(fig1, tipo="bar")
    fig1.write_html("site/gastos_mes.html", include_plotlyjs="cdn")

    # 2. Gastos por tipo (pie chart)
    fig2 = px.pie(
        df_agrupado_tipo,
        names="Tipo gasto",
        values="Cantidad",
        title="Distribución de gastos por tipo"
    )
    fig2 = aplicar_estilo(fig2, tipo="pie")
    fig2.write_html("site/gastos_por_tipo_mes.html", include_plotlyjs="cdn")

    # 3. Gastos por cuenta (pie chart)
    fig3 = px.pie(
        df_agrupado_cuenta,
        names="Cuenta",
        values="Cantidad",
        title="Distribución de gastos por cuenta"
    )
    fig3 = aplicar_estilo(fig3, tipo="pie")
    fig3.write_html("site/gastos_por_cuenta_mes.html", include_plotlyjs="cdn")

     # Gráfico de línea
    fig_line = px.line(
        df,
        x="Fecha del gasto",
        y="Cantidad",
        color="Categoría",
        markers=True,
        title="Evolución de gastos"
    )
    fig_line.write_html("site/index.html", include_plotlyjs="cdn")

    # - Gráfico comparativo mes anterior
    # Crear columna de periodo (año-mes)
    df["Mes"] = df["Fecha_del_gasto"].dt.to_period("M")

    # Determinar mes actual y mes anterior
    ultimo_mes = df["Mes"].max()
    mes_anterior = ultimo_mes - 1

    # Filtrar solo esos 2 meses
    df_filtrado = df[df["Mes"].isin([ultimo_mes, mes_anterior])]

    # Agrupar por categoría y mes
    df_agg = df_filtrado.groupby(["Categoría", "Mes"], as_index=False)["Cantidad"].sum()

    # Convertir Mes a string legible (ej: "Agosto 2025")
    df_agg["Mes"] = df_agg["Mes"].dt.strftime("%B %Y")
    fig4 = px.bar(
    df_agg,
    x="Categoría",
    y="Cantidad",
    color="Mes",  # diferencia las barras por mes
    barmode="group",  # barras una al lado de la otra
    title="Comparación de gastos por categoría - Mes actual vs Mes anterior"
    )
    fig4 = aplicar_estilo(fig4, tipo="bar")
    fig4.write_html("site/cat_mes_anterior.html", include_plotlyjs="cdn")





def crear_dashboard(df):

    # 1. Gastos por fecha y categoría
    fig1 = px.bar(
        df,
        x="Fecha del gasto",
        y="Cantidad",
        color="Categoría",
        hover_data=["Nombre", "Cuenta", "Tipo gasto"],
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

     # Gráfico de línea
    fig_line = px.line(
        df,
        x="Fecha del gasto",
        y="Cantidad",
        color="Categoría",
        markers=True,
        title="Evolución de gastos"
    )

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
        info_mes(df)
        print("✅ Dashboard actualizado en site/index.html")

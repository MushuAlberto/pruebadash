import streamlit as st
import pandas as pd
import plotly.express as px
import unicodedata

def limpiar_columna(col):
    col = ''.join((c for c in unicodedata.normalize('NFD', col) if unicodedata.category(c) != 'Mn'))
    return col.strip().upper().replace(" ", "")

def buscar_columna(df, posibles):
    cols_limpias = {limpiar_columna(col): col for col in df.columns}
    for posible in posibles:
        posible_limpio = limpiar_columna(posible)
        if posible_limpio in cols_limpias:
            return cols_limpias[posible_limpio]
    return None

def normalizar_nombres_empresas(df, empresa_col):
    agrupaciones = {
        'M&Q SPA': ['M&Q SPA', 'M & Q', 'M & Q SPA', 'MINING AND QUARRYING SPA'],
        'M S & D SPA': ['M S & D SPA', 'M S & D', 'MINING SERVICES AND DERIVATES SPA', 
                        'MINING SERVICES AND DERIVATES', 'MS&D SPA'],
        'JORQUERA TRANSPORTE S. A.': ['JORQUERA TRANSPORTE S. A.', 'JORQUERA TRANSPORTE S A'],
        'COSEDUCAM S A': ['COSEDUCAM S A', 'COSEDUCAM'],
        'AG SERVICES SPA': ['AG SERVICES SPA'],
        'ARTISA': ['ARTISA']
    }
    mapeo_normalizacion = {}
    for nombre_principal, variantes in agrupaciones.items():
        for variante in variantes:
            mapeo_normalizacion[limpiar_columna(variante)] = nombre_principal
    def normalizar_nombre(nombre):
        if pd.isna(nombre):
            return nombre
        nombre_limpio = limpiar_columna(str(nombre))
        if nombre_limpio in mapeo_normalizacion:
            return mapeo_normalizacion[nombre_limpio]
        for nombre_normalizado, variantes in agrupaciones.items():
            for variante in variantes:
                if limpiar_columna(variante) in nombre_limpio or nombre_limpio in limpiar_columna(variante):
                    return nombre_normalizado
        return nombre
    df[empresa_col + '_normalizada'] = df[empresa_col].apply(normalizar_nombre)
    return df

st.set_page_config(page_title="Dashboard por Fecha y Empresa", layout="wide")
st.markdown(
    """
    <style>
    .banner-container {
        width: 100vw;
        margin-left: -8vw;
        margin-top: -3.5vw;
    }
    @media (max-width: 900px) {
        .banner-container { margin-left: -4vw; }
    }
    </style>
    <div class='banner-container'>
        <img src='assets/banner.png' style='width: 100%; height: auto; display: block;'>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("Carga tu archivo Excel, selecciona la fecha y automáticamente verás los gráficos de PRODUCTO vs TONELAJE por EMPRESA DE TRANSPORTE, con cada DESTINO identificado por color.")

st.sidebar.header("📁 Cargar Datos")
uploaded_file = st.sidebar.file_uploader(
    "Selecciona tu archivo Excel",
    type=['xlsx', 'xls'],
    help="Formatos soportados: .xlsx, .xls"
)

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, dtype=str)
        df.columns = [col.strip() for col in df.columns]
        st.write("Nombres de columna detectados:", df.columns.tolist())
        st.write("Vista previa de los datos:")
        st.dataframe(df.head(10), use_container_width=True)

        # Buscar columnas por palabras clave
        col_fecha = buscar_columna(df, ["FECHA"])
        col_producto = buscar_columna(df, ["PRODUCTO"])
        col_tonelaje = buscar_columna(df, ["TONELAJE"])
        col_empresa = buscar_columna(df, ["EMPRESA DE TRANSPORTE", "EMPRESA"])
        col_destino = buscar_columna(df, ["DESTINO"])
        col_tiempo = buscar_columna(df, ["TIEMPO OPERACIONAL"])

        # Validar columnas requeridas
        if not col_fecha or not col_producto or not col_tonelaje or not col_empresa or not col_destino:
            st.error(f"No se encontraron las columnas requeridas. Fecha: {col_fecha}, Producto: {col_producto}, Tonelaje: {col_tonelaje}, Empresa: {col_empresa}, Destino: {col_destino}")
            st.stop()

        # Convertir FECHA a datetime
        df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce')
        # Convertir TONELAJE a numérico
        df[col_tonelaje] = pd.to_numeric(df[col_tonelaje], errors='coerce')

        # Normalizar nombres de empresa
        df = normalizar_nombres_empresas(df, col_empresa)
        empresa_col_normalizada = col_empresa + '_normalizada'

        # Selección de fecha
        st.markdown("---")
        st.header("📅 Selecciona una fecha para filtrar los datos")
        min_date = df[col_fecha].min().date()
        max_date = df[col_fecha].max().date()
        selected_date = st.date_input(
            "Selecciona la fecha",
            min_value=min_date,
            max_value=max_date,
            value=min_date,
            key="main_date_input"
        )
        filtered_df = df[df[col_fecha].dt.date == selected_date]
        if filtered_df.empty:
            st.warning("No hay datos para la fecha seleccionada. Por favor, elige otra fecha.")
            st.stop()

        # Indicador de Tiempo Operacional (si existe)
        if col_tiempo and col_tiempo in filtered_df.columns:
            tiempo_operacional = pd.to_numeric(filtered_df[col_tiempo], errors='coerce').mean()
            horas = int(tiempo_operacional) // 60 if pd.notnull(tiempo_operacional) else 0
            minutos = int(tiempo_operacional) % 60 if pd.notnull(tiempo_operacional) else 0
            tiempo_str = f"{horas}:{minutos:02d}" if pd.notnull(tiempo_operacional) else "N/A"
        else:
            tiempo_str = "N/A"
        st.markdown(
            f"""
            <div style='background-color:#e6f4ea; border:1px solid #4caf50; border-radius:5px; padding:10px; text-align:center; width:300px; margin:auto;'>
                <b>Tiempo Operacional</b><br>
                <span style='color:red; font-size:1.5em;'><b>{tiempo_str}</b></span>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("---")

        # Gráficos automáticos por empresa, coloreando por DESTINO
        st.markdown("## Gráficos PRODUCTO vs TONELAJE por EMPRESA DE TRANSPORTE (coloreado por DESTINO)")
        empresas = filtered_df[empresa_col_normalizada].dropna().unique().tolist()
        if not empresas:
            st.info("No hay empresas para la fecha seleccionada.")
        else:
            for empresa in empresas:
                df_empresa = filtered_df[filtered_df[empresa_col_normalizada] == empresa]
                if not df_empresa.empty:
                    st.markdown(f"### {empresa}")
                    fig = px.bar(
                        df_empresa,
                        x=col_producto,
                        y=col_tonelaje,
                        color=col_destino,
                        title=f"{empresa}: PRODUCTO vs TONELAJE (coloreado por DESTINO)",
                        labels={col_producto: "Producto", col_tonelaje: "Tonelaje", col_destino: "Destino"}
                    )
                    st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
        st.info("Asegúrate de que el archivo sea un Excel válido (.xlsx o .xls) y que las columnas tengan los nombres correctos.")

else:
    st.info("👆 Carga un archivo Excel desde la barra lateral para comenzar")
    st.markdown("### 📋 Formato de datos esperado")
    example_data = {
        'FECHA': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'PRODUCTO': ['A', 'B', 'A'],
        'DESTINO': ['X', 'Y', 'Z'],
        'TONELAJE': [100, 150, 120],
        'EMPRESA DE TRANSPORTE': ['M&Q SPA', 'M & Q', 'JORQUERA TRANSPORTE S. A.'],
        'TIEMPO OPERACIONAL': [138, 120, 90]
    }
    st.dataframe(pd.DataFrame(example_data))
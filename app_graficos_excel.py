import streamlit as st
import pandas as pd
import plotly.express as px

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
            mapeo_normalizacion[variante.upper().strip()] = nombre_principal
    def normalizar_nombre(nombre):
        if pd.isna(nombre):
            return nombre
        nombre_limpio = str(nombre).upper().strip()
        if nombre_limpio in mapeo_normalizacion:
            return mapeo_normalizacion[nombre_limpio]
        for nombre_normalizado, variantes in agrupaciones.items():
            for variante in variantes:
                if variante.upper() in nombre_limpio or nombre_limpio in variante.upper():
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
st.markdown("Carga tu archivo Excel, selecciona la fecha y automáticamente verás los gráficos de PRODUCTO vs TONELAJE por EMPRESA.")

st.sidebar.header("📁 Cargar Datos")
uploaded_file = st.sidebar.file_uploader(
    "Selecciona tu archivo Excel",
    type=['xlsx', 'xls'],
    help="Formatos soportados: .xlsx, .xls"
)

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, dtype=str)
        # Asegurarse de que los nombres de columna estén limpios
        df.columns = [col.strip().upper() for col in df.columns]

        # Convertir FECHA a datetime
        if 'FECHA' in df.columns:
            df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce')
        else:
            st.error("No se encontró la columna 'FECHA' en el archivo.")
            st.stop()

        # Convertir TONELAJE a numérico
        if 'TONELAJE' in df.columns:
            df['TONELAJE'] = pd.to_numeric(df['TONELAJE'], errors='coerce')
        else:
            st.error("No se encontró la columna 'TONELAJE' en el archivo.")
            st.stop()

        # Normalizar nombres de empresa
        if 'EMPRESA' in df.columns:
            df = normalizar_nombres_empresas(df, 'EMPRESA')
            empresa_col_normalizada = 'EMPRESA_normalizada'
        else:
            st.error("No se encontró la columna 'EMPRESA' en el archivo.")
            st.stop()

        st.write("Vista previa de los datos:")
        st.dataframe(df.head(10), use_container_width=True)

        # Selección de fecha
        st.markdown("---")
        st.header("📅 Selecciona una fecha para filtrar los datos")
        min_date = df['FECHA'].min().date()
        max_date = df['FECHA'].max().date()
        selected_date = st.date_input(
            "Selecciona la fecha",
            min_value=min_date,
            max_value=max_date,
            value=min_date,
            key="main_date_input"
        )
        filtered_df = df[df['FECHA'].dt.date == selected_date]
        if filtered_df.empty:
            st.warning("No hay datos para la fecha seleccionada. Por favor, elige otra fecha.")
            st.stop()

        # Indicador de Tiempo Operacional (si existe)
        if 'TIEMPO OPERACIONAL' in filtered_df.columns:
            tiempo_operacional = pd.to_numeric(filtered_df['TIEMPO OPERACIONAL'], errors='coerce').mean()
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

        # Gráficos automáticos por empresa
        st.markdown("## Gráficos PRODUCTO vs TONELAJE por EMPRESA")
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
                        x='PRODUCTO',
                        y='TONELAJE',
                        title=f"{empresa}: PRODUCTO vs TONELAJE",
                        labels={'PRODUCTO': "Producto", 'TONELAJE': "Tonelaje"}
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
        'EMPRESA': ['M&Q SPA', 'M & Q', 'JORQUERA TRANSPORTE S. A.'],
        'TIEMPO OPERACIONAL': [138, 120, 90]
    }
    st.dataframe(pd.DataFrame(example_data))
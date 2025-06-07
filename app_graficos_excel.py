import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

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

def detectar_columna_fecha(df):
    date_cols = df.select_dtypes(include=['datetime', 'datetime64[ns]', 'datetime64[ns, UTC]']).columns.tolist()
    if not date_cols:
        for col in df.columns:
            if any(word in col.lower() for word in ['fecha', 'date', 'día', 'dia']):
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    if df[col].notnull().sum() > 0:
                        date_cols.append(col)
                except Exception:
                    pass
    return date_cols

def detectar_columna_empresa(df):
    for col in df.columns:
        if any(word in col.lower() for word in ['empresa', 'compañía', 'compania', 'company', 'sociedad']):
            return col
    return None

def main():
    st.set_page_config(page_title="Dashboard por Fecha y Empresa", layout="wide")
    # Banner imagen a todo el ancho (sin títulos debajo)
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

    st.markdown("Carga tu archivo Excel, selecciona la fecha y automáticamente verás los gráficos de Producto vs Tonelaje por empresa.")

    st.sidebar.header("📁 Cargar Datos")
    uploaded_file = st.sidebar.file_uploader(
        "Selecciona tu archivo Excel",
        type=['xlsx', 'xls'],
        help="Formatos soportados: .xlsx, .xls"
    )

    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            st.write("Vista previa de los datos:")
            st.dataframe(df.head(10), use_container_width=True)

            # Detectar columna de fecha
            date_columns = detectar_columna_fecha(df)

            if date_columns:
                st.markdown("---")
                st.header("📅 Selecciona una fecha para filtrar los datos")
                date_col = st.selectbox("Columna de fecha", date_columns, key="main_date_col")
                df = df[df[date_col].notnull()]
                min_date = df[date_col].min().date()
                max_date = df[date_col].max().date()
                selected_date = st.date_input(
                    "Selecciona la fecha",
                    min_value=min_date,
                    max_value=max_date,
                    value=min_date,
                    key="main_date_input"
                )
                filtered_df = df[df[date_col].dt.date == selected_date]
                if filtered_df.empty:
                    st.warning("No hay datos para la fecha seleccionada. Por favor, elige otra fecha.")
                    return
            else:
                st.info("No se detectó ninguna columna de fecha. Se mostrarán todos los datos.")
                filtered_df = df.copy()

            # Detectar columna de empresa
            empresa_col = detectar_columna_empresa(filtered_df)
            if empresa_col:
                filtered_df = normalizar_nombres_empresas(filtered_df, empresa_col)
                empresa_col_normalizada = empresa_col + '_normalizada'
            else:
                st.info("No se detectó ninguna columna de empresa. No se pueden generar los gráficos por empresa.")
                return

            # Fecha seleccionada
            st.markdown(f"**Fecha :**  {selected_date.strftime('%A, %d de %B de %Y')}", unsafe_allow_html=True)

            # Indicador de Tiempo Operacional (columna E)
            col_tiempo = "Tiempo Operacional"  # Cambia esto si tu columna tiene otro nombre
            if col_tiempo in filtered_df.columns:
                tiempo_operacional = filtered_df[col_tiempo].mean()
                horas = int(tiempo_operacional) // 60
                minutos = int(tiempo_operacional) % 60
                tiempo_str = f"{horas}:{minutos:02d}"
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

            # --- GRAFICOS AUTOMATICOS POR EMPRESA: Producto vs Tonelaje ---
            col_tonelaje = "Tonelaje"  # Cambia esto si tu columna tiene otro nombre
            col_producto = "Producto"  # Cambia esto si tu columna tiene otro nombre

            if col_tonelaje in filtered_df.columns and col_producto in filtered_df.columns:
                st.markdown("## Gráficos Producto vs Tonelaje por Empresa")
                empresas = filtered_df[empresa_col_normalizada].dropna().unique().tolist()
                for empresa in empresas:
                    df_empresa = filtered_df[filtered_df[empresa_col_normalizada] == empresa]
                    if not df_empresa.empty:
                        st.markdown(f"### {empresa}")
                        fig = px.bar(
                            df_empresa,
                            x=col_producto,
                            y=col_tonelaje,
                            title=f"{empresa}: Producto vs Tonelaje",
                            labels={col_producto: "Producto", col_tonelaje: "Tonelaje"}
                        )
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No se encontraron las columnas 'Producto' y/o 'Tonelaje' en los datos.")

        except Exception as e:
            st.error(f"Error al procesar el archivo: {str(e)}")
            st.info("Asegúrate de que el archivo sea un Excel válido (.xlsx o .xls)")

    else:
        st.info("👆 Carga un archivo Excel desde la barra lateral para comenzar")
        st.markdown("### 📋 Formato de datos esperado")
        example_data = {
            'Fecha': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'Empresa': ['M&Q SPA', 'M & Q', 'JORQUERA TRANSPORTE S. A.'],
            'Tiempo Operacional': [138, 120, 90],  # minutos
            'Tonelaje': [100, 150, 120],
            'Producto': ['A', 'B', 'A'],
            'Region': ['Norte', 'Sur', 'Norte']
        }
        st.dataframe(pd.DataFrame(example_data))

if __name__ == "__main__":
    main()
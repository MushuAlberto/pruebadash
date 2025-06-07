
import streamlit as st
import pandas as pd
import plotly.express as px
import re

def normalizar_nombres_empresas(df, empresa_col):
    """
    Normaliza y agrupa nombres de empresas similares
    """
    # Diccionario de agrupaciones específicas
    agrupaciones = {
        'M&Q SPA': ['M&Q SPA', 'M & Q', 'M & Q SPA', 'MINING AND QUARRYING SPA'],
        'M S & D SPA': ['M S & D SPA', 'M S & D', 'MINING SERVICES AND DERIVATES SPA', 
                        'MINING SERVICES AND DERIVATES', 'MS&D SPA'],
        'JORQUERA TRANSPORTE S. A.': ['JORQUERA TRANSPORTE S. A.', 'JORQUERA TRANSPORTE S A'],
        'COSEDUCAM S A': ['COSEDUCAM S A', 'COSEDUCAM'],
        'AG SERVICES SPA': ['AG SERVICES SPA'],
        'ARTISA': ['ARTISA']
    }

    # Crear un mapeo de normalización
    mapeo_normalizacion = {}
    for nombre_principal, variantes in agrupaciones.items():
        for variante in variantes:
            mapeo_normalizacion[variante.upper().strip()] = nombre_principal

    # Función para normalizar un nombre individual
    def normalizar_nombre(nombre):
        if pd.isna(nombre):
            return nombre

        nombre_limpio = str(nombre).upper().strip()

        # Buscar coincidencia exacta primero
        if nombre_limpio in mapeo_normalizacion:
            return mapeo_normalizacion[nombre_limpio]

        # Buscar coincidencias parciales para casos no definidos
        for nombre_normalizado, variantes in agrupaciones.items():
            for variante in variantes:
                if variante.upper() in nombre_limpio or nombre_limpio in variante.upper():
                    return nombre_normalizado

        # Si no encuentra coincidencia, devolver el nombre original
        return nombre

    # Aplicar normalización
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
    st.title("📊 Dashboard Dinámico por Fecha y Empresa")
    st.markdown("Carga tu archivo Excel, elige una fecha y una o varias empresas para ver los dashboards filtrados.")

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
                # Normalizar nombres de empresas
                filtered_df = normalizar_nombres_empresas(filtered_df, empresa_col)
                empresa_col_normalizada = empresa_col + '_normalizada'

                st.markdown("---")
                st.header("🏢 Selecciona una o varias empresas")

                # Mostrar mapeo de normalización
                with st.expander("Ver agrupaciones de empresas"):
                    st.write("**Empresas agrupadas automáticamente:**")
                    mapeo_empresas = filtered_df.groupby(empresa_col_normalizada)[empresa_col].unique().to_dict()
                    for empresa_normalizada, variantes in mapeo_empresas.items():
                        if len(variantes) > 1:
                            st.write(f"• **{empresa_normalizada}**: {', '.join(variantes)}")
                        else:
                            st.write(f"• **{empresa_normalizada}**: {variantes[0]}")

                empresas = filtered_df[empresa_col_normalizada].dropna().unique().tolist()
                empresas_seleccionadas = st.multiselect(
                    "Empresas (nombres normalizados)",
                    options=empresas,
                    default=empresas,
                    key="empresas_multiselect"
                )
                filtered_df = filtered_df[filtered_df[empresa_col_normalizada].isin(empresas_seleccionadas)]
                if filtered_df.empty:
                    st.warning("No hay datos para la(s) empresa(s) seleccionada(s).")
                    return
            else:
                st.info("No se detectó ninguna columna de empresa. Se mostrarán todos los datos.")

            # Solo mostrar dashboards si hay datos filtrados
            if not filtered_df.empty:
                numeric_columns = filtered_df.select_dtypes(include=['number']).columns.tolist()
                categorical_columns = filtered_df.select_dtypes(include=['object', 'category']).columns.tolist()
                all_columns = filtered_df.columns.tolist()

                st.markdown("---")
                st.header("🎨 Dashboards y Gráficos")

                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "📈 Líneas/Barras",
                    "🥧 Circular",
                    "📊 Dispersión",
                    "📉 Histograma",
                    "🔥 Mapa de Calor"
                ])

                with tab1:
                    st.subheader("Gráficos de Líneas y Barras")
                    col1, col2 = st.columns(2)
                    with col1:
                        chart_type = st.selectbox(
                            "Tipo de gráfico",
                            ["Barras", "Líneas", "Barras horizontales"],
                            key="line_bar_type"
                        )
                        x_axis = st.selectbox("Eje X", all_columns, key="line_bar_x")
                        y_axis = st.selectbox("Eje Y", numeric_columns, key="line_bar_y")
                    with col2:
                        color_by = st.selectbox(
                            "Colorear por (opcional)",
                            [None] + categorical_columns,
                            key="line_bar_color"
                        )
                        title = st.text_input("Título del gráfico", f"{chart_type}: {y_axis} por {x_axis}", key="line_bar_title")
                    if st.button("Generar gráfico", key="generate_line_bar"):
                        if chart_type == "Barras":
                            fig = px.bar(filtered_df, x=x_axis, y=y_axis, color=color_by, title=title)
                        elif chart_type == "Líneas":
                            fig = px.line(filtered_df, x=x_axis, y=y_axis, color=color_by, title=title)
                        else:
                            fig = px.bar(filtered_df, x=y_axis, y=x_axis, color=color_by, title=title, orientation='h')
                        fig.update_layout(height=500)
                        st.plotly_chart(fig, use_container_width=True)

                with tab2:
                    st.subheader("Gráfico Circular (Pie)")
                    col1, col2 = st.columns(2)
                    with col1:
                        pie_values = st.selectbox("Valores", numeric_columns, key="pie_values")
                        pie_names = st.selectbox("Etiquetas", categorical_columns, key="pie_names")
                    with col2:
                        pie_title = st.text_input("Título", f"Distribución de {pie_values}", key="pie_title")
                        show_percentages = st.checkbox("Mostrar porcentajes", True, key="pie_percentages")
                    if st.button("Generar gráfico circular", key="generate_pie"):
                        pie_data = filtered_df.groupby(pie_names)[pie_values].sum().reset_index()
                        fig = px.pie(
                            pie_data,
                            values=pie_values,
                            names=pie_names,
                            title=pie_title
                        )
                        if show_percentages:
                            fig.update_traces(textposition='inside', textinfo='percent+label')
                        fig.update_layout(height=500)
                        st.plotly_chart(fig, use_container_width=True)

                with tab3:
                    st.subheader("Gráfico de Dispersión")
                    col1, col2 = st.columns(2)
                    with col1:
                        scatter_x = st.selectbox("Eje X", numeric_columns, key="scatter_x")
                        scatter_y = st.selectbox("Eje Y", numeric_columns, key="scatter_y")
                    with col2:
                        scatter_color = st.selectbox(
                            "Colorear por (opcional)",
                            [None] + categorical_columns + numeric_columns,
                            key="scatter_color"
                        )
                        scatter_size = st.selectbox(
                            "Tamaño por (opcional)",
                            [None] + numeric_columns,
                            key="scatter_size"
                        )
                    scatter_title = st.text_input("Título", f"Dispersión: {scatter_y} vs {scatter_x}", key="scatter_title")
                    if st.button("Generar dispersión", key="generate_scatter"):
                        fig = px.scatter(
                            filtered_df,
                            x=scatter_x,
                            y=scatter_y,
                            color=scatter_color,
                            size=scatter_size,
                            title=scatter_title,
                            hover_data=filtered_df.columns[:5].tolist()
                        )
                        fig.update_layout(height=500)
                        st.plotly_chart(fig, use_container_width=True)

                with tab4:
                    st.subheader("Histograma")
                    col1, col2 = st.columns(2)
                    with col1:
                        hist_column = st.selectbox("Columna", numeric_columns, key="hist_column")
                        bins = st.slider("Número de bins", 10, 100, 30, key="hist_bins")
                    with col2:
                        hist_color_by = st.selectbox(
                            "Separar por (opcional)",
                            [None] + categorical_columns,
                            key="hist_color"
                        )
                    hist_title = st.text_input("Título", f"Distribución de {hist_column}", key="hist_title")
                    if st.button("Generar histograma", key="generate_hist"):
                        fig = px.histogram(
                            filtered_df,
                            x=hist_column,
                            color=hist_color_by,
                            nbins=bins,
                            title=hist_title
                        )
                        fig.update_layout(height=500)
                        st.plotly_chart(fig, use_container_width=True)

                with tab5:
                    st.subheader("Mapa de Calor (Correlaciones)")
                    if len(numeric_columns) >= 2:
                        selected_columns = st.multiselect(
                            "Selecciona columnas numéricas",
                            numeric_columns,
                            default=numeric_columns[:5] if len(numeric_columns) >= 5 else numeric_columns,
                            key="heatmap_columns"
                        )
                        if len(selected_columns) >= 2:
                            if st.button("Generar mapa de calor", key="generate_heatmap"):
                                correlation_matrix = filtered_df[selected_columns].corr()
                                fig = px.imshow(
                                    correlation_matrix,
                                    title="Mapa de Calor - Correlaciones",
                                    color_continuous_scale="RdBu_r",
                                    aspect="auto"
                                )
                                fig.update_layout(height=500)
                                st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning("Selecciona al menos 2 columnas numéricas")
                    else:
                        st.warning("Se necesitan al menos 2 columnas numéricas para crear un mapa de calor")

                # Sección de estadísticas descriptivas
                st.markdown("---")
                st.header("📈 Estadísticas Descriptivas")
                if st.checkbox("Mostrar estadísticas", key="show_stats"):
                    st.subheader("Estadísticas de columnas numéricas")
                    st.dataframe(filtered_df.describe(), use_container_width=True)
                    if categorical_columns:
                        st.subheader("Información de columnas categóricas")
                        for idx, col in enumerate(categorical_columns[:3]):
                            st.write(f"**{col}:**")
                            value_counts = filtered_df[col].value_counts().head(10)
                            st.bar_chart(value_counts)

        except Exception as e:
            st.error(f"Error al procesar el archivo: {str(e)}")
            st.info("Asegúrate de que el archivo sea un Excel válido (.xlsx o .xls)")

    else:
        st.info("👆 Carga un archivo Excel desde la barra lateral para comenzar")
        st.markdown("### 📋 Formato de datos esperado")
        example_data = {
            'Fecha': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'Empresa': ['M&Q SPA', 'M & Q', 'JORQUERA TRANSPORTE S. A.'],
            'Ventas': [1000, 1500, 1200],
            'Producto': ['A', 'B', 'A'],
            'Region': ['Norte', 'Sur', 'Norte']
        }
        st.dataframe(pd.DataFrame(example_data))

if __name__ == "__main__":
    main()

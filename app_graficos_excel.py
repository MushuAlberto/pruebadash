
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def main():
    st.set_page_config(page_title="Generador de Gráficos Excel", layout="wide")

    st.title("📊 Generador de Gráficos desde Excel")
    st.markdown("Carga tu archivo Excel y crea gráficos interactivos fácilmente")

    # Sidebar para cargar archivo
    st.sidebar.header("📁 Cargar Datos")
    uploaded_file = st.sidebar.file_uploader(
        "Selecciona tu archivo Excel",
        type=['xlsx', 'xls'],
        help="Formatos soportados: .xlsx, .xls"
    )

    if uploaded_file is not None:
        try:
            # Leer el archivo Excel
            df = pd.read_excel(uploaded_file)

            st.sidebar.success(f"✅ Archivo cargado: {uploaded_file.name}")
            st.sidebar.info(f"Filas: {len(df)} | Columnas: {len(df.columns)}")

            # Detectar columnas de tipo fecha
            date_columns = df.select_dtypes(include=['datetime', 'datetime64[ns]', 'datetime64[ns, UTC]']).columns.tolist()
            if not date_columns:
                # Intentar convertir columnas con nombre típico a fecha
                for col in df.columns:
                    if 'fecha' in col.lower() or 'date' in col.lower():
                        try:
                            df[col] = pd.to_datetime(df[col])
                            date_columns.append(col)
                        except Exception:
                            pass

            # Mostrar vista previa de los datos
            with st.expander("👀 Vista previa de los datos", expanded=True):
                st.dataframe(df.head(10), use_container_width=True)

            # Información básica del dataset
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de filas", len(df))
            with col2:
                st.metric("Total de columnas", len(df.columns))
            with col3:
                st.metric("Valores nulos", df.isnull().sum().sum())

            # Si hay columnas de fecha, mostrar selector en la página principal
            if date_columns:
                st.markdown("---")
                st.header("📅 Selecciona una fecha para filtrar los datos")
                date_col = st.selectbox("Columna de fecha", date_columns, key="main_date_col")
                min_date = df[date_col].min().date()
                max_date = df[date_col].max().date()
                selected_date = st.date_input("Selecciona la fecha", min_value=min_date, max_value=max_date, value=min_date, key="main_date_input")
                # Filtrar el DataFrame por la fecha seleccionada
                filtered_df = df[df[date_col].dt.date == selected_date]
                if filtered_df.empty:
                    st.warning("No hay datos para la fecha seleccionada. Por favor, elige otra fecha.")
                    return
            else:
                filtered_df = df.copy()
                selected_date = None

            # Separar columnas numéricas y categóricas
            numeric_columns = filtered_df.select_dtypes(include=['number']).columns.tolist()
            categorical_columns = filtered_df.select_dtypes(include=['object', 'category']).columns.tolist()
            all_columns = filtered_df.columns.tolist()

            st.markdown("---")
            st.header("🎨 Crear Gráficos")

            # Tabs para diferentes tipos de gráficos
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
                    title = st.text_input("Título del gráfico", f"{chart_type}: {y_axis} por {x_axis}")

                if st.button("Generar gráfico", key="generate_line_bar"):
                    if chart_type == "Barras":
                        fig = px.bar(filtered_df, x=x_axis, y=y_axis, color=color_by, title=title)
                    elif chart_type == "Líneas":
                        fig = px.line(filtered_df, x=x_axis, y=y_axis, color=color_by, title=title)
                    else:  # Barras horizontales
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
                    pie_title = st.text_input("Título", f"Distribución de {pie_values}")
                    show_percentages = st.checkbox("Mostrar porcentajes", True)

                if st.button("Generar gráfico circular", key="generate_pie"):
                    # Agrupar datos si es necesario
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

                scatter_title = st.text_input("Título", f"Dispersión: {scatter_y} vs {scatter_x}")

                if st.button("Generar dispersión", key="generate_scatter"):
                    fig = px.scatter(
                        filtered_df, 
                        x=scatter_x, 
                        y=scatter_y, 
                        color=scatter_color,
                        size=scatter_size,
                        title=scatter_title,
                        hover_data=filtered_df.columns[:5].tolist()  # Mostrar primeras 5 columnas en hover
                    )

                    fig.update_layout(height=500)
                    st.plotly_chart(fig, use_container_width=True)

            with tab4:
                st.subheader("Histograma")
                col1, col2 = st.columns(2)

                with col1:
                    hist_column = st.selectbox("Columna", numeric_columns, key="hist_column")
                    bins = st.slider("Número de bins", 10, 100, 30)

                with col2:
                    hist_color_by = st.selectbox(
                        "Separar por (opcional)", 
                        [None] + categorical_columns,
                        key="hist_color"
                    )

                hist_title = st.text_input("Título", f"Distribución de {hist_column}")

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
                        default=numeric_columns[:5] if len(numeric_columns) >= 5 else numeric_columns
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

            if st.checkbox("Mostrar estadísticas"):
                st.subheader("Estadísticas de columnas numéricas")
                st.dataframe(filtered_df.describe(), use_container_width=True)

                if categorical_columns:
                    st.subheader("Información de columnas categóricas")
                    for col in categorical_columns[:3]:  # Mostrar solo las primeras 3
                        st.write(f"**{col}:**")
                        value_counts = filtered_df[col].value_counts().head(10)
                        st.bar_chart(value_counts)

        except Exception as e:
            st.error(f"Error al procesar el archivo: {str(e)}")
            st.info("Asegúrate de que el archivo sea un Excel válido (.xlsx o .xls)")

    else:
        st.info("👆 Carga un archivo Excel desde la barra lateral para comenzar")

        # Mostrar ejemplo de datos esperados
        st.markdown("### 📋 Formato de datos esperado")
        example_data = {
            'Fecha': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'Ventas': [1000, 1500, 1200],
            'Producto': ['A', 'B', 'A'],
            'Region': ['Norte', 'Sur', 'Norte']
        }
        st.dataframe(pd.DataFrame(example_data))

if __name__ == "__main__":
    main()

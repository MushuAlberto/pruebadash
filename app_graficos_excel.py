import streamlit as st
import pandas as pd
import plotly.express as px

def detectar_columna_fecha(df):
    # Buscar columnas que ya sean datetime
    date_cols = df.select_dtypes(include=['datetime', 'datetime64[ns]', 'datetime64[ns, UTC]']).columns.tolist()
    # Si no hay, intentar convertir columnas con nombres típicos
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

def main():
    st.set_page_config(page_title="Dashboard por Fecha", layout="wide")
    st.title("📊 Dashboard Dinámico por Fecha")
    st.markdown("Carga tu archivo Excel, elige una fecha y explora los datos filtrados en los dashboards.")

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
                # Eliminar filas con fecha nula
                df = df[df[date_col].notnull()]
                # Mostrar rango de fechas
                min_date = df[date_col].min().date()
                max_date = df[date_col].max().date()
                # Selector de fecha
                selected_date = st.date_input(
                    "Selecciona la fecha",
                    min_value=min_date,
                    max_value=max_date,
                    value=min_date,
                    key="main_date_input"
                )
                # Filtrar el DataFrame por la fecha seleccionada
                filtered_df = df[df[date_col].dt.date == selected_date]
                if filtered_df.empty:
                    st.warning("No hay datos para la fecha seleccionada. Por favor, elige otra fecha.")
                    return
            else:
                st.info("No se detectó ninguna columna de fecha. Se mostrarán todos los datos.")
                filtered_df = df.copy()

            # Solo mostrar dashboards si hay datos filtrados
            if not filtered_df.empty:
                numeric_columns = filtered_df.select_dtypes(include=['number']).columns.tolist()
                categorical_columns = filtered_df.select_dtypes(include=['object', 'category']).columns.tolist()
                all_columns = filtered_df.columns.tolist()

                st.markdown("---")
                st.header("🎨 Dashboards y Gráficos")

                tab1, tab2, tab3 = st.tabs([
                    "📈 Líneas/Barras",
                    "🥧 Circular",
                    "📊 Dispersión"
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

        except Exception as e:
            st.error(f"Error al procesar el archivo: {str(e)}")
            st.info("Asegúrate de que el archivo sea un Excel válido (.xlsx o .xls)")

    else:
        st.info("👆 Carga un archivo Excel desde la barra lateral para comenzar")
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
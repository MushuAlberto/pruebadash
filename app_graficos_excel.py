import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Dashboard Ejecutivo Histórico Romanas", layout="wide")
st.title('Dashboard Ejecutivo Histórico Romanas')

# --- CARGA MANUAL DEL ARCHIVO ---
uploaded_file = st.file_uploader("Sube el archivo Excel (.xlsx) de Histórico Romanas", type=["xlsx"])

if 'show_dashboard' not in st.session_state:
    st.session_state.show_dashboard = False

if uploaded_file is not None:
    @st.cache_data
    def load_data(file):
        df = pd.read_excel(file)
        df.columns = [c.strip().upper() for c in df.columns]
        df['FECHA'] = pd.to_datetime(df['FECHA'], dayfirst=True, errors='coerce')
        for col in ['PRODUCTO', 'DESTINO', 'EMPRESA DE TRANSPORTE']:
            df[col] = df[col].astype(str).str.strip()
        df['FECHA_DATE'] = df['FECHA'].dt.date  # Para comparación robusta
        return df

    df = load_data(uploaded_file)
    fechas_disponibles = sorted(df['FECHA_DATE'].dropna().unique())
    selected_date = st.date_input(
        'Selecciona la fecha a analizar',
        fechas_disponibles[-1],
        min_value=fechas_disponibles[0],
        max_value=fechas_disponibles[-1]
    )

# El botón SIEMPRE se muestra, incluso antes de subir el archivo
if st.button("Siguiente ➡️"):
    st.session_state.show_dashboard = True

if st.session_state.show_dashboard:
    if uploaded_file is not None:
        # --- FILTRADO DE DATOS ---
        df_hoy = df[df['FECHA_DATE'] == selected_date]
        fecha_ayer = selected_date - timedelta(days=1)
        df_ayer = df[df['FECHA_DATE'] == fecha_ayer]

        # --- KPIs ---
        tonelaje_hoy = df_hoy['TONELAJE'].sum()
        top_destino_hoy = df_hoy['DESTINO'].mode()[0] if not df_hoy.empty else 'Sin datos'
        top_producto_hoy = df_hoy['PRODUCTO'].mode()[0] if not df_hoy.empty else 'Sin datos'
        tonelaje_ayer = df_ayer['TONELAJE'].sum()
        variacion = ((tonelaje_hoy - tonelaje_ayer) / tonelaje_ayer * 100) if tonelaje_ayer > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric('Tonelaje Hoy', f"{tonelaje_hoy:,.2f}")
        col2.metric('Variación vs. Ayer', f"{variacion:+.1f}%")
        col3.metric('Top Destino', top_destino_hoy)
        col4.metric('Top Producto', top_producto_hoy)

        st.markdown("---")

        # --- GRÁFICO DE BARRAS AGRUPADAS: Tonelaje por destino hoy vs. ayer ---
        gb_df = pd.concat([
            df_hoy.groupby('DESTINO')['TONELAJE'].sum().rename('Hoy'),
            df_ayer.groupby('DESTINO')['TONELAJE'].sum().rename('Ayer')
        ], axis=1).fillna(0).reset_index()

        fig_bar = px.bar(
            gb_df,
            x='DESTINO',
            y=['Hoy', 'Ayer'],
            barmode='group',
            color_discrete_map={'Hoy': '#1f77b4', 'Ayer': '#cccccc'},
            title='Tonelaje por Destino (Hoy vs. Ayer)'
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # --- GRÁFICO DE LÍNEAS: Evolución últimos 7 días ---
        ultimos_7 = df[df['FECHA_DATE'] >= selected_date - timedelta(days=6)]
        line_df = ultimos_7.groupby(['FECHA_DATE', 'DESTINO'])['TONELAJE'].sum().reset_index()
        fig_line = px.line(
            line_df,
            x='FECHA_DATE',
            y='TONELAJE',
            color='DESTINO',
            markers=True,
            title='Evolución de Tonelaje por Destino (Últimos 7 días)'
        )
        st.plotly_chart(fig_line, use_container_width=True)

        # --- ANÁLISIS EJECUTIVO AUTOMÁTICO ---
        st.subheader('Análisis Ejecutivo')
        if tonelaje_ayer > 0:
            if variacion > 0:
                st.success(
                    f"El tonelaje total aumentó {variacion:.1f}% respecto a ayer. "
                    f"El destino con mayor movimiento fue **{top_destino_hoy}** y el producto más transportado fue **{top_producto_hoy}**."
                )
            elif variacion < 0:
                st.warning(
                    f"El tonelaje total disminuyó {abs(variacion):.1f}% respecto a ayer. "
                    f"El destino con mayor movimiento fue **{top_destino_hoy}** y el producto más transportado fue **{top_producto_hoy}**."
                )
            else:
                st.info(
                    f"El tonelaje total se mantuvo igual que ayer. "
                    f"El destino con mayor movimiento fue **{top_destino_hoy}** y el producto más transportado fue **{top_producto_hoy}**."
                )
        else:
            st.info("No hay datos del día anterior para comparar.")

        # --- INFORME SLIT ---
        st.subheader('Informe de Producto - SLIT')
        df_slit = df_hoy[df_hoy['PRODUCTO'].str.upper() == 'SLIT']
        if not df_slit.empty:
            tonelaje_slit = df_slit['TONELAJE'].sum()
            destinos_slit = df_slit['DESTINO'].unique()
            st.markdown(f"**Tonelaje SLIT hoy:** {tonelaje_slit:,.2f}")
            st.markdown(f"**Destinos SLIT hoy:** {', '.join(destinos_slit)}")
            fig_slit = px.bar(
                df_slit,
                x='DESTINO',
                y='TONELAJE',
                color='DESTINO',
                title='Tonelaje SLIT por Destino (Hoy)'
            )
            st.plotly_chart(fig_slit, use_container_width=True)
        else:
            st.info('No hay movimientos de SLIT para la fecha seleccionada.')
    else:
        st.info("Por favor, sube un archivo Excel para comenzar.")
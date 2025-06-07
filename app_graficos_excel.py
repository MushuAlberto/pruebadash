# Crear el código completo con análisis ejecutivo e informe de SLIT
codigo_completo_ejecutivo = '''import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import unicodedata
from datetime import datetime, timedelta

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

def crear_grafico_comparacion(df_hoy, df_ayer, empresa, col_producto, col_tonelaje, col_destino, fecha_hoy, fecha_ayer):
    """Crea un gráfico de comparación entre dos días para una empresa"""
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=[f"{fecha_hoy.strftime('%d/%m/%Y')}", f"{fecha_ayer.strftime('%d/%m/%Y')}"],
        shared_yaxes=True
    )
    
    # Gráfico del día actual
    if not df_hoy.empty:
        for destino in df_hoy[col_destino].unique():
            df_destino = df_hoy[df_hoy[col_destino] == destino]
            fig.add_trace(
                go.Scatter(
                    x=df_destino[col_producto],
                    y=df_destino[col_tonelaje],
                    mode='lines+markers',
                    name=f"{destino} (Hoy)",
                    line=dict(width=3),
                    marker=dict(size=8)
                ),
                row=1, col=1
            )
    
    # Gráfico del día anterior
    if not df_ayer.empty:
        for destino in df_ayer[col_destino].unique():
            df_destino = df_ayer[df_ayer[col_destino] == destino]
            fig.add_trace(
                go.Scatter(
                    x=df_destino[col_producto],
                    y=df_destino[col_tonelaje],
                    mode='lines+markers',
                    name=f"{destino} (Ayer)",
                    line=dict(width=3, dash='dash'),
                    marker=dict(size=8)
                ),
                row=1, col=2
            )
    
    fig.update_layout(
        title=f"Comparación {empresa}: {fecha_hoy.strftime('%d/%m/%Y')} vs {fecha_ayer.strftime('%d/%m/%Y')}",
        height=500
    )
    fig.update_xaxes(title_text="Producto")
    fig.update_yaxes(title_text="Tonelaje")
    
    return fig

def generar_analisis_ejecutivo(filtered_df_hoy, filtered_df_ayer, selected_date, previous_date, 
                              col_tonelaje, col_empresa, col_destino, col_producto, col_tiempo):
    """Genera análisis ejecutivo automatizado"""
    
    # Calcular métricas principales
    total_tonelaje_hoy = filtered_df_hoy[col_tonelaje].sum()
    total_tonelaje_ayer = filtered_df_ayer[col_tonelaje].sum() if not filtered_df_ayer.empty else 0
    diferencia_tonelaje = total_tonelaje_hoy - total_tonelaje_ayer
    porcentaje_cambio = (diferencia_tonelaje / total_tonelaje_ayer * 100) if total_tonelaje_ayer > 0 else 0
    
    empresas_hoy = len(filtered_df_hoy[col_empresa + '_normalizada'].unique())
    empresas_ayer = len(filtered_df_ayer[col_empresa + '_normalizada'].unique()) if not filtered_df_ayer.empty else 0
    
    # Análisis por empresa
    empresas_rendimiento = []
    for empresa in filtered_df_hoy[col_empresa + '_normalizada'].unique():
        tonelaje_hoy = filtered_df_hoy[filtered_df_hoy[col_empresa + '_normalizada'] == empresa][col_tonelaje].sum()
        tonelaje_ayer = filtered_df_ayer[filtered_df_ayer[col_empresa + '_normalizada'] == empresa][col_tonelaje].sum() if not filtered_df_ayer.empty else 0
        cambio = tonelaje_hoy - tonelaje_ayer
        porcentaje_empresa = (cambio / tonelaje_ayer * 100) if tonelaje_ayer > 0 else 0
        empresas_rendimiento.append({
            'empresa': empresa,
            'tonelaje_hoy': tonelaje_hoy,
            'tonelaje_ayer': tonelaje_ayer,
            'cambio': cambio,
            'porcentaje': porcentaje_empresa
        })
    
    # Ordenar por rendimiento
    empresas_rendimiento.sort(key=lambda x: x['porcentaje'], reverse=True)
    
    return {
        'total_tonelaje_hoy': total_tonelaje_hoy,
        'total_tonelaje_ayer': total_tonelaje_ayer,
        'diferencia_tonelaje': diferencia_tonelaje,
        'porcentaje_cambio': porcentaje_cambio,
        'empresas_hoy': empresas_hoy,
        'empresas_ayer': empresas_ayer,
        'empresas_rendimiento': empresas_rendimiento
    }

def generar_informe_slit(filtered_df_hoy, filtered_df_ayer, col_producto, col_tonelaje, 
                        col_destino, col_empresa):
    """Genera informe específico del producto SLIT"""
    
    # Filtrar datos de SLIT
    slit_hoy = filtered_df_hoy[filtered_df_hoy[col_producto].str.upper().str.contains('SLIT', na=False)]
    slit_ayer = filtered_df_ayer[filtered_df_ayer[col_producto].str.upper().str.contains('SLIT', na=False)] if not filtered_df_ayer.empty else pd.DataFrame()
    
    # Métricas de SLIT
    tonelaje_slit_hoy = slit_hoy[col_tonelaje].sum() if not slit_hoy.empty else 0
    tonelaje_slit_ayer = slit_ayer[col_tonelaje].sum() if not slit_ayer.empty else 0
    diferencia_slit = tonelaje_slit_hoy - tonelaje_slit_ayer
    porcentaje_slit = (diferencia_slit / tonelaje_slit_ayer * 100) if tonelaje_slit_ayer > 0 else 0
    
    # Destinos principales para SLIT
    destinos_slit = []
    if not slit_hoy.empty:
        destinos_agrupados = slit_hoy.groupby(col_destino)[col_tonelaje].sum().sort_values(ascending=False)
        for destino, tonelaje in destinos_agrupados.head(5).items():
            tonelaje_ayer_destino = slit_ayer[slit_ayer[col_destino] == destino][col_tonelaje].sum() if not slit_ayer.empty else 0
            cambio_destino = tonelaje - tonelaje_ayer_destino
            destinos_slit.append({
                'destino': destino,
                'tonelaje_hoy': tonelaje,
                'tonelaje_ayer': tonelaje_ayer_destino,
                'cambio': cambio_destino
            })
    
    # Empresas que transportan SLIT
    empresas_slit = []
    if not slit_hoy.empty:
        empresas_agrupadas = slit_hoy.groupby(col_empresa + '_normalizada')[col_tonelaje].sum().sort_values(ascending=False)
        for empresa, tonelaje in empresas_agrupadas.head(5).items():
            tonelaje_ayer_empresa = slit_ayer[slit_ayer[col_empresa + '_normalizada'] == empresa][col_tonelaje].sum() if not slit_ayer.empty else 0
            cambio_empresa = tonelaje - tonelaje_ayer_empresa
            empresas_slit.append({
                'empresa': empresa,
                'tonelaje_hoy': tonelaje,
                'tonelaje_ayer': tonelaje_ayer_empresa,
                'cambio': cambio_empresa
            })
    
    return {
        'tonelaje_slit_hoy': tonelaje_slit_hoy,
        'tonelaje_slit_ayer': tonelaje_slit_ayer,
        'diferencia_slit': diferencia_slit,
        'porcentaje_slit': porcentaje_slit,
        'destinos_slit': destinos_slit,
        'empresas_slit': empresas_slit,
        'tiene_datos': not slit_hoy.empty
    }

st.set_page_config(page_title="Dashboard Ejecutivo Comparativo", layout="wide")
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
    .executive-summary {
        background-color: #f8f9fa;
        border-left: 5px solid #007bff;
        padding: 20px;
        margin: 20px 0;
        border-radius: 5px;
    }
    .alert-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .alert-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .alert-danger {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    </style>
    <div class='banner-container'>
        <img src='assets/banner.png' style='width: 100%; height: auto; display: block;'>
    </div>
    """,
    unsafe_allow_html=True
)

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
        
        # Calcular fecha anterior
        previous_date = selected_date - timedelta(days=1)
        
        # Filtrar datos para ambos días
        filtered_df_hoy = df[df[col_fecha].dt.date == selected_date]
        filtered_df_ayer = df[df[col_fecha].dt.date == previous_date]
        
        if filtered_df_hoy.empty:
            st.warning("No hay datos para la fecha seleccionada. Por favor, elige otra fecha.")
            st.stop()

        # ANÁLISIS EJECUTIVO
        st.markdown("---")
        st.markdown("# 🎯 ANÁLISIS EJECUTIVO")
        
        analisis = generar_analisis_ejecutivo(
            filtered_df_hoy, filtered_df_ayer, selected_date, previous_date,
            col_tonelaje, col_empresa, col_destino, col_producto, col_tiempo
        )
        
        # Resumen ejecutivo principal
        st.markdown(
            f"""
            <div class="executive-summary">
                <h2>📊 RESUMEN EJECUTIVO - {selected_date.strftime('%d/%m/%Y')}</h2>
                <h3>🎯 RENDIMIENTO GENERAL</h3>
                <p><strong>Tonelaje Total:</strong> {analisis['total_tonelaje_hoy']:,.0f} ton 
                   ({analisis['diferencia_tonelaje']:+,.0f} ton vs ayer | {analisis['porcentaje_cambio']:+.1f}%)</p>
                <p><strong>Empresas Activas:</strong> {analisis['empresas_hoy']} empresas</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Alertas automáticas
        st.markdown("### 🚨 ALERTAS Y DESTACADOS")
        
        # Top performer y alertas
        if analisis['empresas_rendimiento']:
            mejor_empresa = analisis['empresas_rendimiento'][0]
            peor_empresa = analisis['empresas_rendimiento'][-1]
            
            col1, col2 = st.columns(2)
            with col1:
                if mejor_empresa['porcentaje'] > 10:
                    st.markdown(
                        f"""
                        <div class="alert-success">
                            🏆 <strong>TOP PERFORMER:</strong> {mejor_empresa['empresa']}<br>
                            Incremento: {mejor_empresa['porcentaje']:+.1f}% ({mejor_empresa['cambio']:+,.0f} ton)
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"""
                        <div class="alert-warning">
                            📈 <strong>MEJOR RENDIMIENTO:</strong> {mejor_empresa['empresa']}<br>
                            Cambio: {mejor_empresa['porcentaje']:+.1f}% ({mejor_empresa['cambio']:+,.0f} ton)
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            
            with col2:
                if peor_empresa['porcentaje'] < -10:
                    st.markdown(
                        f"""
                        <div class="alert-danger">
                            ⚠️ <strong>ALERTA CRÍTICA:</strong> {peor_empresa['empresa']}<br>
                            Caída: {peor_empresa['porcentaje']:.1f}% ({peor_empresa['cambio']:,.0f} ton)
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                elif peor_empresa['porcentaje'] < 0:
                    st.markdown(
                        f"""
                        <div class="alert-warning">
                            📉 <strong>REQUIERE ATENCIÓN:</strong> {peor_empresa['empresa']}<br>
                            Caída: {peor_empresa['porcentaje']:.1f}% ({peor_empresa['cambio']:,.0f} ton)
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        
        # Ranking de empresas
        st.markdown("### 📈 RANKING DE EMPRESAS")
        ranking_data = []
        for i, empresa_data in enumerate(analisis['empresas_rendimiento'][:5], 1):
            ranking_data.append({
                'Posición': i,
                'Empresa': empresa_data['empresa'],
                'Tonelaje Hoy': f"{empresa_data['tonelaje_hoy']:,.0f}",
                'Tonelaje Ayer': f"{empresa_data['tonelaje_ayer']:,.0f}",
                'Cambio': f"{empresa_data['cambio']:+,.0f}",
                'Variación %': f"{empresa_data['porcentaje']:+.1f}%"
            })
        
        st.dataframe(pd.DataFrame(ranking_data), use_container_width=True)
        
        # INFORME DE PRODUCTO SLIT
        st.markdown("---")
        st.markdown("# 📦 INFORME DE PRODUCTO - SLIT")
        
        informe_slit = generar_informe_slit(
            filtered_df_hoy, filtered_df_ayer, col_producto, col_tonelaje,
            col_destino, col_empresa
        )
        
        if informe_slit['tiene_datos']:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Tonelaje SLIT HOY",
                    f"{informe_slit['tonelaje_slit_hoy']:,.0f} ton",
                    delta=f"{informe_slit['diferencia_slit']:+,.0f} ton"
                )
            
            with col2:
                st.metric(
                    "Tonelaje SLIT AYER",
                    f"{informe_slit['tonelaje_slit_ayer']:,.0f} ton"
                )
            
            with col3:
                st.metric(
                    "Variación SLIT",
                    f"{informe_slit['porcentaje_slit']:+.1f}%"
                )
            
            # Destinos principales para SLIT
            if informe_slit['destinos_slit']:
                st.markdown("#### 📍 DESTINOS PRINCIPALES - SLIT")
                destinos_data = []
                for destino_data in informe_slit['destinos_slit']:
                    destinos_data.append({
                        'Destino': destino_data['destino'],
                        'Tonelaje Hoy': f"{destino_data['tonelaje_hoy']:,.0f}",
                        'Tonelaje Ayer': f"{destino_data['tonelaje_ayer']:,.0f}",
                        'Cambio': f"{destino_data['cambio']:+,.0f}"
                    })
                st.dataframe(pd.DataFrame(destinos_data), use_container_width=True)
            
            # Empresas que transportan SLIT
            if informe_slit['empresas_slit']:
                st.markdown("#### 🚚 EMPRESAS DE TRANSPORTE - SLIT")
                empresas_slit_data = []
                for empresa_data in informe_slit['empresas_slit']:
                    empresas_slit_data.append({
                        'Empresa': empresa_data['empresa'],
                        'Tonelaje Hoy': f"{empresa_data['tonelaje_hoy']:,.0f}",
                        'Tonelaje Ayer': f"{empresa_data['tonelaje_ayer']:,.0f}",
                        'Cambio': f"{empresa_data['cambio']:+,.0f}"
                    })
                st.dataframe(pd.DataFrame(empresas_slit_data), use_container_width=True)
            
            # Alertas específicas de SLIT
            st.markdown("#### 🚨 ALERTAS SLIT")
            if informe_slit['porcentaje_slit'] < -15:
                st.markdown(
                    f"""
                    <div class="alert-danger">
                        ⚠️ <strong>ALERTA CRÍTICA SLIT:</strong> Caída significativa del {informe_slit['porcentaje_slit']:.1f}%<br>
                        Requiere investigación inmediata
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            elif informe_slit['porcentaje_slit'] > 15:
                st.markdown(
                    f"""
                    <div class="alert-success">
                        🎉 <strong>EXCELENTE RENDIMIENTO SLIT:</strong> Incremento del {informe_slit['porcentaje_slit']:+.1f}%<br>
                        Analizar factores de éxito para replicar
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("No se encontraron datos del producto SLIT para las fechas seleccionadas.")
        
        # RECOMENDACIONES AUTOMÁTICAS
        st.markdown("---")
        st.markdown("# 💡 RECOMENDACIONES EJECUTIVAS")
        
        recomendaciones = []
        
        # Recomendaciones basadas en rendimiento general
        if analisis['porcentaje_cambio'] < -10:
            recomendaciones.append("🔍 **URGENTE:** Investigar causas de la caída general del tonelaje")
        elif analisis['porcentaje_cambio'] > 15:
            recomendaciones.append("📈 **OPORTUNIDAD:** Analizar factores de éxito para mantener el crecimiento")
        
        # Recomendaciones por empresa
        if analisis['empresas_rendimiento']:
            peor_empresa = analisis['empresas_rendimiento'][-1]
            if peor_empresa['porcentaje'] < -20:
                recomendaciones.append(f"⚠️ **ACCIÓN INMEDIATA:** Reunión urgente con {peor_empresa['empresa']} para resolver problemas operacionales")
            
            mejor_empresa = analisis['empresas_rendimiento'][0]
            if mejor_empresa['porcentaje'] > 20:
                recomendaciones.append(f"🏆 **BEST PRACTICE:** Documentar y replicar estrategias exitosas de {mejor_empresa['empresa']}")
        
        # Recomendaciones de SLIT
        if informe_slit['tiene_datos']:
            if informe_slit['porcentaje_slit'] < -15:
                recomendaciones.append("📦 **SLIT CRÍTICO:** Revisar cadena de suministro y logística de SLIT")
            elif informe_slit['porcentaje_slit'] > 20:
                recomendaciones.append("📦 **SLIT EXITOSO:** Priorizar recursos para mantener momentum en SLIT")
        
        # Mostrar recomendaciones
        for i, recomendacion in enumerate(recomendaciones, 1):
            st.markdown(f"{i}. {recomendacion}")
        
        if not recomendaciones:
            st.markdown("✅ **OPERACIÓN ESTABLE:** Mantener monitoreo continuo de indicadores clave")

        # Indicadores de Tiempo Operacional para ambos días
        st.markdown("---")
        st.markdown("# ⏱️ INDICADORES OPERACIONALES")
        col1, col2 = st.columns(2)
        
        with col1:
            if col_tiempo and col_tiempo in filtered_df_hoy.columns:
                tiempo_operacional_hoy = pd.to_numeric(filtered_df_hoy[col_tiempo], errors='coerce').mean()
                horas_hoy = int(tiempo_operacional_hoy) // 60 if pd.notnull(tiempo_operacional_hoy) else 0
                minutos_hoy = int(tiempo_operacional_hoy) % 60 if pd.notnull(tiempo_operacional_hoy) else 0
                tiempo_str_hoy = f"{horas_hoy}:{minutos_hoy:02d}" if pd.notnull(tiempo_operacional_hoy) else "N/A"
            else:
                tiempo_str_hoy = "N/A"
            st.markdown(
                f"""
                <div style='background-color:#e6f4ea; border:1px solid #4caf50; border-radius:5px; padding:10px; text-align:center; width:300px; margin:auto;'>
                    <b>Tiempo Operacional HOY</b><br>
                    <span style='color:red; font-size:1.5em;'><b>{tiempo_str_hoy}</b></span><br>
                    <small>{selected_date.strftime('%d/%m/%Y')}</small>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col2:
            if col_tiempo and col_tiempo in filtered_df_ayer.columns and not filtered_df_ayer.empty:
                tiempo_operacional_ayer = pd.to_numeric(filtered_df_ayer[col_tiempo], errors='coerce').mean()
                horas_ayer = int(tiempo_operacional_ayer) // 60 if pd.notnull(tiempo_operacional_ayer) else 0
                minutos_ayer = int(tiempo_operacional_ayer) % 60 if pd.notnull(tiempo_operacional_ayer) else 0
                tiempo_str_ayer = f"{horas_ayer}:{minutos_ayer:02d}" if pd.notnull(tiempo_operacional_ayer) else "N/A"
            else:
                tiempo_str_ayer = "N/A"
            st.markdown(
                f"""
                <div style='background-color:#fff3cd; border:1px solid #ffc107; border-radius:5px; padding:10px; text-align:center; width:300px; margin:auto;'>
                    <b>Tiempo Operacional AYER</b><br>
                    <span style='color:orange; font-size:1.5em;'><b>{tiempo_str_ayer}</b></span><br>
                    <small>{previous_date.strftime('%d/%m/%Y')}</small>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        st.markdown("---")

        # Gráficos automáticos por empresa para HOY
        st.markdown(f"## Gráficos del día seleccionado: {selected_date.strftime('%d/%m/%Y')}")
        empresas_hoy = filtered_df_hoy[empresa_col_normalizada].dropna().unique().tolist()
        if not empresas_hoy:
            st.info("No hay empresas para la fecha seleccionada.")
        else:
            for empresa in empresas_hoy:
                df_empresa_hoy = filtered_df_hoy[filtered_df_hoy[empresa_col_normalizada] == empresa]
                if not df_empresa_hoy.empty:
                    st.markdown(f"### {empresa}")
                    df_empresa_hoy = df_empresa_hoy.sort_values(by=col_producto)
                    df_empresa_hoy[col_producto] = df_empresa_hoy[col_producto].astype(str)
                    fig = px.line(
                        df_empresa_hoy,
                        x=col_producto,
                        y=col_tonelaje,
                        color=col_destino,
                        markers=True,
                        line_shape="linear",
                        title=f"{empresa}: PRODUCTO vs TONELAJE - {selected_date.strftime('%d/%m/%Y')}",
                        labels={col_producto: "Producto", col_tonelaje: "Tonelaje", col_destino: "Destino"}
                    )
                    st.plotly_chart(fig, use_container_width=True)

        # Gráficos automáticos por empresa para AYER
        st.markdown(f"## Gráficos del día anterior: {previous_date.strftime('%d/%m/%Y')}")
        empresas_ayer = filtered_df_ayer[empresa_col_normalizada].dropna().unique().tolist() if not filtered_df_ayer.empty else []
        if not empresas_ayer:
            st.info("No hay datos para el día anterior.")
        else:
            for empresa in empresas_ayer:
                df_empresa_ayer = filtered_df_ayer[filtered_df_ayer[empresa_col_normalizada] == empresa]
                if not df_empresa_ayer.empty:
                    st.markdown(f"### {empresa}")
                    df_empresa_ayer = df_empresa_ayer.sort_values(by=col_producto)
                    df_empresa_ayer[col_producto] = df_empresa_ayer[col_producto].astype(str)
                    fig = px.line(
                        df_empresa_ayer,
                        x=col_producto,
                        y=col_tonelaje,
                        color=col_destino,
                        markers=True,
                        line_shape="linear",
                        title=f"{empresa}: PRODUCTO vs TONELAJE - {previous_date.strftime('%d/%m/%Y')}",
                        labels={col_producto: "Producto", col_tonelaje: "Tonelaje", col_destino: "Destino"}
                    )
                    st.plotly_chart(fig, use_container_width=True)

        # Sección de comparación
        st.markdown("---")
        st.markdown("## 📊 Comparación entre días")
        
        # Obtener empresas que aparecen en ambos días
        empresas_comunes = list(set(empresas_hoy) & set(empresas_ayer))
        
        if empresas_comunes:
            st.markdown(f"### Empresas con datos en ambos días ({len(empresas_comunes)})")
            for empresa in empresas_comunes:
                df_empresa_hoy = filtered_df_hoy[filtered_df_hoy[empresa_col_normalizada] == empresa]
                df_empresa_ayer = filtered_df_ayer[filtered_df_ayer[empresa_col_normalizada] == empresa]
                
                if not df_empresa_hoy.empty and not df_empresa_ayer.empty:
                    st.markdown(f"#### {empresa}")
                    
                    # Crear gráfico de comparación
                    fig_comp = crear_grafico_comparacion(
                        df_empresa_hoy, df_empresa_ayer, empresa, 
                        col_producto, col_tonelaje, col_destino,
                        selected_date, previous_date
                    )
                    st.plotly_chart(fig_comp, use_container_width=True)
                    
                    # Tabla de comparación de totales
                    col1, col2 = st.columns(2)
                    with col1:
                        total_hoy = df_empresa_hoy[col_tonelaje].sum()
                        st.metric(
                            label=f"Total Tonelaje HOY ({selected_date.strftime('%d/%m')})",
                            value=f"{total_hoy:,.0f}",
                            delta=None
                        )
                    with col2:
                        total_ayer = df_empresa_ayer[col_tonelaje].sum()
                        diferencia = total_hoy - total_ayer
                        st.metric(
                            label=f"Total Tonelaje AYER ({previous_date.strftime('%d/%m')})",
                            value=f"{total_ayer:,.0f}",
                            delta=f"{diferencia:+,.0f}"
                        )
        else:
            st.info("No hay empresas con datos en ambos días para comparar.")
            
        # Resumen general
        st.markdown("---")
        st.markdown("### 📈 Resumen General")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_empresas_hoy = len(empresas_hoy)
            st.metric("Empresas HOY", total_empresas_hoy)
            
        with col2:
            total_empresas_ayer = len(empresas_ayer)
            st.metric("Empresas AYER", total_empresas_ayer)
            
        with col3:
            total_tonelaje_hoy = filtered_df_hoy[col_tonelaje].sum()
            total_tonelaje_ayer = filtered_df_ayer[col_tonelaje].sum() if not filtered_df_ayer.empty else 0
            diferencia_total = total_tonelaje_hoy - total_tonelaje_ayer
            st.metric(
                "Tonelaje Total HOY", 
                f"{total_tonelaje_hoy:,.0f}",
                delta=f"{diferencia_total:+,.0f}"
            )

    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
        st.info("Asegúrate de que el archivo sea un Excel válido (.xlsx o .xls) y que las columnas tengan los nombres correctos.")

else:
    st.info("👆 Carga un archivo Excel desde la barra lateral para comenzar")
    st.markdown("### 📋 Formato de datos esperado")
    example_data = {
        'FECHA': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'PRODUCTO': ['SLIT', 'CONCENTRADO', 'SLIT'],
        'DESTINO': ['Puerto A', 'Puerto B', 'Puerto C'],
        'TONELAJE': [100, 150, 120],
        'EMPRESA DE TRANSPORTE': ['M&Q SPA', 'M & Q', 'JORQUERA TRANSPORTE S. A.'],
        'TIEMPO OPERACIONAL': [138, 120, 90]
    }
    st.dataframe(pd.DataFrame(example_data))
'''

# Guardar el código en un archivo
with open('app_ejecutivo_completo.py', 'w', encoding='utf-8') as f:
    f.write(codigo_completo_ejecutivo)

print("Código ejecutivo completo generado y guardado como 'app_ejecutivo_completo.py'")
print("\nCaracterísticas incluidas:")
print("✅ Análisis ejecutivo automatizado")
print("✅ Informe específico de producto SLIT")
print("✅ Alertas automáticas por rendimiento")
print("✅ Ranking de empresas")
print("✅ Recomendaciones ejecutivas")
print("✅ Métricas comparativas")
print("✅ Gráficos de líneas comparativos")
print("✅ Formato listo para presentar a gerencia")
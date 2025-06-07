# 📊 Generador de Gráficos desde Excel

Una aplicación web interactiva para cargar archivos Excel y crear gráficos dinámicos.

## 🚀 Características

- **Carga de archivos Excel** (.xlsx, .xls)
- **Múltiples tipos de gráficos**:
  - Gráficos de barras y líneas
  - Gráficos circulares (pie)
  - Gráficos de dispersión
  - Histogramas
  - Mapas de calor (correlaciones)
- **Interfaz intuitiva** con tabs organizados
- **Estadísticas descriptivas** automáticas
- **Gráficos interactivos** con Plotly

## 📦 Instalación

1. Instala las dependencias:
```bash
pip install -r requirements.txt
```

2. Ejecuta la aplicación:
```bash
streamlit run app_graficos_excel.py
```

3. Abre tu navegador en `http://localhost:8501`

## 📋 Uso

1. **Carga tu archivo Excel** usando la barra lateral
2. **Explora tus datos** en la vista previa
3. **Selecciona el tipo de gráfico** que deseas crear
4. **Configura las columnas** para los ejes X, Y y opciones adicionales
5. **Genera el gráfico** y visualízalo de forma interactiva

## 📊 Tipos de gráficos disponibles

- **Barras/Líneas**: Perfectos para comparar valores entre categorías
- **Circular**: Ideal para mostrar proporciones
- **Dispersión**: Excelente para analizar relaciones entre variables
- **Histograma**: Útil para ver distribuciones de datos
- **Mapa de calor**: Visualiza correlaciones entre variables numéricas

## 🎯 Consejos

- Asegúrate de que tu Excel tenga encabezados en la primera fila
- Los datos numéricos se detectan automáticamente para gráficos apropiados
- Puedes colorear gráficos por diferentes categorías
- Los gráficos son interactivos: puedes hacer zoom, filtrar, etc.

¡Disfruta creando visualizaciones increíbles! 🎨

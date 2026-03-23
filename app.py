import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Monitor de Clima - OpenMeteo", layout="wide")

st.title("📊 Panel de Control Meteorológico")

# Función para cargar datos saltando las filas de encabezado de OpenMeteo
@st.cache_data
def cargar_datos():
    # Saltamos 3 filas que son los metadatos de Open-Meteo
    archivo = 'open-meteo-26.89S56.87W167m (1).csv'
    df = pd.read_csv(archivo, skiprows=3)
    
    # Limpieza de nombres de columnas (quitar espacios)
    df.columns = [c.strip() for c in df.columns]
    
    # Convertir la columna de tiempo (usualmente se llama 'time')
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'])
    
    return df

try:
    df = cargar_datos()
    
    # Mostrar tabla resumida
    with st.expander("Ver tabla de datos completa"):
        st.write(df)

    # Configuración del gráfico
    st.subheader("📈 Evolución por Hora")
    
    # Listamos las columnas que NO son el tiempo para elegir qué graficar
    variables = [c for c in df.columns if c != 'time']
    opcion = st.selectbox("Selecciona la variable a observar:", variables)

    # Crear el gráfico automático
    fig = px.line(df, x='time', y=opcion, 
                 title=f"Histórico de {opcion}",
                 labels={'time': 'Fecha y Hora', opcion: opcion},
                 markers=True)
    
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error al procesar el archivo: {e}")
    st.info("Asegúrate de que el archivo CSV esté en la misma carpeta que este script.")

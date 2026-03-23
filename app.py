import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image

# 1. Configuración de la página
st.set_page_config(page_title="FCA UNA - Filial Santa Rosa", layout="wide", page_icon="🌱")

# 2. Encabezado con Logo y Título Institucional
try:
    # Asegúrate de que el archivo se llame exactamente así en GitHub
    logo = Image.open('logoproyecto.png')
    
    col1, col2 = st.columns([1, 6])
    with col1:
        # --- AUMENTO DE TAMAÑO DEL LOGO ---
        # Cambié width=120 por width=250 para que sea más grande.
        st.image(logo, width=250)
    with col2:
        st.title("Datos de la Facultad de Ciencias Agrarias UNA")
        st.subheader("Filial Santa Rosa - Monitoreo Meteorológico")

except Exception:
    st.title("FCA UNA - Filial Santa Rosa")
    st.subheader("Datos de la Facultad de Ciencias Agrarias")

st.divider()

# 3. Función para procesar los datos
@st.cache_data
def cargar_datos(archivo):
    # Saltamos las líneas de encabezado de Open-Meteo
    df = pd.read_csv(archivo, skiprows=3)
    df.columns = [c.strip() for c in df.columns]
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'])
    return df

# 4. Lógica de Carga de Archivos
nombre_archivo_base = 'open-meteo-26.89S56.87W167m (1).csv'
archivo_manual = st.sidebar.file_uploader("Actualizar datos (Subir nuevo CSV)", type=["csv"])

try:
    if archivo_manual is not None:
        df = cargar_datos(archivo_manual)
    else:
        df = cargar_datos(nombre_archivo_base)

    # 5. Panel de Métricas (Últimos datos registrados)
    st.markdown("### 📍 Estado Actual en Santa Rosa")
    m1, m2, m3 = st.columns(3)
    
    # Extraemos los últimos valores del archivo
    temp_actual = df.iloc[-1, 2]
    hum_actual = df.iloc[-1, 3]
    hora_actual = df['time'].iloc[-1].strftime('%H:%M')

    m1.metric("Temperatura", f"{temp_actual} °C")
    m2.metric("Humedad Relativa", f"{hum_actual} %")
    m3.metric("Hora de Lectura", hora_actual)

    # 6. Gráfico de Evolución Horaria
    st.subheader("📈 Análisis de Variables Agrometeorológicas")
    variables = [c for c in df.columns if c != 'time']
    seleccion = st.selectbox("Seleccione la variable para visualizar:", variables)
    
    # Gráfico con color verde (representativo de Agronomía)
    fig = px.line(df, x='time', y=seleccion, markers=True, template="plotly_white")
    fig.update_traces(line_color='#2E7D32') 
    fig.update_layout(xaxis_title="Tiempo (Horas)", yaxis_title=seleccion)
    st.plotly_chart(fig, use_container_width=True)

    # 7. Tabla de datos
    with st.expander("Ver tabla de registros horarios"):
        st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Error al cargar los datos: {e}")
    st.info("Verifica que el archivo CSV y el Logo estén en tu repositorio de GitHub.")

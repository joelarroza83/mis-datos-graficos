import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image

# 1. Configuración de la página
st.set_page_config(page_title="FCA UNA - Filial Santa Rosa", layout="wide", page_icon="🌱")

# 2. Encabezado: LOGO GRANDE Y CENTRADO
try:
    logo = Image.open('logoproyecto.png')
    
    # Creamos 3 columnas para centrar la del medio
    col_izq, col_centro, col_der = st.columns([1, 2, 1])
    
    with col_centro:
        # Tamaño grande: 400 píxeles
        st.image(logo, width=400, use_container_width=False)
    
    # Títulos centrados con estilo HTML
    st.markdown("<h1 style='text-align: center; color: #1B5E20;'>Datos de la Facultad de Ciencias Agrarias UNA</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #4E342E;'>Filial Santa Rosa - Monitoreo Meteorológico</h3>", unsafe_allow_html=True)

except Exception as e:
    st.title("FCA UNA - Filial Santa Rosa")
    st.subheader("Monitoreo Meteorológico")

st.divider()

# 3. SECCIÓN DE SEGURIDAD EN LA BARRA LATERAL
st.sidebar.header("🔐 Panel de Control")
# CAMBIA TU CONTRASEÑA AQUÍ
clave_acceso = "FCA2026" 
user_password = st.sidebar.text_input("Contraseña de Administrador", type="password")

archivo_manual = None
if user_password == clave_acceso:
    st.sidebar.success("Acceso Autorizado")
    archivo_manual = st.sidebar.file_uploader("📤 Subir nuevo CSV de Open-Meteo", type=["csv"])
elif user_password != "":
    st.sidebar.error("Contraseña Incorrecta")

st.sidebar.info("Nota: Solo el administrador puede cargar nuevos datos. Los usuarios generales solo pueden visualizar.")

# 4. FUNCIÓN PARA PROCESAR LOS DATOS
@st.cache_data
def cargar_datos(archivo):
    try:
        # Saltamos las 3 líneas de metadatos de Open-Meteo
        df = pd.read_csv(archivo, skiprows=3)
        # Limpiamos nombres de columnas
        df.columns = [c.strip() for c in df.columns]
        # Convertimos la columna de tiempo
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'])
        return df
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
        return None

# 5. LÓGICA DE CARGA (Archivo base de GitHub o subida manual)
nombre_archivo_base = 'open-meteo-26.89S56.87W167m (1).csv'

try:
    if archivo_manual is not None:
        df = cargar_datos(archivo_manual)
    else:
        df = cargar_datos(nombre_archivo_base)

    if df is not None:
        # 6. PANEL DE MÉTRICAS (Estado Actual)
        st.markdown("### 📍 Estado Actual en Santa Rosa")
        m1, m2, m3 = st.columns(3)
        
        # Obtenemos los últimos valores registrados
        temp_actual = df.iloc[-1, 2]
        hum_actual = df.iloc[-1, 3]
        hora_actual = df['time'].iloc[-1].strftime('%H:%M hs (%d/%m)')

        m1.metric("Temperatura", f"{temp_actual} °C")
        m2.metric("Humedad Relativa", f"{hum_actual} %")
        m3.metric("Última Lectura", hora_actual)

        # 7. GRÁFICO INTERACTIVO
        st.subheader("📈 Análisis de Variables Agrometeorológicas")
        
        # Filtramos columnas que no son el tiempo para el selector
        variables = [c for c in df.columns if c != 'time']
        seleccion = st.selectbox("Seleccione la variable para visualizar:", variables)
        
        # Gráfico con color verde institucional de Agronomía
        fig = px.line(df, x='time', y=seleccion, markers=True, template="plotly_white")
        fig.update_traces(line_color='#2E7D32', line_width=2) 
        fig.update_layout(
            xaxis_title="Fecha y Hora",
            yaxis_title=seleccion,
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

        # 8. TABLA DE DATOS PARA ESTUDIANTES
        with st.expander("📂 Ver tabla de registros históricos"):
            st.dataframe(df, use_container_width=True)
            
            # Botón opcional para descargar los datos que se están viendo
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Descargar datos en CSV",
                data=csv_data,
                file_name='datos_fca_santa_rosa.csv',
                mime='text/csv',
            )

except Exception as e:
    st.warning("Configurando el sistema... Asegúrate de que los archivos estén en GitHub.")
    st.info("Si eres el administrador, ingresa la clave en el panel izquierdo para cargar datos.")

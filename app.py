import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image

# 1. Configuración de la página
st.set_page_config(page_title="FCA UNA - Filial Santa Rosa", layout="wide", page_icon="🌱")

# 2. Encabezado: LOGO SUPER AMPLIADO Y CENTRADO
try:
    logo = Image.open('logoproyecto.png')
    
    # Usamos columnas para centrar, pero damos más espacio a la del medio
    col_izq, col_centro, col_der = st.columns([0.5, 3, 0.5])
    
    with col_centro:
        # Aumentado a 600 píxeles para una visualización mucho más amplia
        st.image(logo, width=600, use_container_width=False)
    
    # Títulos con estilo HTML para que resalten
    st.markdown("<h1 style='text-align: center; color: #1B5E20; font-size: 45px;'>Datos de la Facultad de Ciencias Agrarias UNA</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #4E342E;'>Filial Santa Rosa - Monitoreo Meteorológico</h2>", unsafe_allow_html=True)

except Exception as e:
    st.title("FCA UNA - Filial Santa Rosa")
    st.subheader("Monitoreo Meteorológico")

st.divider()

# 3. SECCIÓN DE SEGURIDAD EN LA BARRA LATERAL
st.sidebar.header("🔐 Panel de Control")
clave_acceso = "FCA2026" 
user_password = st.sidebar.text_input("Contraseña de Administrador", type="password")

archivo_manual = None
if user_password == clave_acceso:
    st.sidebar.success("Acceso Autorizado")
    archivo_manual = st.sidebar.file_uploader("📤 Subir nuevo CSV de Open-Meteo", type=["csv"])
elif user_password != "":
    st.sidebar.error("Contraseña Incorrecta")

# 4. FUNCIÓN PARA PROCESAR LOS DATOS
@st.cache_data
def cargar_datos(archivo):
    try:
        df = pd.read_csv(archivo, skiprows=3)
        df.columns = [c.strip() for c in df.columns]
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'])
        return df
    except Exception as e:
        return None

# 5. LÓGICA DE CARGA
nombre_archivo_base = 'open-meteo-26.89S56.87W167m (1).csv'

try:
    if archivo_manual is not None:
        df = cargar_datos(archivo_manual)
    else:
        df = cargar_datos(nombre_archivo_base)

    if df is not None:
        # 6. PANEL DE MÉTRICAS
        st.markdown("### 📍 Estado Actual en Santa Rosa")
        m1, m2, m3 = st.columns(3)
        
        temp_actual = df.iloc[-1, 2]
        hum_actual = df.iloc[-1, 3]
        hora_actual = df['time'].iloc[-1].strftime('%H:%M hs (%d/%m)')

        m1.metric("Temperatura", f"{temp_actual} °C")
        m2.metric("Humedad Relativa", f"{hum_actual} %")
        m3.metric("Última Lectura", hora_actual)

        # 7. GRÁFICO INTERACTIVO
        st.subheader("📈 Análisis de Variables Agrometeorológicas")
        variables = [c for c in df.columns if c != 'time']
        seleccion = st.selectbox("Seleccione la variable para visualizar:", variables)
        
        fig = px.line(df, x='time', y=seleccion, markers=True, template="plotly_white")
        fig.update_traces(line_color='#2E7D32', line_width=3) 
        st.plotly_chart(fig, use_container_width=True)

        # 8. TABLA DE DATOS
        with st.expander("📂 Ver tabla de registros históricos"):
            st.dataframe(df, use_container_width=True)
            
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Descargar datos en CSV",
                data=csv_data,
                file_name='datos_fca_santa_rosa.csv',
                mime='text/csv',
            )

except Exception as e:
    st.warning("Configurando el sistema...")

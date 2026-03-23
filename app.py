import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime

# 1. Configuración de la página
st.set_page_config(page_title="FCA UNA - Filial Santa Rosa", layout="wide", page_icon="🌱")

# 2. Encabezado con Logo Grande
try:
    logo = Image.open('logoproyecto.png')
    col_izq, col_centro, col_der = st.columns([0.5, 3, 0.5])
    with col_centro:
        st.image(logo, width=500)
    st.markdown("<h1 style='text-align: center; color: #1B5E20;'>Datos de la Facultad de Ciencias Agrarias UNA</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #4E342E;'>Filial Santa Rosa - Monitoreo Meteorológico</h3>", unsafe_allow_html=True)
except Exception:
    st.title("FCA UNA - Filial Santa Rosa")

st.divider()

# 3. SEGURIDAD Y FILTROS EN LA BARRA LATERAL
st.sidebar.header("🔐 Panel de Control")
clave_acceso = "FCA2026" 
user_password = st.sidebar.text_input("Contraseña de Administrador", type="password")

# 4. FUNCIÓN PARA PROCESAR LOS DATOS
@st.cache_data
def cargar_datos(archivo):
    try:
        df = pd.read_csv(archivo, skiprows=3)
        df.columns = [c.strip() for c in df.columns]
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'])
        return df
    except Exception:
        return None

# Carga inicial de datos
nombre_archivo_base = 'open-meteo-26.89S56.87W167m (1).csv'
df = cargar_datos(nombre_archivo_base)

if df is not None:
    # --- NUEVA FUNCIÓN: FILTRO POR FECHAS ---
    st.sidebar.header("📅 Filtrar por Fecha")
    fecha_min = df['time'].min().date()
    fecha_max = df['time'].max().date()
    
    rango_fechas = st.sidebar.date_input(
        "Selecciona el periodo:",
        value=(fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max
    )

    # Aplicar el filtro si se seleccionan ambas fechas
    if len(rango_fechas) == 2:
        inicio, fin = rango_fechas
        mask = (df['time'].date >= inicio) & (df['time'].date <= fin)
        df_filtrado = df.loc[mask]
    else:
        df_filtrado = df

    # --- ÁREA RESTRINGIDA: CARGA Y DESCARGA ---
    if user_password == clave_acceso:
        st.sidebar.success("Acceso Autorizado")
        
        # Opción de Carga
        archivo_manual = st.sidebar.file_uploader("📤 Subir nuevo CSV", type=["csv"])
        if archivo_manual:
            df_filtrado = cargar_datos(archivo_manual)
            
        # Opción de Descarga en TXT (Protegida)
        st.sidebar.markdown("---")
        st.sidebar.write("📥 **Descargar datos filtrados:**")
        
        # Generar formato TXT
        txt_data = df_filtrado.to_csv(index=False, sep='\t').encode('utf-8')
        st.sidebar.download_button(
            label="Descargar en formato .TXT",
            data=txt_data,
            file_name=f'datos_fca_{datetime.now().strftime("%d_%m_%Y")}.txt',
            mime='text/plain',
        )
    elif user_password != "santarosa2026":
        st.sidebar.error("Contraseña Incorrecta")

    # 5. VISUALIZACIÓN DE DATOS (Métricas y Gráficos)
    m1, m2, m3 = st.columns(3)
    temp_actual = df_filtrado.iloc[-1, 2]
    hum_actual = df_filtrado.iloc[-1, 3]
    hora_actual = df_filtrado['time'].iloc[-1].strftime('%H:%M hs (%d/%m)')

    m1.metric("Temperatura", f"{temp_actual} °C")
    m2.metric("Humedad", f"{hum_actual} %")
    m3.metric("Última Lectura", hora_actual)

    st.subheader("📈 Análisis de Variables")
    variables = [c for c in df_filtrado.columns if c != 'time']
    seleccion = st.selectbox("Variable:", variables)
    
    fig = px.line(df_filtrado, x='time', y=seleccion, markers=True, template="plotly_white")
    fig.update_traces(line_color='#2E7D32') 
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📂 Ver registros históricos"):
        st.dataframe(df_filtrado, use_container_width=True)
else:
    st.error("No se pudieron cargar los datos.")

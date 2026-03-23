import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime

# 1. Configuración de la página
st.set_page_config(page_title="FCA UNA - Filial Santa Rosa", layout="wide", page_icon="🌱")

# 2. Encabezado: Logo Ampliado y Títulos Centrados
try:
    logo = Image.open('logoproyecto.png')
    col_izq, col_centro, col_der = st.columns([0.5, 3, 0.5])
    with col_centro:
        st.image(logo, width=550, use_container_width=False)
    
    st.markdown("<h1 style='text-align: center; color: #1B5E20; margin-bottom: 0;'>Datos de la Facultad de Ciencias Agrarias UNA</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #4E342E; margin-top: 0;'>Filial Santa Rosa - Monitoreo Meteorológico</h3>", unsafe_allow_html=True)
except Exception:
    st.title("FCA UNA - Filial Santa Rosa")

st.divider()

# 3. Función para procesar los datos
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

# Carga del archivo base
nombre_archivo_base = 'open-meteo-26.89S56.87W167m (1).csv'
df = cargar_datos(nombre_archivo_base)

if df is not None:
    # --- BARRA LATERAL: SEGURIDAD Y FILTROS ---
    st.sidebar.header("🔐 Panel de Administración")
    clave_acceso = "FCA2026" 
    user_password = st.sidebar.text_input("Contraseña", type="password")

    # Filtro de Fechas (Visible para todos)
    st.sidebar.divider()
    st.sidebar.header("📅 Rango de Fechas")
    fecha_min = df['time'].min().date()
    fecha_max = df['time'].max().date()
    
    rango = st.sidebar.date_input(
        "Seleccionar periodo:",
        value=(fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max
    )

    # Lógica de filtrado
    if isinstance(rango, tuple) and len(rango) == 2:
        inicio, fin = rango
        df_mostrar = df[(df['time'].dt.date >= inicio) & (df['time'].dt.date <= fin)]
    else:
        df_mostrar = df

    # Área Protegida (Carga y Descarga TXT)
    if user_password == clave_acceso:
        st.sidebar.success("Acceso de Administrador")
        
        # Subir nuevo archivo
        nuevo_archivo = st.sidebar.file_uploader("Actualizar CSV", type=["csv"])
        if nuevo_archivo:
            df_mostrar = cargar_datos(nuevo_archivo)

        # Descarga en TXT
        st.sidebar.write("📥 **Exportar Datos:**")
        # Generamos el formato de texto plano (separado por tabulaciones)
        txt_output = df_mostrar.to_csv(index=False, sep='\t').encode('utf-8')
        st.sidebar.download_button(
            label="Descargar en formato .TXT",
            data=txt_output,
            file_name=f'fca_santa_rosa_{datetime.now().strftime("%d_%m_%Y")}.txt',
            mime='text/plain',
        )
    elif user_password != "":
        st.sidebar.error("Clave incorrecta")

    # 4. VISUALIZACIÓN
    # Métricas principales
    m1, m2, m3 = st.columns(3)
    # Mostramos el último dato del rango seleccionado
    t_act = df_mostrar.iloc[-1, 2]
    h_act = df_mostrar.iloc[-1, 3]
    f_act = df_mostrar['time'].iloc[-1].strftime('%H:%M hs - %d/%m')

    m1.metric("Temperatura", f"{t_act} °C")
    m2.metric("Humedad", f"{h_act} %")
    m3.metric("Fecha/Hora Datos", f_act)

    # Gráfico
    st.subheader("📈 Evolución de Variables")
    vars_disponibles = [c for c in df_mostrar.columns if c != 'time']
    sel = st.selectbox("Elija qué visualizar:", vars_disponibles)
    
    fig = px.line(df_mostrar, x='time', y=sel, markers=True, template="plotly_white")
    fig.update_traces(line_color='#2E7D32', line_width=3)
    st.plotly_chart(fig, use_container_width=True)

    # Tabla histórica
    with st.expander("📂 Ver registros detallados"):
        st.dataframe(df_mostrar, use_container_width=True)

else:
    st.error("Error: No se encontró el archivo de datos en el repositorio.")

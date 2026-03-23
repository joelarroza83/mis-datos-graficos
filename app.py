import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime, timedelta

# 1. Configuración de la página
st.set_page_config(page_title="FCA UNA - Filial Santa Rosa", layout="wide", page_icon="🌱")

# 2. Encabezado
try:
    logo = Image.open('logoproyecto.png')
    col_izq, col_centro, col_der = st.columns([0.5, 3, 0.5])
    with col_centro:
        st.image(logo, width=500)
    st.markdown("<h1 style='text-align: center; color: #1B5E20;'>Datos de la Facultad de Ciencias Agrarias UNA</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #4E342E;'>Filial Santa Rosa - Monitoreo Meteorológico</h3>", unsafe_allow_html=True)
except:
    st.title("FCA UNA - Filial Santa Rosa")

st.divider()

# 3. Función de carga con "LIMPIEZA EXTREMA"
@st.cache_data
def cargar_datos(archivo):
    try:
        # Cargamos saltando las líneas de Open-Meteo
        df = pd.read_csv(archivo, skiprows=3)
        # Limpiamos nombres de columnas (quita espacios invisibles)
        df.columns = df.columns.str.strip()
        
        if 'time' in df.columns:
            # Forzamos la conversión de fecha (día-mes-año hora:minuto)
            df['time'] = pd.to_datetime(df['time'], dayfirst=True, errors='coerce')
            
            # ELIMINAMOS DATOS ERRÓNEOS DEL FUTURO (Cualquier cosa después de hoy)
            fecha_limite = datetime.now() + timedelta(hours=1)
            df = df[df['time'] <= fecha_limite]
            
            # Quitamos filas que no tengan fecha válida y ordenamos
            df = df.dropna(subset=['time'])
            df = df.sort_values(by='time').reset_index(drop=True)
            
        return df
    except Exception as e:
        st.error(f"Error técnico: {e}")
        return None

# Carga del archivo
nombre_archivo_base = 'datos_clima.csv'
df_base = cargar_datos(nombre_archivo_base)

if df_base is not None and not df_base.empty:
    # --- PANEL LATERAL ---
    st.sidebar.header("🔐 Administración")
    admin_pass = st.sidebar.text_input("Acceso Administrador", type="password", key="admin")
    if admin_pass == "FCA2026":
        nuevo = st.sidebar.file_uploader("Actualizar datos_clima.csv", type=["csv"])
        if nuevo:
            df_base = cargar_datos(nuevo)

    st.sidebar.divider()
    
    # RANGO DETECTADO REAL
    min_f = df_base['time'].min()
    max_f = df_base['time'].max()
    
    st.sidebar.header("📅 Rango de Datos Disponible")
    st.sidebar.success(f"Desde: {min_f.strftime('%d/%m/%Y')}")
    st.sidebar.success(f"Hasta: {max_f.strftime('%d/%m/%Y')}")

    # Selector de Rango (Inicia mostrando los últimos 7 días)
    rango = st.sidebar.date_input(
        "Filtrar periodo:",
        value=(max_f.date() - timedelta(days=7), max_f.date()),
        min_value=min_f.date(),
        max_value=max_f.date()
    )

    # 4. FILTRADO
    if isinstance(rango, tuple) and len(rango) == 2:
        inicio, fin = rango
        df_final = df_base[(df_base['time'].dt.date >= inicio) & (df_base['time'].dt.date <= fin)]
    else:
        df_final = df_base.tail(168) # Backup por si el usuario solo hace un clic

    # 5. VISUALIZACIÓN
    if not df_final.empty:
        # Métricas
        m1, m2, m3 = st.columns(3)
        m1.metric("Temperatura", f"{df_final.iloc[-1, 2]} °C")
        m2.metric("Humedad", f"{df_final.iloc[-1, 3]} %")
        m3.metric("Último Registro", df_final['time'].iloc[-1].strftime('%d/%m/%Y %H:%M'))

        # Gráfico
        st.subheader(f"📈 Gráfico Agrometeorológico ({inicio} al {fin})")
        vars_disp = [c for c in df_final.columns if c != 'time']
        seleccion = st.selectbox("Parámetro:", vars_disp)
        
        fig = px.line(df_final, x='time', y=seleccion, markers=True, template="plotly_white")
        fig.update_traces(line_color='#2E7D32', line_width=2)
        st.plotly_chart(fig, use_container_width=True)

        # 6. DESCARGA TXT CON CONTRASEÑA
        st.divider()
        col_p, col_b = st.columns([1, 1])
        with col_p:
            c_desc = st.text_input("Clave para descargar este rango (.txt)", type="password", key="desc")
        with col_b:
            if c_desc == "santarosa2026":
                txt = df_final.to_csv(index=False, sep='\t').encode('utf-8')
                st.write("---")
                st.download_button(
                    label=f"💾 Descargar {len(df_final)} registros",
                    data=txt,
                    file_name=f"FCA_SR_{inicio}_al_{fin}.txt",
                    mime="text/plain"
                )
    else:
        st.warning("No hay datos para el rango seleccionado.")
else:
    st.error("Error: 'datos_clima.csv' no encontrado o vacío.")

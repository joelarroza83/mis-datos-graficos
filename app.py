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
except Exception:
    st.title("FCA UNA - Filial Santa Rosa")

st.divider()

# 3. Función de carga con "LIMPIEZA PROFUNDA"
@st.cache_data
def cargar_datos(archivo):
    try:
        # Cargamos saltando las líneas de Open-Meteo
        df = pd.read_csv(archivo, skiprows=3)
        df.columns = [c.strip() for c in df.columns]
        
        if 'time' in df.columns:
            # Intentamos convertir forzando el formato de día primero (típico de Paraguay)
            df['time'] = pd.to_datetime(df['time'], dayfirst=True, errors='coerce')
            
            # ELIMINAMOS DATOS DEL FUTURO (Si marca diciembre 2026 y hoy es marzo, es un error de lectura)
            hoy_limite = datetime.now() + timedelta(days=1)
            df = df[df['time'] <= hoy_limite]
            
            # Quitamos filas vacías y ordenamos del más antiguo al más nuevo
            df = df.dropna(subset=['time'])
            df = df.sort_values(by='time').reset_index(drop=True)
            
        return df
    except Exception as e:
        st.error(f"Error técnico en el archivo: {e}")
        return None

# Carga del archivo
nombre_archivo_base = 'datos_clima.csv'
df_base = cargar_datos(nombre_archivo_base)

if df_base is not None and not df_base.empty:
    # --- PANEL LATERAL ---
    st.sidebar.header("🔐 Administración")
    admin_pass = st.sidebar.text_input("Acceso Administrador", type="password", key="admin")
    if admin_pass == "FCA2026":
        nuevo_archivo = st.sidebar.file_uploader("Actualizar datos_clima.csv", type=["csv"])
        if nuevo_archivo:
            df_base = cargar_datos(nuevo_archivo)

    st.sidebar.divider()
    
    # VERIFICACIÓN TÉCNICA EN PANTALLA
    min_f = df_base['time'].min()
    max_f = df_base['time'].max()
    
    st.sidebar.header("📅 Rango Detectado")
    st.sidebar.write(f"Primer dato: **{min_f.strftime('%d/%m/%Y')}**")
    st.sidebar.write(f"Último dato: **{max_f.strftime('%d/%m/%Y')}**")

    # Selector de rango (Por defecto muestra los últimos 7 días de los datos existentes)
    try:
        rango = st.sidebar.date_input(
            "Selecciona el periodo:",
            value=(max_f.date() - timedelta(days=7), max_f.date()),
            min_value=min_f.date(),
            max_value=max_f.date()
        )
    except Exception:
        # Si falla el rango por defecto, muestra todo
        rango = (min_f.date(), max_f.date())

    # 4. FILTRADO
    if isinstance(rango, tuple) and len(rango) == 2:
        inicio, fin = rango
        df_final = df_base[(df_base['time'].dt.date >= inicio) & (df_base['time'].dt.date <= fin)]
    else:
        df_final = df_base

    # 5. VISUALIZACIÓN
    if not df_final.empty:
        # Métricas
        m1, m2, m3 = st.columns(3)
        # Usamos .iloc[-1] para el dato más reciente del rango
        m1.metric("Temperatura", f"{df_final.iloc[-1, 2]} °C")
        m2.metric("Humedad", f"{df_final.iloc[-1, 3]} %")
        m3.metric("Fecha/Hora", df_final['time'].iloc[-1].strftime('%d/%m/%Y %H:%M'))

        # Gráfico
        st.subheader("📈 Visualización Agrometeorológica")
        vars_disp = [c for c in df_final.columns if c != 'time']
        seleccion = st.selectbox("Parámetro:", vars_disp)
        
        fig = px.line(df_final, x='time', y=seleccion, markers=True, template="plotly_white")
        fig.update_traces(line_color='#2E7D32', line_width=2)
        fig.update_layout(hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

        # 6. DESCARGA TXT CON CONTRASEÑA
        st.divider()
        st.write("🔒 **Descarga Protegida**")
        col_p, col_b = st.columns([1, 1])
        with col_p:
            c_desc = st.text_input("Contraseña de descarga", type="password", key="desc")
        with col_b:
            if c_desc == "santarosa2026":
                txt = df_final.to_csv(index=False, sep='\t').encode('utf-8')
                st.download_button(
                    label="💾 Descargar Rango Seleccionado (.txt)",
                    data=txt,
                    file_name=f"FCA_SR_{inicio}_al_{fin}.txt",
                    mime="text/plain"
                )
    else:
        st.warning("No hay datos para el rango seleccionado.")
else:
    st.error("No se pudo leer el archivo. Verifica que 'datos_clima.csv' tenga el formato correcto.")

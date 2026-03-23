import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime, timedelta

# 1. Configuración de la página
st.set_page_config(page_title="FCA UNA - Filial Santa Rosa", layout="wide", page_icon="🌱")

# 2. Encabezado con Logo
try:
    logo = Image.open('logoproyecto.png')
    col_izq, col_centro, col_der = st.columns([0.5, 3, 0.5])
    with col_centro:
        st.image(logo, width=550)
    st.markdown("<h1 style='text-align: center; color: #1B5E20;'>Datos de la Facultad de Ciencias Agrarias UNA</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #4E342E;'>Filial Santa Rosa - Monitoreo Meteorológico</h3>", unsafe_allow_html=True)
except Exception:
    st.title("FCA UNA - Filial Santa Rosa")

st.divider()

# 3. Función de carga de datos con DETECCIÓN DE FECHA CORREGIDA
@st.cache_data
def cargar_datos(archivo):
    try:
        df = pd.read_csv(archivo, skiprows=3)
        df.columns = [c.strip() for c in df.columns]
        
        if 'time' in df.columns:
            # Intentamos detectar el formato automáticamente (dayfirst ayuda con formatos latinos)
            df['time'] = pd.to_datetime(df['time'], dayfirst=True, errors='coerce')
            # Eliminamos filas donde la fecha no se pudo leer
            df = df.dropna(subset=['time'])
            # Ordenamos por fecha para que el gráfico no sea un caos
            df = df.sort_values(by='time')
        return df
    except Exception as e:
        st.error(f"Error al procesar fechas: {e}")
        return None

# Carga inicial
nombre_archivo_base = 'datos_clima.csv'
df_base = cargar_datos(nombre_archivo_base)

if df_base is not None and not df_base.empty:
    # --- PANEL LATERAL ---
    st.sidebar.header("🔐 Administración")
    admin_pass = st.sidebar.text_input("Acceso Administrador", type="password")
    if admin_pass == "FCA2026":
        nuevo_archivo = st.sidebar.file_uploader("Actualizar datos_clima.csv", type=["csv"])
        if nuevo_archivo:
            df_base = cargar_datos(nuevo_archivo)

    st.sidebar.divider()
    st.sidebar.header("📅 Rango de Fechas")
    
    # Detectamos el rango real de los datos leídos
    min_date = df_base['time'].min().date()
    max_date = df_base['time'].max().date()

    # Mostramos qué fechas detectó el sistema para que tú lo verifiques
    st.sidebar.write(f"Datos detectados desde: **{min_date}**")
    st.sidebar.write(f"Hasta: **{max_date}**")

    # Selector de rango
    rango = st.sidebar.date_input(
        "Selecciona el periodo a consultar:",
        value=(max_date - timedelta(days=7), max_date),
        min_value=min_date,
        max_value=max_date
    )

    # 4. FILTRADO Y VISUALIZACIÓN
    if isinstance(rango, tuple) and len(rango) == 2:
        inicio, fin = rango
        df_final = df_base[(df_base['time'].dt.date >= inicio) & (df_base['time'].dt.date <= fin)]
    else:
        df_final = df_base.tail(168) # Muestra la última semana si no hay selección

    if not df_final.empty:
        # Métricas
        m1, m2, m3 = st.columns(3)
        m1.metric("Temperatura", f"{df_final.iloc[-1, 2]} °C")
        m2.metric("Humedad", f"{df_final.iloc[-1, 3]} %")
        m3.metric("Fecha Lectura", df_final['time'].iloc[-1].strftime('%d/%m/%Y %H:%M'))

        # Gráfico
        st.subheader("📈 Comportamiento de la Variable")
        var = st.selectbox("Parámetro:", [c for c in df_final.columns if c != 'time'])
        
        # Gráfico con puntos para entender mejor cada lectura
        fig = px.line(df_final, x='time', y=var, markers=True, template="plotly_white", color_discrete_sequence=['#2E7D32'])
        fig.update_layout(xaxis_title="Tiempo", yaxis_title=var)
        st.plotly_chart(fig, use_container_width=True)

        # 5. DESCARGA TXT PROTEGIDA
        st.divider()
        pass_desc = st.text_input("Clave para descargar este periodo en .TXT", type="password")
        if pass_desc == "santarosa2026":
            txt = df_final.to_csv(index=False, sep='\t').encode('utf-8')
            st.download_button("💾 Descargar Rango Seleccionado", txt, f"FCA_{inicio}_{fin}.txt", "text/plain")
    else:
        st.warning("No hay datos para esas fechas.")

else:
    st.error("Error: El archivo no tiene datos válidos o no se encuentra.")

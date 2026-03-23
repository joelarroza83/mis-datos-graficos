import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime, timedelta

# 1. Configuración de la página
st.set_page_config(page_title="FCA UNA - Filial Santa Rosa", layout="wide", page_icon="🌱")

# 2. Encabezado: Logo y Títulos
try:
    logo = Image.open('logoproyecto.png')
    col_izq, col_centro, col_der = st.columns([0.5, 3, 0.5])
    with col_centro:
        st.image(logo, width=550)
    
    st.markdown("<h1 style='text-align: center; color: #1B5E20; margin-bottom: 0;'>Datos de la Facultad de Ciencias Agrarias UNA</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #4E342E; margin-top: 0;'>Filial Santa Rosa - Monitoreo Meteorológico</h3>", unsafe_allow_html=True)
except Exception:
    st.title("FCA UNA - Filial Santa Rosa")

st.divider()

# 3. Función de carga de datos
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

# Nombre de archivo amigable
nombre_archivo_base = 'datos_clima.csv'
df_base = cargar_datos(nombre_archivo_base)

if df_base is not None:
    # --- BARRA LATERAL ---
    st.sidebar.header("🔐 Panel Administrativo")
    admin_pass = st.sidebar.text_input("Acceso para subir datos", type="password")
    
    if admin_pass == "FCA2026":
        nuevo_archivo = st.sidebar.file_uploader("Actualizar base 'datos_clima.csv'", type=["csv"])
        if nuevo_archivo:
            df_base = cargar_datos(nuevo_archivo)

    st.sidebar.divider()
    st.sidebar.header("📅 Selector de Periodo")
    
    # CALCULAMOS EL RANGO REAL DE TUS DATOS (2025-2026)
    min_absoluta = df_base['time'].min().date()
    max_absoluta = df_base['time'].max().date()
    
    # Por defecto mostramos la última semana de datos disponibles
    inicio_defecto = max_absoluta - timedelta(days=7)

    # Widget de fecha mejorado para rangos largos
    rango = st.sidebar.date_input(
        "Selecciona el rango de fechas:",
        value=(inicio_defecto, max_absoluta),
        min_value=min_absoluta,
        max_value=max_absoluta,
        help="Haz clic en el año en el calendario para saltar rápidamente entre 2025 y 2026"
    )

    # Lógica de filtrado robusta
    if isinstance(rango, tuple) and len(rango) == 2:
        start_date, end_date = rango
        df_filtrado = df_base[(df_base['time'].dt.date >= start_date) & (df_base['time'].dt.date <= end_date)]
    else:
        # Caso mientras el usuario está seleccionando la segunda fecha
        df_filtrado = df_base[df_base['time'].dt.date >= inicio_defecto]
        start_date, end_date = inicio_defecto, max_absoluta

    # 4. VISUALIZACIÓN
    if not df_filtrado.empty:
        # Métricas (Basadas en el último registro del rango seleccionado)
        m1, m2, m3 = st.columns(3)
        t_act = df_filtrado.iloc[-1, 2]
        h_act = df_filtrado.iloc[-1, 3]
        f_act = df_filtrado['time'].iloc[-1].strftime('%H:%M hs - %d/%m/%Y')

        m1.metric("Temp. en Rango", f"{t_act} °C")
        m2.metric("Hum. en Rango", f"{h_act} %")
        m3.metric("Fecha del dato", f_act)

        st.subheader(f"📈 Gráfico del periodo: {start_date} al {end_date}")
        
        variables = [c for c in df_filtrado.columns if c != 'time']
        sel = st.selectbox("Parámetro a visualizar:", variables)
        
        fig = px.line(df_filtrado, x='time', y=sel, markers=True, template="plotly_white")
        fig.update_traces(line_color='#2E7D32', line_width=2)
        # Añadimos slider de tiempo en el mismo gráfico para navegar meses fácilmente
        fig.update_xaxes(rangeslider_visible=True)
        st.plotly_chart(fig, use_container_width=True)

        # 5. DESCARGA PROTEGIDA
        st.divider()
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            st.info(f"Se han encontrado {len(df_filtrado)} registros en este periodo.")
        with c2:
            clave_tx = st.text_input("Clave para exportar TXT", type="password")
        with c3:
            if clave_tx == "santarosa2026":
                txt_out = df_filtrado.to_csv(index=False, sep='\t').encode('utf-8')
                st.write("---")
                st.download_button(
                    label="💾 Descargar Rango (.txt)",
                    data=txt_out,
                    file_name=f'FCA_Reporte_{start_date}_a_{end_date}.txt',
                    mime='text/plain',
                )
    else:
        st.warning("No hay registros para las fechas seleccionadas.")
else:
    st.error("No se detectó el archivo 'datos_clima.csv' en GitHub.")

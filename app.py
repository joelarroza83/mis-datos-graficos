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

# 3. Función de carga con DETECCIÓN AUTOMÁTICA DE FORMATO
@st.cache_data
def cargar_datos(archivo):
    try:
        df = pd.read_csv(archivo, skiprows=3)
        df.columns = df.columns.str.strip()
        
        if 'time' in df.columns:
            # Intento 1: Formato con guiones (2026-03-20) como se ve en tu Excel
            df['time'] = pd.to_datetime(df['time'], errors='coerce')
            
            # Intento 2: Si hay nulos, probar formato día primero (20/03/2026)
            mask = df['time'].isna()
            if mask.any():
                df.loc[mask, 'time'] = pd.to_datetime(df.loc[mask, 'time'], dayfirst=True, errors='coerce')
            
            # Limpieza de seguridad
            df = df.dropna(subset=['time'])
            # Eliminamos fechas futuras erróneas (posteriores a mañana)
            limite = datetime.now() + timedelta(days=1)
            df = df[df['time'] <= limite]
            
            # ORDENAR de más viejo a más nuevo
            df = df.sort_values(by='time').reset_index(drop=True)
            
        return df
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
        return None

# Carga de la base de datos
nombre_archivo_base = 'datos_clima.csv'
df_base = cargar_datos(nombre_archivo_base)

if df_base is not None and not df_base.empty:
    # --- PANEL LATERAL ---
    st.sidebar.header("🔐 Administración")
    admin_pass = st.sidebar.text_input("Clave Admin", type="password")
    if admin_pass == "FCA2026":
        subida = st.sidebar.file_uploader("Actualizar datos_clima.csv", type=["csv"])
        if subida:
            df_base = cargar_datos(subida)

    st.sidebar.divider()
    
    # Rango Real detectado tras la corrección
    min_f = df_base['time'].min().date()
    max_f = df_base['time'].max().date()
    
    st.sidebar.header("📅 Periodo Detectado")
    st.sidebar.info(f"Desde: {min_f.strftime('%d/%m/%Y')}")
    st.sidebar.info(f"Hasta: {max_f.strftime('%d/%m/%Y')}")

    # Selector de Rango (Inicia en los últimos 7 días)
    rango = st.sidebar.date_input(
        "Filtrar fechas:",
        value=(max_f - timedelta(days=7), max_f),
        min_value=min_f,
        max_value=max_f
    )

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
        ultima = df_final.iloc[-1]
        m1.metric("Temperatura", f"{ultima.iloc[2]} °C")
        m2.metric("Humedad", f"{ultima.iloc[3]} %")
        m3.metric("Último Registro", ultima['time'].strftime('%d/%m/%Y %H:%M'))

        # Gráfico
        st.subheader(f"📈 Análisis Agrometeorológico")
        opciones = [c for c in df_final.columns if c != 'time']
        variable = st.selectbox("Parámetro:", opciones)
        
        fig = px.line(df_final, x='time', y=variable, markers=True, template="plotly_white")
        fig.update_traces(line_color='#2E7D32', line_width=2)
        st.plotly_chart(fig, use_container_width=True)

        # 6. DESCARGA TXT (santarosa2026)
        st.divider()
        st.write("🔒 **Descarga Protegida**")
        col_p, col_b = st.columns([1, 1])
        with col_p:
            c_desc = st.text_input("Contraseña de descarga", type="password")
        with col_b:
            if c_desc == "santarosa2026":
                txt = df_final.to_csv(index=False, sep='\t').encode('utf-8')
                st.download_button(
                    label=f"💾 Descargar {len(df_final)} registros (.txt)",
                    data=txt,
                    file_name=f"FCA_SR_Reporte_{inicio}_{fin}.txt",
                    mime="text/plain"
                )
    else:
        st.warning("No hay datos en ese periodo.")
else:
    st.error("Error: El sistema no detectó datos válidos. Revisa que el archivo en GitHub se llame 'datos_clima.csv' y tenga datos de 2025.")

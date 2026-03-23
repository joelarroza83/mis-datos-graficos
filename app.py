import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime, timedelta
import os

# 1. Configuración de página
st.set_page_config(page_title="FCA UNA - Santa Rosa", layout="wide", page_icon="🌱")

# 2. Encabezado
try:
    logo = Image.open('logoproyecto.png')
    st.image(logo, width=400)
    st.markdown("<h1 style='text-align: center; color: #1B5E20;'>Monitoreo Meteorológico FCA UNA</h1>", unsafe_allow_html=True)
except:
    st.title("FCA UNA - Filial Santa Rosa")

st.divider()

# 3. MOTOR DE CARGA ULTRA-ESPECÍFICO
@st.cache_data(ttl=300)
def cargar_clima_fca():
    archivos = ['datos_clima2025.csv', 'datos_clima2026.csv']
    dfs = []
    
    for nombre in archivos:
        if os.path.exists(nombre):
            try:
                # Leemos el archivo saltando el encabezado de Open-Meteo
                # 'errors' e 'ignore' ayudan a pasar el muro del 21 de marzo si hay caracteres raros
                df_t = pd.read_csv(nombre, skiprows=3, on_bad_lines='skip', engine='python')
                df_t.columns = [c.strip() for c in df_t.columns]
                
                # Nos quedamos solo con lo necesario: time, temp y humidity
                # Buscamos las columnas por palabras clave para evitar errores de nombre exacto
                col_time = [c for c in df_t.columns if 'time' in c.lower()][0]
                col_temp = [c for c in df_t.columns if 'temp' in c.lower()][0]
                col_hum = [c for c in df_t.columns if 'hum' in c.lower()][0]
                
                df_clean = df_t[[col_time, col_temp, col_hum]].copy()
                df_clean.columns = ['time', 'Temperatura (°C)', 'Humedad (%)']
                
                # Conversión de fecha
                df_clean['time'] = pd.to_datetime(df_clean['time'], errors='coerce')
                dfs.append(df_clean)
                st.sidebar.success(f"✅ {nombre} conectado")
            except Exception as e:
                st.sidebar.error(f"❌ Problema en {nombre}: {e}")
    
    if not dfs: return None
    
    # Unir, limpiar nulos y ordenar
    df_full = pd.concat(dfs, ignore_index=True)
    df_full = df_full.dropna(subset=['time'])
    
    # Convertir datos a números
    df_full['Temperatura (°C)'] = pd.to_numeric(df_full['Temperatura (°C)'], errors='coerce')
    df_full['Humedad (%)'] = pd.to_numeric(df_full['Humedad (%)'], errors='coerce')
    
    return df_full.sort_values('time').drop_duplicates().reset_index(drop=True)

# Ejecución
df_base = cargar_clima_fca()

if df_base is not None and not df_base.empty:
    # --- INFO SIDEBAR ---
    f_min, f_max = df_base['time'].min(), df_base['time'].max()
    st.sidebar.divider()
    st.sidebar.metric("Última actualización", f"{f_max.strftime('%d/%m %H:%M')}")
    st.sidebar.write(f"Registros totales: {len(df_base):,}")

    # Selector de Rango
    rango = st.sidebar.date_input(
        "Periodo de visualización:",
        value=(f_max.date() - timedelta(days=3), f_max.date()),
        min_value=f_min.date(),
        max_value=f_max.date()
    )

    # 4. FILTRADO
    if isinstance(rango, tuple) and len(rango) == 2:
        df_plot = df_base[(df_base['time'].dt.date >= rango[0]) & (df_base['time'].dt.date <= rango[1])]
    else:
        df_plot = df_base

    if not df_plot.empty:
        # Selección de Variable
        var = st.radio("Seleccione variable:", ["Temperatura (°C)", "Humedad (%)"], horizontal=True)

        # Métricas principales
        c1, c2, c3 = st.columns(3)
        c1.metric("Máximo", f"{df_plot[var].max():.1f}")
        c2.metric("Mínimo", f"{df_plot[var].min():.1f}")
        c3.metric("Promedio", f"{df_plot[var].mean():.1f}")

        # Gráfico
        color = '#E64A19' if "Temp" in var else '#1976D2'
        fig = px.line(df_plot, x='time', y=var, markers=True, template="plotly_white")
        fig.update_traces(line_color=color, line_width=2)
        fig.update_xaxes(rangeslider_visible=True)
        st.plotly_chart(fig, use_container_width=True)

        # 5. DESCARGA
        st.divider()
        if st.sidebar.text_input("Clave de descarga", type="password") == "santarosa2026":
            csv = df_plot.to_csv(index=False, sep='\t').encode('utf-8')
            st.download_button("💾 Descargar datos seleccionados", csv, f"FCA_Clima_{rango[0]}.txt")
    else:
        st.warning("No hay datos para las fechas seleccionadas.")
else:
    st.error("No se pudo leer la información. Asegúrate de que los archivos se llamen 'datos_clima2025.csv' y 'datos_clima2026.csv'.")

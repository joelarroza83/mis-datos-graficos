import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime, timedelta
import os

# 1. Configuración
st.set_page_config(page_title="FCA UNA - Santa Rosa", layout="wide", page_icon="🌱")

# 2. Encabezado
try:
    logo = Image.open('logoproyecto.png')
    st.image(logo, width=500)
    st.markdown("<h1 style='text-align: center; color: #1B5E20;'>Monitoreo Meteorológico FCA UNA</h1>", unsafe_allow_html=True)
except:
    st.title("FCA UNA - Filial Santa Rosa")

st.divider()

# 3. EL NUEVO ENFOQUE: Lector de Flujo de Texto (Ignora bloqueos)
@st.cache_data
def carga_forzada_multianual():
    archivos = ['datos_clima2025.csv', 'datos_clima2026.csv']
    columnas_finales = ['time', 'temperature_2m (°C)', 'relative_humidity_2m (%)', 'dew_point_2m (°C)', 'apparent_temperature (°C)', 'precipitation (mm)', 'rain (mm)']
    datos_recuperados = []

    for nombre in archivos:
        if os.path.exists(nombre):
            try:
                with open(nombre, 'r', encoding='utf-8', errors='ignore') as f:
                    # Saltamos las primeras 4 líneas (Open-Meteo header + nombres de columnas originales)
                    lineas = f.readlines()[4:] 
                    
                    for i, linea in enumerate(lineas):
                        partes = linea.strip().split(',')
                        # Validamos que la línea tenga datos y no sea solo comas
                        if len(partes) >= 3 and partes[0] != "":
                            datos_recuperados.append(partes[:len(columnas_finales)])
                st.sidebar.success(f"✅ {nombre} procesado línea por línea.")
            except Exception as e:
                st.sidebar.error(f"❌ Error crítico en {nombre}: {e}")
    
    if not datos_recuperados:
        return None

    # Creamos el DataFrame desde la lista de líneas limpias
    df = pd.DataFrame(datos_recuperados, columns=columnas_finales)
    
    # Conversión Forzada de Tipos
    df['time'] = pd.to_datetime(df['time'], dayfirst=True, errors='coerce')
    for col in columnas_finales[1:]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Limpieza final: quitar nulos, ordenar y quitar duplicados
    df = df.dropna(subset=['time']).drop_duplicates().sort_values('time').reset_index(drop=True)
    
    # Filtro de seguridad (no ver datos del futuro lejano por error de fecha)
    df = df[df['time'] <= datetime.now() + timedelta(days=2)]
    
    return df

# Ejecución de la carga
df_base = carga_forzada_multianual()

if df_base is not None and not df_base.empty:
    # --- PANEL LATERAL DE DIAGNÓSTICO ---
    st.sidebar.divider()
    f_min, f_max = df_base['time'].min(), df_base['time'].max()
    
    st.sidebar.header("📊 Datos en Memoria")
    st.sidebar.info(f"📅 **Desde:** {f_min.strftime('%d/%m/%Y')}")
    st.sidebar.info(f"📅 **Hasta:** {f_max.strftime('%d/%m/%Y')}")
    st.sidebar.write(f"🔢 Registros totales: **{len(df_base)}**")

    # Selector de Rango
    rango = st.sidebar.date_input(
        "Filtrar fechas:",
        value=(f_max.date() - timedelta(days=7), f_max.date()),
        min_value=f_min.date(),
        max_value=f_max.date()
    )

    # 4. FILTRADO
    if isinstance(rango, tuple) and len(rango) == 2:
        df_plot = df_base[(df_base['time'].dt.date >= rango[0]) & (df_base['time'].dt.date <= rango[1])]
    else:
        df_plot = df_base

    # 5. GRÁFICO
    if not df_plot.empty:
        st.subheader(f"📈 Gráfico: {rango[0]} al {rango[1]}")
        var = st.selectbox("Parámetro:", [c for c in df_plot.columns if c != 'time'])
        
        fig = px.line(df_plot, x='time', y=var, markers=True, template="plotly_white", color_discrete_sequence=['#2E7D32'])
        fig.update_xaxes(rangeslider_visible=True)
        st.plotly_chart(fig, use_container_width=True)

        # 6. DESCARGA (santarosa2026)
        st.divider()
        pw = st.text_input("Clave de descarga", type="password")
        if pw == "santarosa2026":
            txt = df_plot.to_csv(index=False, sep='\t').encode('utf-8')
            st.download_button("💾 Descargar Selección (.txt)", txt, f"Datos_FCA_{rango[0]}.txt")
    else:
        st.warning("No hay datos para el rango seleccionado.")
else:
    st.error("No se detectaron archivos válidos en GitHub. Asegúrate de que se llamen 'datos_clima2025.csv' y 'datos_clima2026.csv'.")

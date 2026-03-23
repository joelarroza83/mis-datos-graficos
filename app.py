import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime, timedelta

# 1. Configuración de la página
st.set_page_config(page_title="FCA UNA - Santa Rosa", layout="wide", page_icon="🌱")

# 2. Encabezado
try:
    logo = Image.open('logoproyecto.png')
    st.image(logo, width=500)
except:
    st.title("FCA UNA - Filial Santa Rosa")

# 3. FUNCIÓN DE RECONSTRUCCIÓN TOTAL (Lector de Emergencia)
@st.cache_data
def cargar_datos_seguro(nombre_archivo):
    try:
        # Leemos el archivo completo como texto plano para evitar bloqueos de CSV
        with open(nombre_archivo, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
        
        # Saltamos las primeras 3 líneas de encabezado de Open-Meteo
        datos_utiles = lineas[3:]
        
        # Buscamos la cabecera (time, temp, etc.)
        header = datos_utiles[0].strip().split(',')
        header = [h.strip() for h in header]
        
        filas_limpias = []
        for i, linea in enumerate(datos_utiles[1:]):
            partes = linea.strip().split(',')
            # SOLO aceptamos filas que tengan el mismo número de columnas que la cabecera
            if len(partes) == len(header):
                filas_limpias.append(partes)
        
        # Creamos el DataFrame
        df = pd.DataFrame(filas_limpias, columns=header)
        
        # Convertimos columnas numéricas (Temperatura, Humedad, etc.)
        for col in df.columns:
            if col != 'time':
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Conversión de FECHA con máxima tolerancia
        df['time'] = pd.to_datetime(df['time'], errors='coerce')
        
        # LIMPIEZA FINAL
        df = df.dropna(subset=['time']) # Fuera errores
        df = df[df['time'] >= '2025-01-01'] # Solo desde 2025
        df = df[df['time'] <= datetime.now() + timedelta(days=1)] # No futuro
        
        return df.sort_values('time').reset_index(drop=True)
        
    except Exception as e:
        st.error(f"Error en reconstrucción: {e}")
        return None

# Carga
df_base = cargar_datos_seguro('datos_clima.csv')

if df_base is not None and not df_base.empty:
    # --- PANEL LATERAL ---
    st.sidebar.header("📊 Diagnóstico de Datos")
    
    # Esto nos dirá si realmente leyó el 2025
    total = len(df_base)
    inicio_real = df_base['time'].min()
    fin_real = df_base['time'].max()
    
    st.sidebar.info(f"Registros recuperados: {total}")
    st.sidebar.write(f"📅 **Desde:** {inicio_real.strftime('%d/%m/%Y')}")
    st.sidebar.write(f"📅 **Hasta:** {fin_real.strftime('%d/%m/%Y')}")

    # Selector de Rango
    rango = st.sidebar.date_input(
        "Periodo a visualizar:",
        value=(fin_real.date() - timedelta(days=7), fin_real.date()),
        min_value=inicio_real.date(),
        max_value=fin_real.date()
    )

    # 4. FILTRADO Y GRÁFICO
    if isinstance(rango, tuple) and len(rango) == 2:
        df_final = df_base[(df_base['time'].dt.date >= rango[0]) & (df_base['time'].dt.date <= rango[1])]
    else:
        df_final = df_base

    if not df_final.empty:
        st.subheader(f"📈 Análisis Agrometeorológico")
        var = st.selectbox("Parámetro:", [c for c in df_final.columns if c != 'time'])
        
        fig = px.line(df_final, x='time', y=var, markers=True, template="plotly_white")
        fig.update_traces(line_color='#2E7D32')
        st.plotly_chart(fig, use_container_width=True)
        
        # 5. DESCARGA (santarosa2026)
        st.divider()
        passw = st.text_input("Clave para descargar este rango (.txt)", type="password")
        if passw == "santarosa2026":
            txt = df_final.to_csv(index=False, sep='\t').encode('utf-8')
            st.download_button("💾 Descargar Selección", txt, f"FCA_SR_{rango[0]}.txt")
else:
    st.error("El archivo 'datos_clima.csv' está vacío o tiene un error de origen que impide leer el 2025.")

import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime, timedelta
import os

# 1. Configuración de la página
st.set_page_config(page_title="FCA UNA - Santa Rosa", layout="wide", page_icon="🌱")

# 2. Encabezado
try:
    logo = Image.open('logoproyecto.png')
    st.image(logo, width=450)
    st.markdown("<h1 style='text-align: center; color: #1B5E20;'>Monitoreo Meteorológico FCA UNA</h1>", unsafe_allow_html=True)
except:
    st.title("FCA UNA - Filial Santa Rosa")

st.divider()

# 3. FUNCIÓN DE RASTREO DE DATOS (No falla con filas corruptas)
@st.cache_data(ttl=300)
def carga_inteligente():
    archivos = ['datos_clima2025.csv', 'datos_clima2026.csv']
    todos_los_datos = []
    
    for nombre in archivos:
        if os.path.exists(nombre):
            try:
                # Leemos el archivo como texto puro para evitar bloqueos
                with open(nombre, 'r', encoding='utf-8', errors='ignore') as f:
                    lineas = f.readlines()
                
                # Buscamos en qué línea empieza la cabecera real
                inicio_datos = 0
                for i, linea in enumerate(lineas):
                    if 'time' in linea.lower():
                        inicio_datos = i
                        columnas = [c.strip() for c in linea.split(',')]
                        break
                
                # Extraemos las filas de datos
                for l in lineas[inicio_datos + 1:]:
                    partes = [p.strip() for p in l.split(',')]
                    if len(partes) >= len(columnas):
                        todos_los_datos.append(partes[:len(columnas)])
                
                st.sidebar.success(f"✅ {nombre} rastreado.")
            except Exception as e:
                st.sidebar.error(f"❌ Error en {nombre}: {e}")
    
    if not todos_los_datos: return None

    # Reconstrucción del DataFrame
    df = pd.DataFrame(todos_los_datos, columns=columnas)
    
    # Conversión flexible de fechas y números
    df['time'] = pd.to_datetime(df['time'], dayfirst=True, errors='coerce')
    for col in df.columns:
        if col != 'time':
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Limpieza: quitar vacíos, ordenar y eliminar duplicados de la unión
    df = df.dropna(subset=['time']).drop_duplicates().sort_values('time').reset_index(drop=True)
    
    # Asegurar rango correcto (desde 2025 hasta hoy)
    df = df[(df['time'].dt.year >= 2025) & (df['time'] <= datetime.now() + timedelta(days=1))]
    
    return df

# Ejecución
df_base = carga_inteligente()

if df_base is not None and not df_base.empty:
    # --- INFO EN SIDEBAR ---
    f_min, f_max = df_base['time'].min(), df_base['time'].max()
    st.sidebar.divider()
    st.sidebar.info(f"📅 **Inicio:** {f_min.strftime('%d/%m/%Y %H:%M')}")
    st.sidebar.info(f"📅 **Fin:** {f_max.strftime('%d/%m/%Y %H:%M')}")
    st.sidebar.write(f"🔢 Registros: **{len(df_base):,}**")

    # Selector de Rango
    rango = st.sidebar.date_input(
        "Periodo:",
        value=(f_max.date() - timedelta(days=7), f_max.date()),
        min_value=f_min.date(),
        max_value=f_max.date()
    )

    # 4. FILTRADO Y DASHBOARD
    if isinstance(rango, tuple) and len(rango) == 2:
        df_plot = df_base[(df_base['time'].dt.date >= rango[0]) & (df_base['time'].dt.date <= rango[1])]
    else:
        df_plot = df_base

    if not df_plot.empty:
        # Selector de variables amigable
        variables = {
            "🌡 Temperatura": "temperature_2m (°C)",
            "💧 Humedad": "relative_humidity_2m (%)",
            "🌧 Precipitación": "precipitation (mm)",
            "🥵 Sensación": "apparent_temperature (°C)"
        }
        
        label = st.selectbox("Parámetro:", list(variables.keys()))
        var = variables[label]

        # Métricas
        c1, c2, c3 = st.columns(3)
        c1.metric("Máximo", f"{df_plot[var].max():.1f}")
        c2.metric("Mínimo", f"{df_plot[var].min():.1f}")
        c3.metric("Último", f"{df_plot[var].iloc[-1]:.1f}")

        # Gráfico
        fig = px.line(df_plot, x='time', y=var, markers=True, template="plotly_white", color_discrete_sequence=['#2E7D32'])
        fig.update_xaxes(rangeslider_visible=True)
        st.plotly_chart(fig, use_container_width=True)

        # 5. DESCARGA
        st.divider()
        if st.text_input("Clave de descarga", type="password") == "santarosa2026":
            txt = df_plot.to_csv(index=False, sep='\t').encode('utf-8')
            st.download_button("💾 Descargar Selección", txt, f"FCA_SR_{rango[0]}.txt")
    else:
        st.warning("No hay datos en el rango.")
else:
    st.error("No se detectaron datos. Revisa los archivos en GitHub.")

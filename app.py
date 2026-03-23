import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime, timedelta
import os
import io

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

# 3. MOTOR DE RECONSTRUCCIÓN DE TEXTO (Evita el corte del 21 de marzo)
@st.cache_data(ttl=60) # Se actualiza cada minuto para pruebas
def carga_total_y_limpia():
    archivos = ['datos_clima2025.csv', 'datos_clima2026.csv']
    filas_finales = []
    columnas = None

    for nombre in archivos:
        if os.path.exists(nombre):
            try:
                with open(nombre, 'r', encoding='utf-8', errors='ignore') as f:
                    contenido = f.read() # Leemos el archivo entero de una vez
                
                # Dividimos por líneas y limpiamos espacios locos
                lineas = [l.strip() for l in contenido.split('\n') if l.strip()]
                
                # Buscamos la cabecera real
                for i, linea in enumerate(lineas):
                    if 'time' in linea.lower() and ',' in linea:
                        if columnas is None:
                            columnas = [c.strip() for c in linea.split(',')]
                        # Agregamos todas las líneas después de la cabecera
                        for dato in lineas[i+1:]:
                            partes = [p.strip() for p in dato.split(',')]
                            if len(partes) >= len(columnas):
                                filas_finales.append(partes[:len(columnas)])
                        break
                st.sidebar.success(f"✅ {nombre} absorbido por completo.")
            except Exception as e:
                st.sidebar.error(f"❌ Error en {nombre}: {e}")

    if not filas_finales: return None

    # Creamos el DataFrame
    df = pd.DataFrame(filas_finales, columns=columnas)
    
    # Conversión Forzada
    df['time'] = pd.to_datetime(df['time'], dayfirst=True, errors='coerce')
    for col in df.columns:
        if col != 'time':
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Limpieza: eliminar basura y duplicados
    df = df.dropna(subset=['time']).drop_duplicates().sort_values('time').reset_index(drop=True)
    
    # IMPORTANTE: No filtrar por fecha máxima aquí para ver si el archivo tiene el 23
    return df

# Ejecución
df_base = carga_total_y_limpia()

if df_base is not None and not df_base.empty:
    # --- PANEL DE CONTROL ---
    f_min, f_max = df_base['time'].min(), df_base['time'].max()
    
    st.sidebar.divider()
    st.sidebar.header("📊 Resumen del Sistema")
    st.sidebar.info(f"📅 **Inicio:** {f_min.strftime('%d/%m/%Y %H:%M')}")
    st.sidebar.info(f"📅 **Fin Detectado:** {f_max.strftime('%d/%m/%Y %H:%M')}")
    st.sidebar.metric("Registros en Memoria", f"{len(df_base):,}")

    # Selector de Rango
    rango = st.sidebar.date_input(
        "Ver periodo:",
        value=(f_max.date() - timedelta(days=7), f_max.date()),
        min_value=f_min.date(),
        max_value=f_max.date()
    )

    # 4. DASHBOARD
    if isinstance(rango, tuple) and len(rango) == 2:
        df_plot = df_base[(df_base['time'].dt.date >= rango[0]) & (df_base['time'].dt.date <= rango[1])]
    else:
        df_plot = df_base

    if not df_plot.empty:
        # Variables
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
        c3.metric("Último valor", f"{df_plot[var].iloc[-1]:.1f}")

        # Gráfico con Slider de tiempo
        fig = px.line(df_plot, x='time', y=var, markers=True, template="plotly_white")
        fig.update_traces(line_color='#2E7D32', line_width=2)
        fig.update_xaxes(rangeslider_visible=True)
        st.plotly_chart(fig, use_container_width=True)

        # 5. DESCARGA
        st.divider()
        if st.text_input("Contraseña de descarga", type="password") == "santarosa2026":
            csv = df_plot.to_csv(index=False, sep='\t').encode('utf-8')
            st.download_button("💾 Bajar reporte .txt", csv, f"FCA_{rango[0]}.txt")
    else:
        st.warning("No hay datos en el rango.")
else:
    st.error("Error: Los archivos CSV están vacíos o no tienen la columna 'time'.")

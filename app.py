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
    st.markdown("<h1 style='text-align: center; color: #1B5E20;'>Monitoreo Meteorológico FCA UNA</h1>", unsafe_allow_html=True)
except:
    st.title("FCA UNA - Filial Santa Rosa")

st.divider()

# 3. CARGA DE FUERZA BRUTA
@st.cache_data
def carga_ultra_limpia(nombre_archivo):
    try:
        # Leemos el archivo como texto puro
        with open(nombre_archivo, 'r', encoding='utf-8', errors='ignore') as f:
            lineas = f.readlines()
        
        # Saltamos el encabezado de Open-Meteo (3 primeras líneas)
        # La cuarta línea (index 3) debería ser la cabecera: time,temp,hum...
        columnas = [c.strip() for c in lineas[3].split(',')]
        
        datos_validados = []
        for l in lineas[4:]:
            partes = [p.strip() for p in l.split(',')]
            # Solo guardamos si la fila tiene el mismo número de columnas que la cabecera
            if len(partes) == len(columnas):
                datos_validados.append(partes)
        
        df = pd.DataFrame(datos_validados, columns=columnas)
        
        # Convertimos las fechas intentando varios formatos
        df['time'] = pd.to_datetime(df['time'], dayfirst=True, errors='coerce')
        
        # Convertimos los números
        for col in columnas:
            if col != 'time':
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Limpieza de nulos y ordenamiento
        df = df.dropna(subset=['time'])
        df = df.sort_values('time').reset_index(drop=True)
        
        return df
    except Exception as e:
        st.error(f"Error crítico de lectura: {e}")
        return None

# Intentar cargar
df_base = carga_ultra_limpia('datos_clima.csv')

if df_base is not None and not df_base.empty:
    # --- PANEL DE CONTROL ---
    st.sidebar.header("📊 Diagnóstico del Archivo")
    
    # Verificamos qué años y días existen realmente en el DataFrame
    fecha_min = df_base['time'].min()
    fecha_max = df_base['time'].max()
    años_encontrados = df_base['time'].dt.year.unique()
    
    st.sidebar.info(f"Registros totales: {len(df_base)}")
    st.sidebar.success(f"Años detectados: {list(años_encontrados)}")
    st.sidebar.write(f"📅 **Inicia:** {fecha_min.strftime('%d/%m/%Y')}")
    st.sidebar.write(f"📅 **Termina:** {fecha_max.strftime('%d/%m/%Y')}")

    # Selector de Rango
    rango = st.sidebar.date_input(
        "Selecciona el periodo:",
        value=(fecha_max.date() - timedelta(days=7), fecha_max.date()),
        min_value=fecha_min.date(),
        max_value=fecha_max.date()
    )

    # 4. FILTRADO
    if isinstance(rango, tuple) and len(rango) == 2:
        df_final = df_base[(df_base['time'].dt.date >= rango[0]) & (df_base['time'].dt.date <= rango[1])]
    else:
        df_final = df_base

    # 5. GRÁFICO
    if not df_final.empty:
        st.subheader("📈 Visualización de Datos")
        v = st.selectbox("Parámetro:", [c for c in df_final.columns if c != 'time'])
        
        fig = px.line(df_final, x='time', y=v, markers=True, template="plotly_white", color_discrete_sequence=['#2E7D32'])
        fig.update_xaxes(rangeslider_visible=True) # Para navegar fácilmente
        st.plotly_chart(fig, use_container_width=True)
        
        # DESCARGA
        st.divider()
        pw = st.text_input("Clave para descargar (.txt)", type="password")
        if pw == "santarosa2026":
            txt = df_final.to_csv(index=False, sep='\t').encode('utf-8')
            st.download_button("💾 Descargar Selección", txt, f"Reporte_{rango[0]}.txt")
    
    # 6. EXPLORADOR TÉCNICO (Solo para ti)
    with st.expander("Ver las primeras 10 filas del archivo (Depuración)"):
        st.write(df_base.head(10))
    with st.expander("Ver las últimas 10 filas del archivo (Depuración)"):
        st.write(df_base.tail(10))

else:
    st.error("No se detectaron datos. El archivo 'datos_clima.csv' podría estar vacío o mal nombrado en GitHub.")

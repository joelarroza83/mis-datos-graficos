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
    st.image(logo, width=450)
    st.markdown("<h1 style='text-align: center; color: #1B5E20;'>Monitoreo Meteorológico FCA UNA</h1>", unsafe_allow_html=True)
except:
    st.title("FCA UNA - Filial Santa Rosa")

st.divider()

# 3. MOTOR DE CARGA ROBUSTO
@st.cache_data(ttl=300)
def cargar_datos_fca():
    archivos = ['datos_clima2025.csv', 'datos_clima2026.csv']
    lista_dfs = []
    
    for nombre in archivos:
        if os.path.exists(nombre):
            try:
                # Leemos ignorando errores de codificación y filas mal formadas
                df_t = pd.read_csv(
                    nombre, 
                    skiprows=3, 
                    on_bad_lines='skip', 
                    engine='c', # Motor C es el más rápido y estable
                    encoding='utf-8',
                    low_memory=False
                )
                
                # Limpiar nombres de columnas
                df_t.columns = [c.strip() for c in df_t.columns]
                
                if 'time' in df_t.columns:
                    # Convertir fecha (Formato ISO o Día/Mes/Año)
                    df_t['time'] = pd.to_datetime(df_t['time'], errors='coerce')
                    df_t = df_t.dropna(subset=['time'])
                    lista_dfs.append(df_t)
                    st.sidebar.success(f"✅ {nombre} cargado")
            except Exception as e:
                st.sidebar.error(f"❌ Error en {nombre}: {e}")
        else:
            st.sidebar.warning(f"⚠️ No encontrado: {nombre}")

    if not lista_dfs: return None

    # Unir archivos
    df_full = pd.concat(lista_dfs, ignore_index=True)
    
    # Convertir todas las columnas excepto 'time' a números
    for col in df_full.columns:
        if col != 'time':
            df_full[col] = pd.to_numeric(df_full[col], errors='coerce')

    # Ordenar y limpiar duplicados
    df_full = df_full.sort_values('time').drop_duplicates().reset_index(drop=True)
    
    return df_full

# Ejecución
df_base = cargar_datos_fca()

if df_base is not None and not df_base.empty:
    # --- PANEL LATERAL ---
    f_min, f_max = df_base['time'].min(), df_base['time'].max()
    
    st.sidebar.divider()
    st.sidebar.header("📊 Información de Base")
    st.sidebar.info(f"📅 **Inicio:** {f_min.strftime('%d/%m/%Y %H:%M')}")
    st.sidebar.info(f"📅 **Fin:** {f_max.strftime('%d/%m/%Y %H:%M')}")
    st.sidebar.metric("Total Filas", f"{len(df_base):,}")

    # Selector de Rango
    rango = st.sidebar.date_input(
        "Filtrar Periodo:",
        value=(f_max.date() - timedelta(days=7), f_max.date()),
        min_value=f_min.date(),
        max_value=f_max.date()
    )

    # 4. DASHBOARD
    if isinstance(rango, tuple) and len(rango) == 2:
        df_p = df_base[(df_base['time'].dt.date >= rango[0]) & (df_base['time'].dt.date <= rango[1])]
    else:
        df_p = df_base

    if not df_p.empty:
        # Variables mapeadas para el usuario
        mapeo = {
            "Temperatura (°C)": "temperature_2m (°C)",
            "Humedad (%)": "relative_humidity_2m (%)",
            "Precipitación (mm)": "precipitation (mm)",
            "Sensación Térmica (°C)": "apparent_temperature (°C)"
        }
        
        # Filtramos solo las que existan en el CSV
        opciones = [k for k, v in mapeo.items() if v in df_p.columns]
        sel_label = st.selectbox("Seleccione Parámetro:", opciones)
        sel_col = mapeo[sel_label]

        # Métricas
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Máximo", f"{df_p[sel_col].max():.1f}")
        c2.metric("Mínimo", f"{df_p[sel_col].min():.1f}")
        c3.metric("Promedio", f"{df_p[sel_col].mean():.1f}")
        c4.metric("Último", f"{df_p[sel_col].iloc[-1]:.1f}")

        # Gráfico
        fig = px.line(df_p, x='time', y=sel_col, markers=True, template="plotly_white", color_discrete_sequence=['#2E7D32'])
        fig.update_xaxes(rangeslider_visible=True)
        st.plotly_chart(fig, use_container_width=True)

        # 5. DESCARGA (santarosa2026)
        st.divider()
        if st.text_input("Clave de descarga", type="password") == "santarosa2026":
            csv_data = df_p.to_csv(index=False, sep='\t').encode('utf-8')
            st.download_button("💾 Bajar Reporte", csv_data, f"FCA_{rango[0]}.txt")
    else:
        st.warning("No hay datos para las fechas seleccionadas.")
else:
    st.error("Error: Los archivos no tienen el formato correcto o la columna 'time' no existe.")

import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime, timedelta
import os

# =============================
# CONFIGURACIÓN GENERAL
# =============================
st.set_page_config(page_title="FCA UNA - Santa Rosa", layout="wide", page_icon="🌱")

# =============================
# ENCABEZADO
# =============================
try:
    logo = Image.open('logoproyecto.png')
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.image(logo, use_container_width=True)
    st.markdown("<h1 style='text-align: center; color: #1B5E20;'>Monitoreo Meteorológico FCA UNA</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #388E3C;'>Filial Santa Rosa - Agrometeorología</h3>", unsafe_allow_html=True)
except:
    st.title("FCA UNA - Filial Santa Rosa")

st.divider()

# =============================
# CARGA DE DATOS (RESCATE DE ÚLTIMOS DÍAS)
# =============================
@st.cache_data(ttl=600) # Se actualiza cada 10 min
def carga_multianual():
    archivos = ['datos_clima2025.csv', 'datos_clima2026.csv']
    dfs = []

    for nombre in archivos:
        if os.path.exists(nombre):
            try:
                # Usamos un motor más flexible para no perder el final del archivo
                df_temp = pd.read_csv(nombre, skiprows=4, on_bad_lines='skip', engine='python')
                dfs.append(df_temp)
                st.sidebar.success(f"✅ {nombre} conectado")
            except Exception as e:
                st.sidebar.error(f"❌ Error en {nombre}: {e}")
    
    if not dfs: return None

    df = pd.concat(dfs, ignore_index=True)
    df.columns = [c.strip() for c in df.columns]

    # Conversión robusta de fecha
    df['time'] = pd.to_datetime(df['time'], dayfirst=True, errors='coerce')
    
    # Convertir datos numéricos
    cols_num = [c for c in df.columns if c != 'time']
    for col in cols_num:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Limpieza: Eliminar filas vacías y ordenar
    df = df.dropna(subset=['time']).sort_values('time').reset_index(drop=True)
    
    # IMPORTANTE: Asegurar que el 2025 y 2026 no tengan fechas "locas"
    df = df[df['time'].dt.year >= 2025]
    
    return df

# Ejecución
df_base = carga_multianual()

if df_base is not None and not df_base.empty:
    # --- INFO SIDEBAR ---
    st.sidebar.divider()
    f_min, f_max = df_base['time'].min(), df_base['time'].max()
    años = df_base['time'].dt.year.unique()

    st.sidebar.header("📊 Estado de la Base")
    st.sidebar.info(f"📅 Inicio: {f_min.strftime('%d/%m/%Y')}")
    st.sidebar.info(f"📅 Fin: {f_max.strftime('%d/%m/%Y')}")
    st.sidebar.metric("Total Registros", f"{len(df_base):,}")
    st.sidebar.write(f"Años detectados: {list(años)}")

    # Selector de Rango (Calendario)
    rango = st.sidebar.date_input(
        "Seleccionar periodo:",
        value=(f_max.date() - timedelta(days=7), f_max.date()),
        min_value=f_min.date(),
        max_value=f_max.date()
    )

    # Filtrado
    if isinstance(rango, tuple) and len(rango) == 2:
        inicio, fin = rango
        df_plot = df_base[(df_base['time'].dt.date >= inicio) & (df_base['time'].dt.date <= fin)]
    else:
        df_plot = df_base

    if not df_plot.empty:
        # --- DASHBOARD ---
        variables = {
            "🌡 Temperatura": "temperature_2m (°C)",
            "💧 Humedad": "relative_humidity_2m (%)",
            "🌧 Precipitación": "precipitation (mm)",
            "🌦 Lluvia": "rain (mm)",
            "🥵 Sensación térmica": "apparent_temperature (°C)"
        }

        label = st.selectbox("Elija el parámetro a analizar:", list(variables.keys()))
        var = variables[label]

        # Métricas Dinámicas
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Máximo", f"{df_plot[var].max():.1f}")
        c2.metric("Mínimo", f"{df_plot[var].min():.1f}")
        c3.metric("Promedio", f"{df_plot[var].mean():.1f}")
        c4.metric("Último dato", f"{df_plot[var].iloc[-1]:.1f}")

        # Gráfico Profesional
        fig = px.line(df_plot, x='time', y=var, markers=True, template="plotly_white")
        fig.update_traces(line_color='#2E7D32', line_width=2)
        fig.update_layout(hovermode="x unified", xaxis_title="Fecha y Hora", yaxis_title=label)
        fig.update_xaxes(rangeslider_visible=True)
        st.plotly_chart(fig, use_container_width=True)

        # --- EXPORTACIÓN ---
        st.divider()
        with st.expander("🔓 Panel de Descarga"):
            pw = st.text_input("Contraseña (santarosa2026):", type="password")
            if pw == "santarosa2026":
                txt = df_plot.to_csv(index=False, sep='\t').encode('utf-8')
                st.download_button(
                    label=f"💾 Descargar {len(df_plot)} registros (.txt)",
                    data=txt,
                    file_name=f"FCA_SR_Reporte_{inicio}_{fin}.txt",
                    mime="text/plain"
                )
    else:
        st.warning("No hay registros en las fechas seleccionadas.")
else:
    st.error("Error: Verifica que los archivos 'datos_clima2025.csv' y 'datos_clima2026.csv' estén en la carpeta raíz de GitHub.")

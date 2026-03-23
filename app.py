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
    st.image(logo, width=450)
    st.markdown("<h1 style='text-align: center; color: #1B5E20;'>Monitoreo Meteorológico FCA UNA</h1>", unsafe_allow_html=True)
except:
    st.title("FCA UNA - Filial Santa Rosa")

st.divider()

# =============================
# CARGA DE DATOS MEJORADA
# =============================
@st.cache_data
def carga_multianual():
    archivos = ['datos_clima2025.csv', 'datos_clima2026.csv']
    dfs = []

    for nombre in archivos:
        if os.path.exists(nombre):
            try:
                df_temp = pd.read_csv(nombre, skiprows=4)
                dfs.append(df_temp)
                st.sidebar.success(f"✅ {nombre} cargado")
            except Exception as e:
                st.sidebar.error(f"❌ Error en {nombre}: {e}")
        else:
            st.sidebar.warning(f"⚠️ No encontrado: {nombre}")

    if not dfs:
        return None

    df = pd.concat(dfs, ignore_index=True)

    # Normalizar nombres de columnas
    df.columns = [c.strip() for c in df.columns]

    # Convertir tipos
    df['time'] = pd.to_datetime(df['time'], errors='coerce')

    for col in df.columns:
        if col != 'time':
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Limpieza
    df = df.dropna(subset=['time'])
    df = df.sort_values('time').reset_index(drop=True)

    return df

# =============================
# EJECUCIÓN
# =============================
df_base = carga_multianual()

if df_base is not None and not df_base.empty:

    # =============================
    # SIDEBAR
    # =============================
    st.sidebar.divider()
    f_min, f_max = df_base['time'].min(), df_base['time'].max()

    st.sidebar.header("📊 Datos en Memoria")
    st.sidebar.info(f"Desde: {f_min.strftime('%d/%m/%Y')}")
    st.sidebar.info(f"Hasta: {f_max.strftime('%d/%m/%Y')}")
    st.sidebar.write(f"Registros: {len(df_base)}")

    rango = st.sidebar.date_input(
        "Filtrar fechas:",
        value=(f_max.date() - timedelta(days=7), f_max.date()),
        min_value=f_min.date(),
        max_value=f_max.date()
    )

    # =============================
    # FILTRO
    # =============================
    if isinstance(rango, tuple) and len(rango) == 2:
        df_plot = df_base[(df_base['time'].dt.date >= rango[0]) & (df_base['time'].dt.date <= rango[1])]
    else:
        df_plot = df_base

    if not df_plot.empty:

        st.subheader(f"📈 Gráfico: {rango[0]} al {rango[1]}")

        # =============================
        # SELECTOR DE VARIABLE AMIGABLE
        # =============================
        variables = {
            "🌡 Temperatura": "temperature_2m (°C)",
            "💧 Humedad": "relative_humidity_2m (%)",
            "🌧 Precipitación": "precipitation (mm)",
            "🌦 Lluvia": "rain (mm)",
            "🥵 Sensación térmica": "apparent_temperature (°C)"
        }

        label = st.selectbox("Parámetro:", list(variables.keys()))
        var = variables[label]

        # =============================
        # MÉTRICAS
        # =============================
        col1, col2, col3 = st.columns(3)

        col1.metric("Máximo", f"{df_plot[var].max():.2f}")
        col2.metric("Mínimo", f"{df_plot[var].min():.2f}")
        col3.metric("Promedio", f"{df_plot[var].mean():.2f}")

        # =============================
        # GRÁFICO
        # =============================
        fig = px.line(
            df_plot,
            x='time',
            y=var,
            markers=True,
            template="plotly_white"
        )

        fig.update_xaxes(rangeslider_visible=True)
        st.plotly_chart(fig, use_container_width=True)

        # =============================
        # ALERTAS SIMPLES
        # =============================
        if var == "precipitation (mm)" and df_plot[var].max() > 50:
            st.error("⚠️ Alerta: Lluvia intensa detectada")

        if var == "temperature_2m (°C)" and df_plot[var].max() > 38:
            st.warning("🔥 Alerta: Temperatura muy alta")

        # =============================
        # DESCARGA SEGURA
        # =============================
        st.divider()

        pw = st.text_input("Clave de descarga", type="password")
        CLAVE = os.getenv("CLAVE_DESCARGA", "santarosa2026")

        if pw == CLAVE:
            txt = df_plot.to_csv(index=False, sep='\t').encode('utf-8')
            st.download_button(
                "💾 Descargar datos",
                txt,
                f"Datos_{rango[0]}.txt"
            )

    else:
        st.warning("No hay datos para el rango seleccionado")

else:
    st.error("No se pudieron cargar los datos. Verifica los archivos CSV")

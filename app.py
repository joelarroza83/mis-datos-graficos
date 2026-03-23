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
    st.image(logo, width=500)
    st.markdown("<h1 style='text-align: center; color: #1B5E20;'>Monitoreo Meteorológico FCA UNA</h1>", unsafe_allow_html=True)
except:
    st.title("FCA UNA - Filial Santa Rosa")

st.divider()

# 3. FUNCIÓN DE CARGA MULTI-ARCHIVO
@st.cache_data
def cargar_todos_los_años():
    # Lista de archivos que vas a subir a GitHub
    archivos_objetivo = ['datos_clima2025.csv', 'datos_clima2026.csv']
    lista_df = []
    
    for nombre in archivos_objetivo:
        if os.path.exists(nombre):
            try:
                # Leemos cada año con limpieza individual
                temp_df = pd.read_csv(nombre, skiprows=3, on_bad_lines='skip', engine='python')
                temp_df.columns = temp_df.columns.str.strip()
                
                if 'time' in temp_df.columns:
                    temp_df['time'] = pd.to_datetime(temp_df['time'], dayfirst=True, errors='coerce')
                    temp_df = temp_df.dropna(subset=['time'])
                    lista_df.append(temp_df)
            except Exception as e:
                st.sidebar.error(f"Error en {nombre}: {e}")
    
    if not lista_df:
        return None
    
    # Unimos todos los años en un solo "Gran DataFrame"
    df_completo = pd.concat(lista_df, axis=0, ignore_index=True)
    
    # Ordenamos cronológicamente para que la línea del gráfico sea continua
    df_completo = df_completo.sort_values(by='time').reset_index(drop=True)
    
    # Filtro de seguridad (Solo hasta hoy)
    df_completo = df_completo[df_completo['time'] <= datetime.now() + timedelta(hours=1)]
    
    return df_completo

# Ejecutar carga
df_base = cargar_todos_los_años()

if df_base is not None and not df_base.empty:
    # --- PANEL LATERAL ---
    st.sidebar.header("📂 Gestión de Archivos")
    
    # Detectar qué años están cargados realmente
    años_activos = df_base['time'].dt.year.unique()
    st.sidebar.success(f"Años en sistema: {list(años_activos)}")
    
    f_min = df_base['time'].min()
    f_max = df_base['time'].max()
    
    st.sidebar.write(f"📊 Registros totales: **{len(df_base)}**")
    st.sidebar.divider()

    # Selector de Rango Inteligente (Abarca todos los años disponibles)
    st.sidebar.header("📅 Filtro de Fecha")
    rango = st.sidebar.date_input(
        "Seleccione el periodo:",
        value=(f_max.date() - timedelta(days=7), f_max.date()),
        min_value=f_min.date(),
        max_value=f_max.date(),
        help="Puedes navegar entre 2025 y 2026 usando el selector de año del calendario"
    )

    # 4. FILTRADO
    if isinstance(rango, tuple) and len(rango) == 2:
        df_final = df_base[(df_base['time'].dt.date >= rango[0]) & (df_base['time'].dt.date <= rango[1])]
    else:
        df_final = df_base

    # 5. VISUALIZACIÓN
    if not df_final.empty:
        # Métricas del periodo seleccionado
        m1, m2, m3 = st.columns(3)
        u = df_final.iloc[-1]
        m1.metric("Temperatura", f"{u.iloc[2]} °C")
        m2.metric("Humedad", f"{u.iloc[3]} %")
        m3.metric("Último dato", u['time'].strftime('%d/%m/%Y %H:%M'))

        st.subheader(f"📈 Gráfico Agrometeorológico")
        variables = [c for c in df_final.columns if c != 'time']
        seleccion = st.selectbox("Parámetro a visualizar:", variables)
        
        fig = px.line(df_final, x='time', y=seleccion, markers=True, template="plotly_white")
        fig.update_traces(line_color='#2E7D32', line_width=2)
        # Slider para navegar por los meses del año seleccionado
        fig.update_xaxes(rangeslider_visible=True)
        st.plotly_chart(fig, use_container_width=True)

        # 6. EXPORTACIÓN (santarosa2026)
        st.divider()
        col_p, col_b = st.columns([1, 1])
        with col_p:
            passw = st.text_input("Clave de descarga", type="password")
        with col_b:
            if passw == "santarosa2026":
                txt = df_final.to_csv(index=False, sep='\t').encode('utf-8')
                st.download_button(
                    label=f"💾 Descargar Reporte ({len(df_final)} registros)",
                    data=txt,
                    file_name=f"FCA_SR_Reporte_{rango[0]}_a_{rango[1]}.txt",
                    mime="text/plain"
                )
    else:
        st.warning("No hay datos en el rango seleccionado.")
else:
    st.error("⚠️ No se encontraron los archivos: 'datos_clima2025.csv' o 'datos_clima2026.csv'. Por favor, verifica los nombres en GitHub.")

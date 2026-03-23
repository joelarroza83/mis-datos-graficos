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

# 3. CARGA INDEPENDIENTE Y UNIÓN FORZADA
@st.cache_data
def cargar_y_unir_archivos():
    # Definimos los archivos por año
    archivos = {
        "2025": "datos_clima2025.csv",
        "2026": "datos_clima2026.csv"
    }
    
    lista_datos = []
    
    for año, nombre in archivos.items():
        if os.path.exists(nombre):
            try:
                # Leemos el archivo de ese año
                df_temp = pd.read_csv(nombre, skiprows=3, on_bad_lines='skip', engine='python')
                df_temp.columns = df_temp.columns.str.strip()
                
                if 'time' in df_temp.columns:
                    # Convertimos fechas de ese año específico
                    df_temp['time'] = pd.to_datetime(df_temp['time'], dayfirst=True, errors='coerce')
                    df_temp = df_temp.dropna(subset=['time'])
                    
                    # Nos aseguramos de que solo tenga datos de ese año para evitar solapamientos
                    df_temp = df_temp[df_temp['time'].dt.year == int(año)]
                    
                    lista_datos.append(df_temp)
                    st.sidebar.success(f"✅ Archivo {año} cargado correctamente.")
            except Exception as e:
                st.sidebar.error(f"❌ Error leyendo {nombre}: {e}")
        else:
            st.sidebar.warning(f"⚠️ No se encontró el archivo: {nombre}")

    if not lista_datos:
        return None
    
    # UNIÓN: Pegamos los años uno debajo del otro
    df_unido = pd.concat(lista_datos, axis=0, ignore_index=True)
    
    # Ordenamos por fecha (del más viejo al más nuevo)
    df_unido = df_unido.sort_values(by='time').reset_index(drop=True)
    
    # Filtro anti-futuro
    df_unido = df_unido[df_unido['time'] <= datetime.now() + timedelta(days=1)]
    
    return df_unido

# Ejecutar la carga
df_base = cargar_y_unir_archivos()

if df_base is not None and not df_base.empty:
    # --- PANEL LATERAL ---
    st.sidebar.divider()
    f_min = df_base['time'].min()
    f_max = df_base['time'].max()
    
    st.sidebar.header("📅 Control de Datos")
    st.sidebar.write(f"**Inicio Real:** {f_min.strftime('%d/%m/%Y')}")
    st.sidebar.write(f"**Fin Real:** {f_max.strftime('%d/%m/%Y')}")
    st.sidebar.write(f"**Total Registros:** {len(df_base)}")

    # Selector de Rango
    rango = st.sidebar.date_input(
        "Periodo a visualizar:",
        value=(f_max.date() - timedelta(days=7), f_max.date()),
        min_value=f_min.date(),
        max_value=f_max.date()
    )

    # 4. FILTRADO
    if isinstance(rango, tuple) and len(rango) == 2:
        df_final = df_base[(df_base['time'].dt.date >= rango[0]) & (df_base['time'].dt.date <= rango[1])]
    else:
        df_final = df_base

    # 5. VISUALIZACIÓN
    if not df_final.empty:
        st.subheader(f"📊 Análisis: {rango[0]} al {rango[1]}")
        
        # Métricas rápidas
        col1, col2, col3 = st.columns(3)
        u = df_final.iloc[-1]
        col1.metric("Última Temp.", f"{u.iloc[2]} °C")
        col2.metric("Última Hum.", f"{u.iloc[3]} %")
        col3.metric("Fecha/Hora", u['time'].strftime('%H:%M - %d/%m'))

        # Gráfico con Slider
        var = st.selectbox("Variable:", [c for c in df_final.columns if c != 'time'])
        fig = px.line(df_final, x='time', y=var, markers=True, template="plotly_white", color_discrete_sequence=['#2E7D32'])
        fig.update_xaxes(rangeslider_visible=True)
        st.plotly_chart(fig, use_container_width=True)

        # 6. EXPORTACIÓN
        st.divider()
        passw = st.text_input("Clave de descarga", type="password")
        if passw == "santarosa2026":
            txt = df_final.to_csv(index=False, sep='\t').encode('utf-8')
            st.download_button("💾 Descargar Selección", txt, f"FCA_SR_{rango[0]}.txt")
    else:
        st.warning("No hay datos en las fechas elegidas.")
else:
    st.error("No se pudo cargar la base de datos. Verifica que los nombres de archivo en GitHub coincidan.")

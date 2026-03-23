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
    st.image(logo, width=400)
    st.markdown("<h1 style='text-align: center; color: #1B5E20;'>Monitoreo Meteorológico FCA UNA</h1>", unsafe_allow_html=True)
except:
    st.title("FCA UNA - Filial Santa Rosa")

st.divider()

# 3. MOTOR DE CARGA UNIVERSAL (Lee todas las columnas existentes)
@st.cache_data(ttl=300)
def cargar_datos_universales():
    archivos = ['datos_clima2025.csv', 'datos_clima2026.csv']
    dfs = []
    
    for nombre in archivos:
        if os.path.exists(nombre):
            try:
                # Leemos el archivo completo
                # skiprows=3 suele ser el estándar de Open-Meteo para llegar a la cabecera
                df_t = pd.read_csv(nombre, skiprows=3, on_bad_lines='skip', engine='python', encoding='utf-8')
                
                # Limpiamos nombres de columnas (quitar espacios y saltos de línea)
                df_t.columns = [c.strip() for c in df_t.columns]
                
                # Buscamos la columna de tiempo (indispensable)
                col_tiempo = [c for c in df_t.columns if 'time' in c.lower()]
                
                if col_tiempo:
                    # Renombramos la columna de tiempo a algo estándar para el código
                    df_t = df_t.rename(columns={col_tiempo[0]: 'Fecha'})
                    # Convertimos a formato fecha
                    df_t['Fecha'] = pd.to_datetime(df_t['Fecha'], errors='coerce')
                    dfs.append(df_t)
                    st.sidebar.success(f"✅ {nombre} cargado")
            except Exception as e:
                st.sidebar.error(f"❌ Error en {nombre}: {e}")
    
    if not dfs: return None
    
    # Unir todos los archivos
    df_full = pd.concat(dfs, ignore_index=True)
    df_full = df_full.dropna(subset=['Fecha'])
    
    # Convertir todas las demás columnas a números automáticamente
    for col in df_full.columns:
        if col != 'Fecha':
            df_full[col] = pd.to_numeric(df_full[col], errors='coerce')
            
    return df_full.sort_values('Fecha').drop_duplicates().reset_index(drop=True)

# Ejecución
df_base = cargar_datos_universales()

if df_base is not None and not df_base.empty:
    # --- PANEL LATERAL ---
    f_min, f_max = df_base['Fecha'].min(), df_base['Fecha'].max()
    st.sidebar.divider()
    st.sidebar.info(f"📅 **Datos desde:** {f_min.strftime('%d/%m/%Y')}")
    st.sidebar.info(f"📅 **Datos hasta:** {f_max.strftime('%d/%m/%Y')}")
    st.sidebar.write(f"🔢 Registros totales: **{len(df_base):,}**")

    # Selector de Rango
    rango = st.sidebar.date_input(
        "Periodo a visualizar:",
        value=(f_max.date() - timedelta(days=7), f_max.date()),
        min_value=f_min.date(),
        max_value=f_max.date()
    )

    # 4. FILTRADO
    if isinstance(rango, tuple) and len(rango) == 2:
        df_p = df_base[(df_base['Fecha'].dt.date >= rango[0]) & (df_base['Fecha'].dt.date <= rango[1])]
    else:
        df_p = df_base

    if not df_p.empty:
        # SELECTOR DINÁMICO: Muestra TODAS las variables encontradas en el CSV
        todas_las_variables = [c for c in df_p.columns if c != 'Fecha']
        
        st.subheader("📊 Análisis de Variables")
        var_seleccionada = st.selectbox("Seleccione la variable que desea observar:", todas_las_variables)

        # Métricas de la variable elegida
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Máximo", f"{df_p[var_seleccionada].max():.2f}")
        c2.metric("Mínimo", f"{df_p[var_seleccionada].min():.2f}")
        c3.metric("Promedio", f"{df_p[var_seleccionada].mean():.2f}")
        c4.metric("Último dato", f"{df_p[var_seleccionada].iloc[-1]:.2f}")

        # Gráfico
        fig = px.line(df_p, x='Fecha', y=var_seleccionada, markers=True, template="plotly_white")
        fig.update_traces(line_color='#2E7D32', line_width=2)
        fig.update_xaxes(rangeslider_visible=True)
        st.plotly_chart(fig, use_container_width=True)

        # 5. DESCARGA
        st.divider()
        if st.text_input("Clave de descarga", type="password") == "santarosa2026":
            csv = df_p.to_csv(index=False, sep='\t').encode('utf-8')
            st.download_button("💾 Descargar selección actual", csv, f"FCA_SR_Export.txt")
    else:
        st.warning("No hay datos para el rango seleccionado.")
else:
    st.error("No se detectaron variables. Verifica que los archivos CSV tengan una columna llamada 'time'.")

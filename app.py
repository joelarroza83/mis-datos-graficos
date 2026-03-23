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

# 3. MOTOR DE CARGA "INTELIGENTE" (Busca variables por palabra clave)
@st.cache_data(ttl=300)
def cargar_datos_completos():
    archivos = ['datos_clima2025.csv', 'datos_clima2026.csv']
    dfs = []
    
    for nombre in archivos:
        if os.path.exists(nombre):
            try:
                # Leemos con motor python para mayor tolerancia a errores de línea
                df_t = pd.read_csv(nombre, skiprows=3, on_bad_lines='skip', engine='python', encoding='utf-8')
                df_t.columns = [c.strip().lower() for c in df_t.columns] # Normalizamos nombres
                
                # Mapeo flexible: Buscamos la columna que contenga la palabra clave
                mapeo_columnas = {}
                
                # Buscamos 'time'
                cols_time = [c for c in df_t.columns if 'time' in c]
                if cols_time: mapeo_columnas[cols_time[0]] = 'Fecha'
                
                # Buscamos 'temp' (Temperatura)
                cols_temp = [c for c in df_t.columns if 'temp' in c]
                if cols_temp: mapeo_columnas[cols_temp[0]] = 'Temperatura (°C)'
                
                # Buscamos 'hum' (Humedad)
                cols_hum = [c for c in df_t.columns if 'hum' in c]
                if cols_hum: mapeo_columnas[cols_hum[0]] = 'Humedad (%)'
                
                # Buscamos 'precip' (Precipitación)
                cols_prec = [c for c in df_t.columns if 'precip' in c]
                if cols_prec: mapeo_columnas[cols_prec[0]] = 'Precipitación (mm)'

                # Renombramos y filtramos solo lo encontrado
                df_clean = df_t[list(mapeo_columnas.keys())].rename(columns=mapeo_columnas)
                
                # Conversión de fecha
                df_clean['Fecha'] = pd.to_datetime(df_clean['Fecha'], errors='coerce')
                dfs.append(df_clean)
                st.sidebar.success(f"✅ {nombre} leído")
            except Exception as e:
                st.sidebar.error(f"❌ Error en {nombre}: {e}")
    
    if not dfs: return None
    
    # Unir todo y limpiar
    df_full = pd.concat(dfs, ignore_index=True)
    df_full = df_full.dropna(subset=['Fecha']).drop_duplicates().sort_values('Fecha').reset_index(drop=True)
    
    # Convertir variables a números
    for col in df_full.columns:
        if col != 'Fecha':
            df_full[col] = pd.to_numeric(df_full[col], errors='coerce')
            
    return df_full

# Ejecución
df_base = cargar_datos_completos()

if df_base is not None and not df_base.empty:
    # --- INFO EN SIDEBAR ---
    f_min, f_max = df_base['Fecha'].min(), df_base['Fecha'].max()
    st.sidebar.divider()
    st.sidebar.info(f"📅 **Inicio:** {f_min.strftime('%d/%m/%Y %H:%M')}")
    st.sidebar.info(f"📅 **Fin Detectado:** {f_max.strftime('%d/%m/%Y %H:%M')}")
    st.sidebar.metric("Registros totales", f"{len(df_base):,}")

    # Selector de Rango
    rango = st.sidebar.date_input(
        "Periodo:",
        value=(f_max.date() - timedelta(days=7), f_max.date()),
        min_value=f_min.date(),
        max_value=f_max.date()
    )

    # 4. DASHBOARD
    if isinstance(rango, tuple) and len(rango) == 2:
        df_plot = df_base[(df_base['Fecha'].dt.date >= rango[0]) & (df_base['Fecha'].dt.date <= rango[1])]
    else:
        df_plot = df_base

    if not df_plot.empty:
        # Selector de todas las variables detectadas
        vars_disponibles = [c for c in df_plot.columns if c != 'Fecha']
        var_sel = st.selectbox("Seleccione Variable del Archivo:", vars_disponibles)

        # Métricas
        col1, col2, col3 = st.columns(3)
        col1.metric("Máximo", f"{df_plot[var_sel].max():.1f}")
        col2.metric("Mínimo", f"{df_plot[var_sel].min():.1f}")
        col3.metric("Último Registro", f"{df_plot[var_sel].iloc[-1]:.1f}")

        # Gráfico
        fig = px.line(df_plot, x='Fecha', y=var_sel, markers=True, template="plotly_white", color_discrete_sequence=['#2E7D32'])
        fig.update_xaxes(rangeslider_visible=True)
        st.plotly_chart(fig, use_container_width=True)

        # 5. DESCARGA
        st.divider()
        if st.text_input("Clave de descarga", type="password") == "santarosa2026":
            csv_data = df_plot.to_csv(index=False, sep='\t').encode('utf-8')
            st.download_button("💾 Bajar datos", csv_data, f"FCA_Export_{rango[0]}.txt")
    else:
        st.warning("No hay datos para las fechas seleccionadas.")
else:
    st.error("No se pudo extraer ninguna variable. Revisa el formato de tus archivos CSV.")

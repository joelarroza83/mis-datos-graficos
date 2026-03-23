import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime, timedelta
import os

# ==========================================
# 1. CONFIGURACIÓN DE PESTAÑA (DNS/INSTITUCIONAL)
# ==========================================
st.set_page_config(
    page_title="FCA UNA - Monitoreo Meteorológico", 
    layout="wide", 
    page_icon="🌱"
)

# ==========================================
# 2. ENCABEZADO OFICIAL
# ==========================================
try:
    logo = Image.open('logoproyecto.png')
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        st.image(logo, use_container_width=True)
    st.markdown("<h1 style='text-align: center; color: #1B5E20;'>Facultad de Ciencias Agrarias - UNA</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #388E3C;'>Estación Agrometeorológica - Filial Santa Rosa</h3>", unsafe_allow_html=True)
except:
    st.title("FCA UNA - Filial Santa Rosa")

st.divider()

# ==========================================
# 3. MOTOR DE CARGA (2025-2026)
# ==========================================
@st.cache_data(ttl=60)
def cargar_datos_fca():
    archivos = ['datos_clima2025.csv', 'datos_clima2026.csv']
    dfs = []
    
    for nombre in archivos:
        if os.path.exists(nombre):
            try:
                # Motor robusto para evitar cortes de fecha
                df_t = pd.read_csv(nombre, skiprows=3, on_bad_lines='skip', engine='python', encoding='utf-8')
                df_t.columns = [c.strip() for c in df_t.columns]
                
                # Búsqueda dinámica de la columna de tiempo
                col_tiempo = [c for c in df_t.columns if 'time' in c.lower()]
                
                if col_tiempo:
                    df_t = df_t.rename(columns={col_tiempo[0]: 'Fecha'})
                    df_t['Fecha'] = pd.to_datetime(df_t['Fecha'], errors='coerce')
                    dfs.append(df_t)
            except:
                continue
                
    if not dfs: return None
    
    df_full = pd.concat(dfs, ignore_index=True).dropna(subset=['Fecha'])
    
    # Conversión masiva de variables a números
    for col in df_full.columns:
        if col != 'Fecha':
            df_full[col] = pd.to_numeric(df_full[col], errors='coerce')
            
    return df_full.sort_values('Fecha').drop_duplicates().reset_index(drop=True)

# ==========================================
# 4. ADMIN PANEL (Contraseña: FCA2026)
# ==========================================
st.sidebar.header("🔐 Administración")
acceso = st.sidebar.text_input("Clave de Acceso:", type="password")

if acceso == "FCA2026":
    st.sidebar.success("Sesión de Administrador")
    archivo_reemplazar = st.sidebar.selectbox("Archivo a actualizar:", ["datos_clima2026.csv", "datos_clima2025.csv"])
    file_upload = st.sidebar.file_uploader(f"Cargar nuevo {archivo_reemplazar}", type=['csv'])
    
    if file_upload:
        try:
            # Validación rápida
            df_check = pd.read_csv(file_upload, skiprows=3, nrows=1)
            st.sidebar.write(f"✅ Archivo válido ({len(df_check.columns)} variables)")
            
            if st.sidebar.button("🚀 ACTUALIZAR AHORA"):
                with open(archivo_reemplazar, "wb") as f:
                    f.write(file_upload.getbuffer())
                st.sidebar.balloons()
                st.sidebar.success("OK: Base de datos actualizada.")
                st.cache_data.clear()
                st.rerun()
        except:
            st.sidebar.error("Archivo no compatible.")

st.sidebar.divider()

# ==========================================
# 5. DASHBOARD PARA EL PÚBLICO
# ==========================================
df_base = cargar_datos_fca()

if df_base is not None and not df_base.empty:
    f_min, f_max = df_base['Fecha'].min(), df_base['Fecha'].max()
    
    st.sidebar.header("📊 Información")
    st.sidebar.info(f"📅 Registros hasta: \n{f_max.strftime('%d/%m/%Y %H:%M')}")

    rango = st.sidebar.date_input(
        "Filtrar Periodo:",
        value=(f_max.date() - timedelta(days=7), f_max.date()),
        min_value=f_min.date(),
        max_value=f_max.date()
    )

    if isinstance(rango, tuple) and len(rango) == 2:
        df_filtered = df_base[(df_base['Fecha'].dt.date >= rango[0]) & (df_base['Fecha'].dt.date <= rango[1])]
        
        if not df_filtered.empty:
            # Lista de todas las variables del CSV
            todas_vars = [c for c in df_filtered.columns if c != 'Fecha']
            variable = st.selectbox("Seleccione el parámetro a visualizar:", todas_vars)

            # Métricas
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Máximo", f"{df_filtered[variable].max():.1f}")
            c2.metric("Mínimo", f"{df_filtered[variable].min():.1f}")
            c3.metric("Promedio", f"{df_filtered[variable].mean():.1f}")
            c4.metric("Último dato", f"{df_filtered[variable].iloc[-1]:.1f}")

            # Gráfico con diseño institucional
            fig = px.line(df_filtered, x='Fecha', y=variable, markers=True, template="plotly_white")
            fig.update_traces(line_color='#2E7D32', line_width=2.5)
            fig.update_xaxes(rangeslider_visible=True, title="Fecha y Hora")
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)

            # --- DESCARGA (Contraseña: santarosa2026) ---
            st.divider()
            col1, col2 = st.columns([1, 2])
            with col1:
                pw_desc = st.text_input("Clave de descarga:", type="password")
                if pw_desc == "santarosa2026":
                    csv_bytes = df_filtered.to_csv(index=False, sep='\t').encode('utf-8')
                    st.download_button(
                        label="💾 Descargar Reporte (.txt)",
                        data=csv_bytes,
                        file_name=f"FCA_SR_Reporte.txt"
                    )
        else:
            st.warning("No hay datos en ese periodo.")
else:
    st.error("⚠️ Base de datos no encontrada. Por favor, cargue los archivos CSV.")

# Pie de página institucional
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Facultad de Ciencias Agrarias - Universidad Nacional de Asunción | Santa Rosa, Paraguay</p>", unsafe_allow_html=True)

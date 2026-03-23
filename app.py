import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime, timedelta
import os

# ==========================================
# 1. CONFIGURACIÓN E IDENTIDAD (RESPONSIVO)
# ==========================================
st.set_page_config(
    page_title="Red Meteorológica FCA UNA", 
    layout="wide", 
    page_icon="🌱"
)

# Estilo CSS optimizado para Móviles y Escritorio
st.markdown("""
    <style>
    .main { background-color: #f4f7f4; }
    /* Ajuste de métricas para que no se corten en pantallas pequeñas */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 10px;
        border-left: 5px solid #2E7D32;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ENCABEZADO ---
try:
    logo = Image.open('logoproyecto.png')
    st.image(logo, width=250)
except:
    st.title("FCA UNA - Agrometeorología")

st.markdown("<h2 style='color: #1B5E20; text-align: center;'>Red de Monitoreo Agrometeorológico</h2>", unsafe_allow_html=True)
st.divider()

# ==========================================
# 2. NAVEGACIÓN POR MENÚ DESPLEGABLE
# ==========================================
st.sidebar.title("📌 Menú Principal")
opcion_principal = st.sidebar.selectbox(
    "Ir a:",
    ["📊 Estaciones Activas", "📡 Próximas Extensiones", "🔐 Panel de Administración"]
)

# ==========================================
# 3. MOTOR DE DATOS (TOLERANTE A ERRORES)
# ==========================================
@st.cache_data(ttl=60)
def cargar_datos_estacion(archivos):
    dfs = []
    for nombre in archivos:
        if os.path.exists(nombre):
            try:
                # Motor python para saltar líneas corruptas (error del 21 de marzo)
                df_t = pd.read_csv(nombre, skiprows=3, on_bad_lines='skip', engine='python', encoding='utf-8')
                df_t.columns = [c.strip() for c in df_t.columns]
                col_tiempo = [c for c in df_t.columns if 'time' in c.lower()]
                if col_tiempo:
                    df_t = df_t.rename(columns={col_tiempo[0]: 'Fecha'})
                    df_t['Fecha'] = pd.to_datetime(df_t['Fecha'], errors='coerce')
                    dfs.append(df_t)
            except: continue
    if not dfs: return None
    df_full = pd.concat(dfs, ignore_index=True).dropna(subset=['Fecha'])
    for col in df_full.columns:
        if col != 'Fecha': df_full[col] = pd.to_numeric(df_full[col], errors='coerce')
    return df_full.sort_values('Fecha').drop_duplicates().reset_index(drop=True)

# ==========================================
# 4. LÓGICA DE SECCIONES
# ==========================================

# --- SECCIÓN 1: ESTACIONES ACTIVAS ---
if opcion_principal == "📊 Estaciones Activas":
    estacion_activa = st.sidebar.selectbox("Seleccione Estación:", ["Santa Rosa (Misiones)"])
    
    if estacion_activa == "Santa Rosa (Misiones)":
        st.subheader(f"📍 Sede: {estacion_activa}")
        df = cargar_datos_estacion(['datos_clima2025.csv', 'datos_clima2026.csv'])

        if df is not None:
            f_max = df['Fecha'].max()
            
            # Selectores superiores
            col_v1, col_v2 = st.columns([1, 1])
            with col_v1:
                rango = st.date_input("Periodo:", value=(f_max.date() - timedelta(days=7), f_max.date()))
            with col_v2:
                vars_disponibles = [c for c in df.columns if c != 'Fecha']
                variable = st.selectbox("Variable:", vars_disponibles)

            if isinstance(rango, tuple) and len(rango) == 2:
                df_p = df[(df['Fecha'].dt.date >= rango[0]) & (df['Fecha'].dt.date <= rango[1])]
                
                if not df_p.empty:
                    # --- MÉTRICAS RESPONSIVAS (DISEÑO 2x2 PARA MÓVIL) ---
                    m_row1_col1, m_row1_col2 = st.columns(2)
                    m_row2_col1, m_row2_col2 = st.columns(2)

                    with m_row1_col1:
                        st.metric("Máximo", f"{df_p[variable].max():.1f}")
                    with m_row1_col2:
                        st.metric("Mínimo", f"{df_p[variable].min():.1f}")
                    with m_row2_col1:
                        st.metric("Promedio", f"{df_p[variable].mean():.1f}")
                    with m_row2_col2:
                        st.metric("Actual", f"{df_p[variable].iloc[-1]:.1f}")

                    # --- GRÁFICO OPTIMIZADO ---
                    fig = px.line(df_p, x='Fecha', y=variable, template="plotly_white", color_discrete_sequence=['#2E7D32'])
                    fig.update_layout(
                        margin=dict(l=10, r=10, t=30, b=10),
                        height=450,
                        hovermode="x unified"
                    )
                    fig.update_xaxes(rangeslider_visible=False) # Oculto para ganar espacio en móvil
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Descarga en Sidebar
                    st.sidebar.divider()
                    if st.sidebar.text_input("Clave Descarga:", type="password") == "santarosa2026":
                        csv = df_p.to_csv(index=False, sep='\t').encode('utf-8')
                        st.sidebar.download_button("💾 Bajar Datos", csv, f"FCA_{estacion_activa}.txt")
        else:
            st.info("Cargando archivos de datos...")

# --- SECCIÓN 2: PRÓXIMAS EXTENSIONES ---
elif opcion_principal == "📡 Próximas Extensiones":
    st.header("🌐 Plan de Expansión de la Red")
    sede_futura = st.selectbox(
        "Ver detalles de la Filial:",
        ["Seleccione...", "San Lorenzo (Sede Central)", "Caazapá", "San Pedro del Ycuamandiyú", 
         "Santa Rosa del Aguaray", "Pedro Juan Caballero", "Ciudad del Este"]
    )
    
    if sede_futura != "Seleccione...":
        st.success(f"### Sede: {sede_futura}")
        st.write("**Estado:** Fase de relevamiento e instalación.")
        st.write("**Próximamente:** Monitoreo en tiempo real de temperatura y humedad.")
    else:
        st.info("Seleccione una filial para conocer el estado de integración.")

# --- SECCIÓN 3: PANEL DE ADMINISTRACIÓN ---
elif opcion_principal == "🔐 Panel de Administración":
    st.header("⚙️ Gestión del Sistema")
    admin_pass = st.text_input("Clave Administrador:", type="password")
    
    if admin_pass == "FCA2026":
        st.success("Acceso Autorizado")
        target = st.selectbox("Archivo a actualizar:", ["datos_clima2026.csv", "datos_clima2025.csv"])
        u_file = st.file_uploader(f"Cargar nuevo {target}", type=['csv'])
        
        if u_file and st.button("🚀 Actualizar"):
            with open(target, "wb") as f:
                f.write(u_file.getbuffer())
            st.balloons()
            st.success("Archivo actualizado correctamente.")
            st.cache_data.clear()
            st.rerun()
    elif admin_pass != "":
        st.error("Clave incorrecta")

# Pie de página
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray; font-size: 0.8rem;'>FCA UNA | Santa Rosa - Paraguay<br>Visualización optimizada para Móviles</p>", unsafe_allow_html=True)

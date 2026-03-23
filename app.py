import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime, timedelta
import os

# ==========================================
# 1. CONFIGURACIÓN E IDENTIDAD
# ==========================================
st.set_page_config(page_title="Red Meteorológica FCA UNA", layout="wide", page_icon="🌱")

# Estética Profesional
st.markdown("""
    <style>
    .main { background-color: #f4f7f4; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #2E7D32; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- ENCABEZADO ---
try:
    logo = Image.open('logoproyecto.png')
    st.image(logo, width=300)
except:
    st.title("FCA UNA - Agrometeorología")

st.markdown("<h2 style='color: #1B5E20;'>Sistema de Monitoreo Agrometeorológico</h2>", unsafe_allow_html=True)
st.divider()

# ==========================================
# 2. NAVEGACIÓN POR MENÚ DESPLEGABLE (SIDEBAR)
# ==========================================
st.sidebar.title("📌 Menú Principal")
opcion_principal = st.sidebar.selectbox(
    "Ir a:",
    ["📊 Estaciones Activas", "📡 Próximas Extensiones", "🔐 Panel de Administración"]
)

# ==========================================
# 3. MOTOR DE DATOS
# ==========================================
@st.cache_data(ttl=60)
def cargar_datos_estacion(archivos):
    dfs = []
    for nombre in archivos:
        if os.path.exists(nombre):
            try:
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
    # Menú desplegable para elegir la estación
    estacion_activa = st.sidebar.selectbox(
        "Seleccione Estación:",
        ["Santa Rosa (Misiones)"] # Aquí agregarás más cuando estén listas
    )
    
    if estacion_activa == "Santa Rosa (Misiones)":
        st.subheader(f"📍 Estación Actual: {estacion_activa}")
        df = cargar_datos_estacion(['datos_clima2025.csv', 'datos_clima2026.csv'])

        if df is not None:
            f_max = df['Fecha'].max()
            
            # Filtros en el área principal para limpieza
            col_v1, col_v2 = st.columns([1, 1])
            with col_v1:
                rango = st.date_input("Periodo de análisis:", value=(f_max.date() - timedelta(days=7), f_max.date()))
            with col_v2:
                vars_disponibles = [c for c in df.columns if c != 'Fecha']
                variable = st.selectbox("Parámetro a visualizar:", vars_disponibles)

            if isinstance(rango, tuple) and len(rango) == 2:
                df_p = df[(df['Fecha'].dt.date >= rango[0]) & (df['Fecha'].dt.date <= rango[1])]
                
                if not df_p.empty:
                    # Métricas
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Máximo", f"{df_p[variable].max():.1f}")
                    m2.metric("Mínimo", f"{df_p[variable].min():.1f}")
                    m3.metric("Promedio", f"{df_p[variable].mean():.1f}")
                    m4.metric("Último Registro", f"{df_p[variable].iloc[-1]:.1f}")

                    # Gráfico
                    fig = px.line(df_p, x='Fecha', y=variable, template="plotly_white", color_discrete_sequence=['#2E7D32'])
                    fig.update_xaxes(rangeslider_visible=True)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Descarga en Sidebar
                    st.sidebar.divider()
                    if st.sidebar.text_input("Clave de Descarga:", type="password") == "santarosa2026":
                        csv = df_p.to_csv(index=False, sep='\t').encode('utf-8')
                        st.sidebar.download_button("💾 Descargar TXT", csv, f"FCA_{estacion_activa}.txt")
        else:
            st.info("Aguardando conexión con la base de datos...")

# --- SECCIÓN 2: PRÓXIMAS EXTENSIONES ---
elif opcion_principal == "📡 Próximas Extensiones":
    st.header("🌐 Plan de Expansión de la Red")
    
    # Menú desplegable para ver detalles de cada futura sede
    sede_futura = st.selectbox(
        "Ver detalles de la Filial:",
        [
            "Seleccione una sede...",
            "San Lorenzo (Sede Central)",
            "Caazapá",
            "San Pedro del Ycuamandiyú",
            "Santa Rosa del Aguaray",
            "Pedro Juan Caballero",
            "Ciudad del Este"
        ]
    )
    
    if sede_futura != "Seleccione una sede...":
        st.success(f"### Sede: {sede_futura}")
        st.write("**Estado del Proyecto:** Fase de relevamiento técnico e infraestructura.")
        st.write("**Objetivo:** Integración de sensores de temperatura, humedad y pluviometría en tiempo real.")
        st.image("https://via.placeholder.com/800x200.png?text=Mapa+de+Cobertura+FCA+UNA", use_container_width=True)
    else:
        st.info("Seleccione una filial del menú de arriba para ver el estado de su integración.")

# --- SECCIÓN 3: PANEL DE ADMINISTRACIÓN ---
elif opcion_principal == "🔐 Panel de Administración":
    st.header("⚙️ Configuración del Sistema")
    
    # Identificación de Admin
    with st.container():
        admin_pass = st.text_input("Contraseña de Administrador:", type="password")
        
        if admin_pass == "FCA2026":
            st.success("Acceso Autorizado")
            
            # Submenú desplegable dentro de Admin
            accion_admin = st.radio("Acción:", ["Subir Datos CSV", "Verificar Archivos Actuales"])
            
            if accion_admin == "Subir Datos CSV":
                target = st.selectbox("Archivo a reemplazar:", ["datos_clima2026.csv", "datos_clima2025.csv"])
                u_file = st.file_uploader(f"Cargar nuevo {target}", type=['csv'])
                
                if u_file and st.button(f"🚀 Ejecutar Cambio en {target}"):
                    with open(target, "wb") as f:
                        f.write(u_file.getbuffer())
                    st.balloons()
                    st.success("✅ Archivo actualizado correctamente.")
                    st.cache_data.clear()
            
            else:
                for f in ['datos_clima2025.csv', 'datos_clima2026.csv']:
                    if os.path.exists(f):
                        st.write(f"✔️ **{f}** - Último cambio: {datetime.fromtimestamp(os.path.getmtime(f)).strftime('%d/%m/%Y %H:%M')}")
                    else:
                        st.write(f"❌ **{f}** - No encontrado.")
        elif admin_pass != "":
            st.error("Clave incorrecta")

# Pie de página
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>FCA UNA | Dirección de Investigación y Extensión Universitaria</p>", unsafe_allow_html=True)

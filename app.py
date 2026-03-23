import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime, timedelta
import os

# ==========================================
# 1. CONFIGURACIÓN E IDENTIDAD (PARCHE MÓVIL)
# ==========================================
st.set_page_config(
    page_title="Red Meteorológica FCA UNA", 
    layout="wide", 
    page_icon="🌱"
)

# ESTILO CSS AVANZADO: Obliga a mostrar métricas en móvil
st.markdown("""
    <style>
    .main { background-color: #f4f7f4; }
    
    /* FUERZA LA VISIBILIDAD DE LAS MÉTRICAS EN PANTALLAS PEQUEÑAS */
    [data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
        display: block !important;
        opacity: 1 !important;
        visibility: visible !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
        display: block !important;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 5px 10px !important;
        border-radius: 8px;
        border-left: 4px solid #2E7D32;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        min-width: 100px !important;
    }
    
    /* Ajuste para que las columnas no colapsen */
    @media (max-width: 640px) {
        div[data-testid="column"] {
            width: 48% !important;
            flex: 1 1 45% !important;
            min-width: 45% !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# --- ENCABEZADO ---
try:
    logo = Image.open('logoproyecto.png')
    st.image(logo, width=220)
except:
    st.title("FCA UNA - Agrometeorología")

st.markdown("<h2 style='color: #1B5E20; text-align: center; font-size: 1.5rem;'>Sistema Meteorológico FCA UNA</h2>", unsafe_allow_html=True)
st.divider()

# ==========================================
# 2. NAVEGACIÓN
# ==========================================
st.sidebar.title("📌 Menú")
opcion_principal = st.sidebar.selectbox(
    "Ir a:",
    ["📊 Estaciones Activas", "📡 Próximas Extensiones", "🔐 Panel de Administración"]
)

# ==========================================
# 3. MOTOR DE DATOS
# ==========================================
@st.cache_data(ttl=60)
def cargar_datos_fca(archivos):
    dfs = []
    for nombre in archivos:
        if os.path.exists(nombre):
            try:
                df_t = pd.read_csv(nombre, skiprows=3, on_bad_lines='skip', engine='python', encoding='utf-8')
                df_t.columns = [c.strip() for c in df_t.columns]
                col_t = [c for c in df_t.columns if 'time' in c.lower()]
                if col_t:
                    df_t = df_t.rename(columns={col_t[0]: 'Fecha'})
                    df_t['Fecha'] = pd.to_datetime(df_t['Fecha'], errors='coerce')
                    dfs.append(df_t)
            except: continue
    if not dfs: return None
    df_f = pd.concat(dfs, ignore_index=True).dropna(subset=['Fecha'])
    for c in df_f.columns:
        if c != 'Fecha': df_f[c] = pd.to_numeric(df_f[c], errors='coerce')
    return df_f.sort_values('Fecha').drop_duplicates().reset_index(drop=True)

# ==========================================
# 4. LÓGICA DE SECCIONES
# ==========================================

if opcion_principal == "📊 Estaciones Activas":
    estacion = st.sidebar.selectbox("Sede:", ["Santa Rosa (Misiones)"])
    df = cargar_datos_fca(['datos_clima2025.csv', 'datos_clima2026.csv'])

    if df is not None:
        f_max = df['Fecha'].max()
        
        # Filtros compactos
        variable = st.selectbox("Variable:", [c for c in df.columns if c != 'Fecha'])
        rango = st.date_input("Periodo:", value=(f_max.date() - timedelta(days=7), f_max.date()))

        if isinstance(rango, tuple) and len(rango) == 2:
            df_p = df[(df['Fecha'].dt.date >= rango[0]) & (df['Fecha'].dt.date <= rango[1])]
            
            if not df_p.empty:
                # --- MÉTRICAS EN FILAS DE 2 (FUERZA BRUTA VISUAL) ---
                row1_col1, row1_col2 = st.columns(2)
                with row1_col1:
                    st.metric("Máximo", f"{df_p[variable].max():.1f}")
                with row1_col2:
                    st.metric("Mínimo", f"{df_p[variable].min():.1f}")
                
                row2_col1, row2_col2 = st.columns(2)
                with row2_col1:
                    st.metric("Promedio", f"{df_p[variable].mean():.1f}")
                with row2_col2:
                    st.metric("Actual", f"{df_p[variable].iloc[-1]:.1f}")

                # --- GRÁFICO SIN SLIDER PARA GANAR ESPACIO ---
                fig = px.line(df_p, x='Fecha', y=variable, template="plotly_white", color_discrete_sequence=['#2E7D32'])
                fig.update_layout(
                    margin=dict(l=5, r=5, t=20, b=5),
                    height=350,
                    hovermode="x"
                )
                fig.update_xaxes(rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
                
                # Descarga Segura
                st.sidebar.divider()
                if st.sidebar.text_input("Clave Descarga:", type="password") == "santarosa2026":
                    txt = df_p.to_csv(index=False, sep='\t').encode('utf-8')
                    st.sidebar.download_button("💾 Bajar TXT", txt, "FCA_Data.txt")
    else:
        st.info("Cargando datos...")

elif opcion_principal == "📡 Próximas Extensiones":
    st.header("🌐 Expansión de la Red")
    sede = st.selectbox("Filial:", ["San Lorenzo", "Caazapá", "San Pedro", "Santa Rosa Aguaray", "PJC", "CDE"])
    st.info(f"Sede {sede} en fase de planificación técnica.")

elif opcion_principal == "🔐 Panel de Administración":
    st.header("⚙️ Admin")
    if st.text_input("Clave:", type="password") == "FCA2026":
        st.success("Acceso OK")
        u_file = st.file_uploader("Actualizar CSV", type=['csv'])
        if u_file and st.button("Guardar"):
            with open("datos_clima2026.csv", "wb") as f: f.write(u_file.getbuffer())
            st.cache_data.clear()
            st.rerun()

# Pie de página
st.markdown("---")
st.markdown("<p style='text-align: center; font-size: 0.7rem;'>FCA UNA | Santa Rosa - Paraguay</p>", unsafe_allow_html=True)

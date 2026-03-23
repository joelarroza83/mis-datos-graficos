import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime, timedelta
import os

# 1. CONFIGURACIÓN
st.set_page_config(page_title="FCA UNA - Red Meteorológica", layout="wide")

# --- ESTILO CSS PARA TARJETAS MANUALES (NUEVO ENFOQUE) ---
st.markdown("""
    <style>
    .metric-container {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        justify-content: center;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: white;
        border-left: 5px solid #2E7D32;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        padding: 15px;
        width: 45%; /* Esto asegura 2 por fila en móvil */
        min-width: 140px;
        text-align: center;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #666;
        margin-bottom: 5px;
        text-transform: uppercase;
        font-weight: bold;
    }
    .metric-value {
        font-size: 1.5rem;
        color: #1B5E20;
        font-weight: bold;
    }
    @media (max-width: 480px) {
        .metric-card { width: 46%; padding: 10px; }
        .metric-value { font-size: 1.3rem; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- CABECERA ---
try:
    logo = Image.open('logoproyecto.png')
    st.image(logo, width=200)
except:
    pass

st.markdown("<h2 style='text-align: center; color: #1B5E20;'>Monitoreo FCA UNA</h2>", unsafe_allow_html=True)

# 2. MENÚ Y MOTOR DE DATOS
st.sidebar.title("Navegación")
menu = st.sidebar.selectbox("Ir a:", ["📊 Estación Santa Rosa", "📡 Sedes Futuras", "🔐 Admin"])

@st.cache_data(ttl=60)
def cargar_datos():
    archivos = ['datos_clima2025.csv', 'datos_clima2026.csv']
    dfs = []
    for f in archivos:
        if os.path.exists(f):
            try:
                df_t = pd.read_csv(f, skiprows=3, on_bad_lines='skip', engine='python')
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

# 3. PÁGINA PRINCIPAL
if menu == "📊 Estación Santa Rosa":
    df = cargar_datos()
    if df is not None:
        f_max = df['Fecha'].max()
        
        # Filtros
        var = st.selectbox("Variable:", [c for c in df.columns if c != 'Fecha'])
        rango = st.date_input("Rango:", value=(f_max.date() - timedelta(days=7), f_max.date()))
        
        df_p = df[(df['Fecha'].dt.date >= rango[0]) & (df['Fecha'].dt.date <= rango[1])]
        
        if not df_p.empty:
            # --- NUEVO SISTEMA DE MÉTRICAS EN HTML (Inmune a bloqueos) ---
            val_max = f"{df_p[var].max():.1f}"
            val_min = f"{df_p[var].min():.1f}"
            val_avg = f"{df_p[var].mean():.1f}"
            val_now = f"{df_p[var].iloc[-1]:.1f}"

            st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-card">
                        <div class="metric-label">Máximo</div>
                        <div class="metric-value">{val_max}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Mínimo</div>
                        <div class="metric-value">{val_min}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Promedio</div>
                        <div class="metric-value">{val_avg}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Actual</div>
                        <div class="metric-value">{val_now}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Gráfico optimizado para móvil
            fig = px.line(df_p, x='Fecha', y=var, template="plotly_white", color_discrete_sequence=['#2E7D32'])
            fig.update_layout(margin=dict(l=5, r=5, t=10, b=5), height=350)
            fig.update_xaxes(rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("No hay datos cargados.")

# 4. ADMIN
elif menu == "🔐 Admin":
    if st.text_input("Clave:", type="password") == "FCA2026":
        u_file = st.file_uploader("Subir CSV", type=['csv'])
        if u_file and st.button("Guardar"):
            with open("datos_clima2026.csv", "wb") as f: f.write(u_file.getbuffer())
            st.cache_data.clear()
            st.rerun()

# 5. SEDES
elif menu == "📡 Sedes Futuras":
    st.info("Próximamente: San Lorenzo, Caazapá, Ciudad del Este.")

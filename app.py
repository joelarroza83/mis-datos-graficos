import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime, timedelta
import os

# ==========================================
# 1. CONFIGURACIÓN E IDENTIDAD
# ==========================================
st.set_page_config(page_title="FCA UNA - Santa Rosa", layout="wide", page_icon="🌱")

# --- ESTILO CSS ACTUALIZADO ---
st.markdown("""
    <style>
    .main { background-color: #f4f7f4; }
    
    /* Resalte de la Sede en la parte superior */
    .sede-badge {
        background-color: #E8F5E9;
        border: 2px solid #1B5E20;
        color: #1B5E20;
        padding: 10px;
        border-radius: 50px;
        text-align: center;
        font-weight: bold;
        font-size: 1.2rem;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* Tarjetas de Datos Personalizadas */
    .metric-container {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        justify-content: center;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: white;
        border-left: 6px solid #1B5E20;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        padding: 20px;
        width: 45%; 
        min-width: 150px;
        text-align: center;
    }
    .metric-value {
        font-size: 1.8rem;
        color: #1B5E20;
        font-weight: 800;
    }
    
    /* Pie de página técnico */
    .footer-tecnico {
        text-align: center;
        color: #555;
        font-size: 0.85rem;
        padding: 20px;
        background-color: #e8eee8;
        border-top: 2px solid #1B5E20;
        margin-top: 40px;
    }

    @media (max-width: 480px) {
        .metric-card { width: 46%; padding: 15px; }
        .metric-value { font-size: 1.4rem; }
        .sede-badge { font-size: 1rem; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- ENCABEZADO Y LOGO ---
col_l1, col_l2, col_l3 = st.columns([1, 4, 1])
with col_l2:
    try:
        logo = Image.open('logoproyecto.png')
        st.image(logo, use_container_width=True)
    except:
        st.title("FCA UNA")

# --- RESALTE DE LA SEDE (NUEVO) ---
st.markdown('<div class="sede-badge">📍 SEDE SANTA ROSA - MISIONES</div>', unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center; color: #1B5E20; margin-top:-10px;'>Red de Monitoreo Agrometeorológico</h2>", unsafe_allow_html=True)
st.divider()

# ==========================================
# 2. NAVEGACIÓN Y MOTOR DE DATOS
# ==========================================
st.sidebar.title("📌 Navegación")
menu = st.sidebar.selectbox("Ir a:", ["📊 Estación Santa Rosa", "📡 Sedes Futuras", "🔐 Panel de Administración"])

@st.cache_data(ttl=60)
def cargar_datos_fca():
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

# ==========================================
# 3. CONTENIDO PRINCIPAL
# ==========================================
if menu == "📊 Estación Santa Rosa":
    df = cargar_datos_fca()
    if df is not None:
        f_max = df['Fecha'].max()
        
        c1, c2 = st.columns(2)
        with c1:
            var_sel = st.selectbox("Variable:", [c for c in df.columns if c != 'Fecha'])
        with c2:
            rango = st.date_input("Periodo:", value=(f_max.date() - timedelta(days=7), f_max.date()))
        
        df_p = df[(df['Fecha'].dt.date >= rango[0]) & (df['Fecha'].dt.date <= rango[1])]
        
        if not df_p.empty:
            # MÉTRICAS HTML
            st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-card"><div style="font-size:0.8rem; font-weight:bold;">MÁXIMO</div><div class="metric-value">{df_p[var_sel].max():.1f}</div></div>
                    <div class="metric-card"><div style="font-size:0.8rem; font-weight:bold;">MÍNIMO</div><div class="metric-value">{df_p[var_sel].min():.1f}</div></div>
                    <div class="metric-card"><div style="font-size:0.8rem; font-weight:bold;">PROMEDIO</div><div class="metric-value">{df_p[var_sel].mean():.1f}</div></div>
                    <div class="metric-card"><div style="font-size:0.8rem; font-weight:bold;">ACTUAL</div><div class="metric-value">{df_p[var_sel].iloc[-1]:.1f}</div></div>
                </div>
            """, unsafe_allow_html=True)

            fig = px.line(df_p, x='Fecha', y=var_sel, template="plotly_white", color_discrete_sequence=['#2E7D32'])
            fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=400)
            fig.update_xaxes(rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # DESCARGA PROTEGIDA
            st.markdown("### 📥 Descarga de Datos")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                clave = st.text_input("Contraseña (santarosa2026):", type="password")
            with col_d2:
                st.write("")
                st.write("")
                if clave == "santarosa2026":
                    csv_data = df_p.to_csv(index=False, sep='\t').encode('utf-8')
                    st.download_button("💾 Bajar archivo .txt", csv_data, f"FCA_SR_{var_sel}.txt")

# ==========================================
# 4. ADMIN Y FOOTER
# ==========================================
elif menu == "🔐 Panel de Administración":
    if st.text_input("Clave Admin:", type="password") == "FCA2026":
        target = st.selectbox("Archivo:", ["datos_clima2026.csv", "datos_clima2025.csv"])
        u_file = st.file_uploader("Subir CSV", type=['csv'])
        if u_file and st.button("🚀 Actualizar"):
            with open(target, "wb") as f: f.write(u_file.getbuffer())
            st.cache_data.clear()
            st.rerun()

elif menu == "📡 Sedes Futuras":
    st.info("Próximamente: San Lorenzo, Caazapá, Ciudad del Este, San Pedro, PJC.")

st.markdown(f"""
    <div class="footer-tecnico">
        <p><b>Facultad de Ciencias Agrarias - Universidad Nacional de Asunción</b></p>
        <p>Sistema desarrollado con <b>Python</b>, Pandas y Streamlit | © {datetime.now().year}</p>
    </div>
""", unsafe_allow_html=True)

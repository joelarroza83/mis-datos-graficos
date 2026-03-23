import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime, timedelta
import os

# ==========================================
# 1. CONFIGURACIÓN E IDENTIDAD
# ==========================================
st.set_page_config(page_title="FCA UNA - Red Meteorológica", layout="wide", page_icon="🌱")

# --- ESTILO CSS (TARJETAS + LOGO + FOOTER) ---
st.markdown("""
    <style>
    .main { background-color: #f4f7f4; }
    
    /* Tarjetas de Datos Personalizadas */
    .metric-container {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        justify-content: center;
        margin-top: 20px;
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
    .metric-label {
        font-size: 0.85rem;
        color: #555;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: bold;
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
        border-radius: 10px 10px 0 0;
    }

    @media (max-width: 480px) {
        .metric-card { width: 46%; padding: 15px; }
        .metric-value { font-size: 1.4rem; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- ENCABEZADO CON LOGO AGRANDADO ---
col_logo_1, col_logo_2, col_logo_3 = st.columns([1, 4, 1])
with col_logo_2:
    try:
        logo = Image.open('logoproyecto.png')
        st.image(logo, use_container_width=True) # Se ajusta al ancho de la columna central
    except:
        st.title("FCA UNA - AGROMETEOROLOGÍA")

st.markdown("<h2 style='text-align: center; color: #1B5E20;'>Red de Monitoreo Agrometeorológico</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #333;'>Facultad de Ciencias Agrarias - Universidad Nacional de Asunción</p>", unsafe_allow_html=True)
st.divider()

# ==========================================
# 2. NAVEGACIÓN Y MOTOR DE DATOS
# ==========================================
st.sidebar.title("📌 Menú de Navegación")
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
        
        # Filtros de visualización
        c1, c2 = st.columns(2)
        with c1:
            var_sel = st.selectbox("Seleccione Variable:", [c for c in df.columns if c != 'Fecha'])
        with c2:
            rango = st.date_input("Periodo de Tiempo:", value=(f_max.date() - timedelta(days=7), f_max.date()))
        
        df_p = df[(df['Fecha'].dt.date >= rango[0]) & (df['Fecha'].dt.date <= rango[1])]
        
        if not df_p.empty:
            # --- TARJETAS HTML ---
            v_max = f"{df_p[var_sel].max():.1f}"
            v_min = f"{df_p[var_sel].min():.1f}"
            v_avg = f"{df_p[var_sel].mean():.1f}"
            v_now = f"{df_p[var_sel].iloc[-1]:.1f}"

            st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-card"><div class="metric-label">MÁXIMO</div><div class="metric-value">{v_max}</div></div>
                    <div class="metric-card"><div class="metric-label">MÍNIMO</div><div class="metric-value">{v_min}</div></div>
                    <div class="metric-card"><div class="metric-label">PROMEDIO</div><div class="metric-value">{v_avg}</div></div>
                    <div class="metric-card"><div class="metric-label">ACTUAL</div><div class="metric-value">{v_now}</div></div>
                </div>
            """, unsafe_allow_html=True)

            # --- GRÁFICO ---
            fig = px.line(df_p, x='Fecha', y=var_sel, template="plotly_white", color_discrete_sequence=['#2E7D32'])
            fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=400)
            fig.update_xaxes(rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # --- SECCIÓN DE DESCARGA PROTEGIDA ---
            st.markdown("### 📥 Descarga de Reportes")
            col_d1, col_d2 = st.columns([1, 1])
            with col_d1:
                clave_descarga = st.text_input("Ingrese contraseña para descargar:", type="password")
            with col_d2:
                st.write("") # Espaciador
                st.write("")
                if clave_descarga == "santarosa2026":
                    csv_bytes = df_p.to_csv(index=False, sep='\t').encode('utf-8')
                    st.download_button(
                        label=f"💾 Descargar Datos de {var_sel} (.txt)",
                        data=csv_bytes,
                        file_name=f"FCA_SR_{var_sel}.txt",
                        mime="text/plain"
                    )
                elif clave_descarga != "":
                    st.error("Contraseña de descarga incorrecta.")

    else:
        st.warning("⚠️ No hay datos disponibles para mostrar.")

# --- SECCIONES SECUNDARIAS ---
elif menu == "📡 Sedes Futuras":
    st.header("🌐 Plan de Expansión de la Red")
    st.write("Sedes en proceso de integración:")
    filiales = ["San Lorenzo (Sede Central)", "Caazapá", "San Pedro del Ycuamandiyú", 
                "Santa Rosa del Aguaray", "Pedro Juan Caballero", "Ciudad del Este"]
    for f in filiales:
        st.info(f"🔹 {f}")

elif menu == "🔐 Panel de Administración":
    st.header("⚙️ Gestión de Datos")
    if st.text_input("Contraseña de Administrador:", type="password") == "FCA2026":
        st.success("Acceso Autorizado")
        target = st.selectbox("Archivo a actualizar:", ["datos_clima2026.csv", "datos_clima2025.csv"])
        u_file = st.file_uploader(f"Subir nuevo {target}", type=['csv'])
        if u_file and st.button("🚀 Guardar Cambios"):
            with open(target, "wb") as f: f.write(u_file.getbuffer())
            st.cache_data.clear()
            st.rerun()

# ==========================================
# 4. PIE DE PÁGINA TÉCNICO (DETALLADO)
# ==========================================
st.markdown(f"""
    <div class="footer-tecnico">
        <p><b>Facultad de Ciencias Agrarias - Universidad Nacional de Asunción</b></p>
        <p>Sistema de Gestión Agrometeorológica | Filial Santa Rosa, Misiones</p>
        <p style="font-family: monospace; font-size: 0.75rem; margin-top:10px;">
            Desarrollado con <b>Python 3.12</b> | Librerías: <b>Pandas, Streamlit, Plotly Express</b><br>
            © {datetime.now().year} - Todos los derechos reservados
        </p>
    </div>
""", unsafe_allow_html=True)

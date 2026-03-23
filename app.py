import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime, timedelta
import os

# ==========================================
# 1. CONFIGURACIÓN E IDENTIDAD INSTITUCIONAL
# ==========================================
st.set_page_config(page_title="Red Meteorológica FCA UNA", layout="wide", page_icon="🌱")

# Estilo CSS para mejorar la legibilidad y estética
st.markdown("""
    <style>
    .main { background-color: #f9fbf9; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #e0e0e0; }
    div[data-testid="stSidebarNav"] { background-image: url('https://vignette.wikia.nocookie.net/logopedia/images/2/2c/UNA_Paraguay.png'); background-repeat: no-repeat; padding-top: 80px; background-position: 20px 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- ENCABEZADO ---
try:
    logo = Image.open('logoproyecto.png')
    col_logo_1, col_logo_2, col_logo_3 = st.columns([1, 2, 1])
    with col_logo_2:
        st.image(logo, use_container_width=True)
except:
    pass

st.markdown("<h1 style='text-align: center; color: #1B5E20;'>Red de Monitoreo Agrometeorológico</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #388E3C;'>Facultad de Ciencias Agrarias - UNA</h3>", unsafe_allow_html=True)
st.divider()

# ==========================================
# 2. SISTEMA DE NAVEGACIÓN (MENÚ)
# ==========================================
st.sidebar.title("Navegación")
menu = st.sidebar.radio(
    "Seleccione una sección:",
    ["🏠 Estación Santa Rosa (Misiones)", "📡 Próximas Extensiones", "🔐 Panel de Administración"]
)

# ==========================================
# 3. MOTOR DE CARGA DE DATOS
# ==========================================
@st.cache_data(ttl=60)
def cargar_datos(lista_archivos):
    dfs = []
    for nombre in lista_archivos:
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
# 4. LÓGICA DE PÁGINAS
# ==========================================

# --- PÁGINA: SANTA ROSA MISIONES (ACTIVA) ---
if menu == "🏠 Estación Santa Rosa (Misiones)":
    st.header("📍 Estación: Filial Santa Rosa, Misiones")
    
    archivos_sr = ['datos_clima2025.csv', 'datos_clima2026.csv']
    df = cargar_datos(archivos_sr)

    if df is not None:
        f_max = df['Fecha'].max()
        f_min = df['Fecha'].min()
        
        # Filtros en columnas
        c_sel1, c_sel2 = st.columns([1, 1])
        with c_sel1:
            rango = st.date_input("Seleccionar Periodo:", value=(f_max.date() - timedelta(days=7), f_max.date()), min_value=f_min.date(), max_value=f_max.date())
        with c_sel2:
            vars_plot = [c for c in df.columns if c != 'Fecha']
            variable = st.selectbox("Parámetro Meteorológico:", vars_plot)

        if isinstance(rango, tuple) and len(rango) == 2:
            df_p = df[(df['Fecha'].dt.date >= rango[0]) & (df['Fecha'].dt.date <= rango[1])]
            
            if not df_p.empty:
                # Métricas destacadas
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Máximo", f"{df_p[variable].max():.1f}")
                m2.metric("Mínimo", f"{df_p[variable].min():.1f}")
                m3.metric("Promedio", f"{df_p[variable].mean():.1f}")
                m4.metric("Actual (Último)", f"{df_p[variable].iloc[-1]:.1f}")

                # Gráfico interactivo
                fig = px.line(df_p, x='Fecha', y=variable, template="plotly_white", color_discrete_sequence=['#2E7D32'])
                fig.update_xaxes(rangeslider_visible=True, title="Línea de Tiempo")
                fig.update_layout(hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)
                
                # Descarga Segura
                st.sidebar.divider()
                st.sidebar.subheader("Descargar Reporte")
                if st.sidebar.text_input("Clave de Descarga:", type="password") == "santarosa2026":
                    csv_data = df_p.to_csv(index=False, sep='\t').encode('utf-8')
                    st.sidebar.download_button("💾 Bajar archivo .TXT", csv_data, f"FCA_SR_{variable}.txt")
    else:
        st.warning("⚠️ No se encontraron archivos de datos para Santa Rosa. Contacte al Administrador.")

# --- PÁGINA: PRÓXIMAS EXTENSIONES (ESTRUCTURA SOLICITADA) ---
elif menu == "📡 Próximas Extensiones":
    st.header("🌐 Expansión de la Red Agrometeorológica")
    st.info("Esta sección muestra las sedes que se integrarán próximamente al sistema centralizado.")
    
    sedes = [
        "🏢 San Lorenzo (Sede Central)",
        "🌿 Caazapá",
        "🚜 San Pedro del Ycuamandiyú",
        "🌱 Santa Rosa del Aguaray",
        "🛰️ Pedro Juan Caballero",
        "🏙️ Ciudad del Este"
    ]
    
    col_a, col_b = st.columns(2)
    for i, sede in enumerate(sedes):
        if i % 2 == 0:
            col_a.markdown(f"### {sede}")
            col_a.write("Estado: *Fase de Planificación / Instalación de Sensores*")
        else:
            col_b.markdown(f"### {sede}")
            col_b.write("Estado: *Fase de Planificación / Instalación de Sensores*")

# --- PÁGINA: PANEL DE ADMINISTRACIÓN ---
elif menu == "🔐 Panel de Administración":
    st.header("⚙️ Gestión del Administrador")
    admin_input = st.text_input("Ingrese Contraseña Maestra:", type="password")
    
    if admin_input == "FCA2026":
        st.success("✅ Acceso Autorizado como Administrador")
        
        tab1, tab2 = st.tabs(["⬆️ Cargar Datos", "📋 Estado de la Red"])
        
        with tab1:
            st.subheader("Actualizar Archivos CSV")
            archivo_a_subir = st.selectbox("Seleccione destino:", ["datos_clima2026.csv", "datos_clima2025.csv"])
            file = st.file_uploader(f"Subir nuevo {archivo_a_subir}", type=['csv'])
            
            if file:
                if st.button(f"Confirmar y Reemplazar {archivo_a_subir}"):
                    with open(archivo_a_subir, "wb") as f:
                        f.write(file.getbuffer())
                    st.balloons()
                    st.success("¡Archivo actualizado!")
                    st.cache_data.clear()
                    st.rerun()
        
        with tab2:
            st.subheader("Verificación de Archivos en Servidor")
            for f_name in ['datos_clima2025.csv', 'datos_clima2026.csv']:
                if os.path.exists(f_name):
                    t_mod = datetime.fromtimestamp(os.path.getmtime(f_name))
                    st.write(f"✔️ **{f_name}**: Actualizado el {t_mod.strftime('%d/%m/%Y %H:%M')}")
                else:
                    st.write(f"❌ **{f_name}**: No encontrado.")
    
    elif admin_input != "":
        st.error("❌ Contraseña incorrecta")

# Pie de página
st.markdown("---")
st.markdown("<p style='text-align: center; color: #777;'>FCA UNA - Facultad de Ciencias Agrarias | Universidad Nacional de Asunción<br>Santa Rosa - Misiones, Paraguay | 2026</p>", unsafe_allow_html=True)

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

# Estilo para mejorar la estética
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- ENCABEZADO ---
try:
    logo = Image.open('logoproyecto.png')
    st.image(logo, width=350)
except:
    pass

st.title("Red de Monitoreo Agrometeorológico")
st.markdown("### Facultad de Ciencias Agrarias - Universidad Nacional de Asunción")
st.divider()

# ==========================================
# 2. SISTEMA DE NAVEGACIÓN (MENÚ PRINCIPAL)
# ==========================================
# Aquí es donde puedes sumar más estaciones en el futuro
menu = st.sidebar.selectbox(
    "📍 Seleccione una Opción:",
    ["🏠 Inicio / Estación Santa Rosa", "🛰️ Próximas Estaciones", "🔐 Panel de Administración"]
)

# ==========================================
# 3. MOTOR DE DATOS (REUTILIZABLE)
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
# LÓGICA POR PÁGINA
# ==========================================

# --- PÁGINA 1: ESTACIÓN SANTA ROSA ---
if menu == "🏠 Inicio / Estación Santa Rosa":
    st.header("📍 Estación: Filial Santa Rosa, Misiones")
    
    # Lista de archivos específicos de esta estación
    archivos_sr = ['datos_clima2025.csv', 'datos_clima2026.csv']
    df = cargar_datos_estacion(archivos_sr)

    if df is not None:
        # Filtros Rápidos
        f_max = df['Fecha'].max()
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            rango = st.date_input("Periodo:", value=(f_max.date() - timedelta(days=7), f_max.date()))
        
        # Selección de Variable
        vars_disponibles = [c for c in df.columns if c != 'Fecha']
        with col_f2:
            variable = st.selectbox("Parámetro:", vars_disponibles)

        # Filtrado y Gráfico
        if isinstance(rango, tuple) and len(rango) == 2:
            df_p = df[(df['Fecha'].dt.date >= rango[0]) & (df['Fecha'].dt.date <= rango[1])]
            
            # Métricas
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Máximo", f"{df_p[variable].max():.1f}")
            c2.metric("Mínimo", f"{df_p[variable].min():.1f}")
            c3.metric("Promedio", f"{df_p[variable].mean():.1f}")
            c4.metric("Último dato", f"{df_p[variable].iloc[-1]:.1f}")

            fig = px.line(df_p, x='Fecha', y=variable, template="plotly_white", color_discrete_sequence=['#2E7D32'])
            fig.update_xaxes(rangeslider_visible=True)
            st.plotly_chart(fig, use_container_width=True)
            
            # Descarga protegida
            st.sidebar.divider()
            if st.sidebar.text_input("Clave Descarga:", type="password") == "santarosa2026":
                txt = df_p.to_csv(index=False, sep='\t').encode('utf-8')
                st.sidebar.download_button("💾 Bajar TXT", txt, f"SR_{variable}.txt")
    else:
        st.info("Cargando datos de la estación...")

# --- PÁGINA 2: PRÓXIMAS ESTACIONES ---
elif menu == "🛰️ Próximas Estaciones":
    st.header("Expansión de la Red")
    st.write("Próximamente se integrarán datos de las siguientes filiales:")
    st.info("🔹 Filial San Juan Bautista")
    st.info("🔹 Filial Ayolas")
    st.info("🔹 Casa Matriz - San Lorenzo")

# --- PÁGINA 3: PANEL DE ADMINISTRACIÓN ---
elif menu == "🔐 Panel de Administración":
    st.header("⚙️ Gestión de Base de Datos")
    pw = st.text_input("Ingrese Contraseña de Administrador:", type="password")
    
    if pw == "FCA2026":
        st.success("Acceso Confirmado")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Subir Archivo (.csv)")
            estacion_sel = st.selectbox("Estación a actualizar:", ["Santa Rosa (2026)", "Santa Rosa (2025)"])
            archivo_final = "datos_clima2026.csv" if "2026" in estacion_sel else "datos_clima2025.csv"
            
            f_nueva = st.file_uploader(f"Seleccione el nuevo {archivo_final}", type=['csv'])
            
            if f_nueva:
                if st.button(f"🚀 Reemplazar {archivo_final}"):
                    with open(archivo_final, "wb") as f:
                        f.write(f_nueva.getbuffer())
                    st.balloons()
                    st.success("✅ ¡Archivo reemplazado con éxito!")
                    st.cache_data.clear()
        
        with col2:
            st.subheader("Estado de Archivos")
            # Verificar si los archivos existen y mostrar su última modificación
            for f in ['datos_clima2025.csv', 'datos_clima2026.csv']:
                if os.path.exists(f):
                    mod_time = datetime.fromtimestamp(os.path.getmtime(f))
                    st.write(f"📁 **{f}**: Última actualización: {mod_time.strftime('%d/%m/%Y %H:%M')}")
                else:
                    st.write(f"❌ **{f}**: No encontrado.")
    
    elif pw != "":
        st.error("Contraseña incorrecta")

# Pie de página
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Sistema desarrollado para la Facultad de Ciencias Agrarias - UNA</p>", unsafe_allow_html=True)

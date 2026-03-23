import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime, timedelta

# 1. Configuración de la página
st.set_page_config(page_title="FCA UNA - Filial Santa Rosa", layout="wide", page_icon="🌱")

# 2. Encabezado: Logo y Títulos
try:
    # Asegúrate de que este nombre sea el mismo en GitHub
    logo = Image.open('logoproyecto.png')
    col_izq, col_centro, col_der = st.columns([0.5, 3, 0.5])
    with col_centro:
        st.image(logo, width=550)
    
    st.markdown("<h1 style='text-align: center; color: #1B5E20; margin-bottom: 0;'>Datos de la Facultad de Ciencias Agrarias UNA</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #4E342E; margin-top: 0;'>Filial Santa Rosa - Monitoreo Meteorológico</h3>", unsafe_allow_html=True)
except Exception:
    st.title("FCA UNA - Filial Santa Rosa")

st.divider()

# 3. Función de carga de datos optimizada
@st.cache_data
def cargar_datos(archivo):
    try:
        # Cargamos el CSV saltando el encabezado técnico de Open-Meteo
        df = pd.read_csv(archivo, skiprows=3)
        df.columns = [c.strip() for c in df.columns]
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'])
        return df
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return None

# --- NOMBRE DE ARCHIVO AMIGABLE ---
nombre_archivo_base = 'datos_clima.csv'

# Intentamos cargar el archivo base
df_base = cargar_datos(nombre_archivo_base)

if df_base is not None:
    # --- BARRA LATERAL ---
    st.sidebar.header("🔐 Panel Administrativo")
    admin_pass = st.sidebar.text_input("Acceso para subir datos", type="password")
    
    if admin_pass == "FCA2026":
        st.sidebar.info("Sube un archivo llamado 'datos_clima.csv' para actualizar")
        nuevo_archivo = st.sidebar.file_uploader("Actualizar base de datos", type=["csv"])
        if nuevo_archivo:
            df_base = cargar_datos(nuevo_archivo)
            st.sidebar.success("✅ Base de datos actualizada")

    st.sidebar.divider()
    st.sidebar.header("📅 Rango de Visualización")
    
    # Configuración por defecto: Últimos 7 días
    max_fecha = df_base['time'].max().date()
    min_siete_dias = max_fecha - timedelta(days=7)
    min_absoluta = df_base['time'].min().date()

    rango = st.sidebar.date_input(
        "Periodo a mostrar:",
        value=(min_siete_dias, max_fecha),
        min_value=min_absoluta,
        max_value=max_fecha
    )

    # Filtrado dinámico según el usuario
    if isinstance(rango, tuple) and len(rango) == 2:
        inicio, fin = rango
        df_filtrado = df_base[(df_base['time'].dt.date >= inicio) & (df_base['time'].dt.date <= fin)]
    else:
        df_filtrado = df_base[df_base['time'].dt.date >= min_siete_dias]
        inicio, fin = min_siete_dias, max_fecha

    # 4. DASHBOARD
    if not df_filtrado.empty:
        # Métricas principales del último momento registrado
        m1, m2, m3 = st.columns(3)
        t_act = df_filtrado.iloc[-1, 2]
        h_act = df_filtrado.iloc[-1, 3]
        f_act = df_filtrado['time'].iloc[-1].strftime('%H:%M hs - %d/%m/%Y')

        m1.metric("Temperatura Actual", f"{t_act} °C")
        m2.metric("Humedad Actual", f"{h_act} %")
        m3.metric("Última Lectura", f_act)

        # Gráficos
        st.subheader("📈 Análisis Agrometeorológico")
        variables = [c for c in df_filtrado.columns if c != 'time']
        sel = st.selectbox("Seleccione parámetro:", variables)
        
        fig = px.line(df_filtrado, x='time', y=sel, markers=True, template="plotly_white")
        fig.update_traces(line_color='#2E7D32', line_width=2)
        st.plotly_chart(fig, use_container_width=True)

        # 5. DESCARGA PROTEGIDA (Solo rango seleccionado)
        st.divider()
        col_info, col_pass, col_btn = st.columns([2, 1, 1])
        
        with col_info:
            st.write(f"📊 **Registros disponibles:** {len(df_filtrado)}")
            st.write(f"📅 **Rango:** {inicio} al {fin}")

        with col_pass:
            clave_descarga = st.text_input("Clave para descargar TXT", type="password", key="descarga_pass")

        with col_btn:
            if clave_descarga == "santarosa2026":
                txt_output = df_filtrado.to_csv(index=False, sep='\t').encode('utf-8')
                st.write("---")
                st.download_button(
                    label="💾 Descargar .TXT",
                    data=txt_output,
                    file_name=f'Reporte_FCA_{inicio}_a_{fin}.txt',
                    mime='text/plain',
                )
            elif clave_descarga != "":
                st.error("Clave incorrecta")
    else:
        st.warning("No hay datos en el rango de fechas seleccionado.")

else:
    st.error("⚠️ No se encontró el archivo 'datos_clima.csv'. Renombra el archivo en GitHub para continuar.")

import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime, timedelta

# 1. Configuración de la página
st.set_page_config(page_title="FCA UNA - Filial Santa Rosa", layout="wide", page_icon="🌱")

# 2. Encabezado
try:
    logo = Image.open('logoproyecto.png')
    col_izq, col_centro, col_der = st.columns([0.5, 3, 0.5])
    with col_centro:
        st.image(logo, width=500)
    st.markdown("<h1 style='text-align: center; color: #1B5E20;'>Datos de la Facultad de Ciencias Agrarias UNA</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #4E342E;'>Filial Santa Rosa - Monitoreo Meteorológico</h3>", unsafe_allow_html=True)
except:
    st.title("FCA UNA - Filial Santa Rosa")

st.divider()

# 3. FUNCIÓN DE CARGA POR FRAGMENTOS (Soluciona el problema de años divididos)
@st.cache_data
def cargar_datos(archivo):
    try:
        # Cargamos el archivo completo asegurando que no se detenga por errores de formato
        df = pd.read_csv(archivo, skiprows=3, on_bad_lines='skip', engine='python')
        df.columns = df.columns.str.strip()
        
        if 'time' in df.columns:
            # Forzamos la conversión de fecha de manera ultra-flexible
            # Esto detectará tanto 2025-01-01 como 01/01/2025
            df['time'] = pd.to_datetime(df['time'], dayfirst=True, errors='coerce')
            
            # Limpieza: eliminamos filas donde la fecha falló
            df = df.dropna(subset=['time'])
            
            # Filtro de seguridad: Solo desde 2025 hasta hoy
            fecha_limite = datetime.now() + timedelta(days=1)
            df = df[(df['time'] >= '2025-01-01') & (df['time'] <= fecha_limite)]
            
            # ORDENAMIENTO TOTAL: Esto es lo que permite "dividir" por años en el filtro
            df = df.sort_values(by='time', ascending=True).reset_index(drop=True)
            
        return df
    except Exception as e:
        st.error(f"Error de lectura en el archivo CSV: {e}")
        return None

# Carga de la base de datos
nombre_archivo_base = 'datos_clima.csv'
df_base = cargar_datos(nombre_archivo_base)

if df_base is not None and not df_base.empty:
    # --- PANEL LATERAL ---
    st.sidebar.header("🔐 Administración")
    admin_pass = st.sidebar.text_input("Acceso Administrador", type="password")
    if admin_pass == "FCA2026":
        subida = st.sidebar.file_uploader("Actualizar base CSV", type=["csv"])
        if subida:
            df_base = cargar_datos(subida)

    st.sidebar.divider()
    
    # DETECCIÓN DE AÑOS DISPONIBLES
    # Esta parte responde a tu duda: permite al usuario ver qué años hay
    años_disponibles = df_base['time'].dt.year.unique()
    st.sidebar.header("📊 Resumen de Datos")
    st.sidebar.write(f"Años detectados: **{', '.join(map(str, años_disponibles))}**")
    
    min_f = df_base['time'].min().date()
    max_f = df_base['time'].max().date()
    
    st.sidebar.info(f"Rango: {min_f.strftime('%d/%m/%Y')} al {max_f.strftime('%d/%m/%Y')}")

    # Selector de Rango (Permite elegir desde 2025 a 2026 libremente)
    rango = st.sidebar.date_input(
        "Seleccione el periodo (2025-2026):",
        value=(max_f - timedelta(days=7), max_f),
        min_value=min_f,
        max_value=max_f
    )

    # 4. FILTRADO DINÁMICO
    if isinstance(rango, tuple) and len(rango) == 2:
        inicio, fin = rango
        df_final = df_base[(df_base['time'].dt.date >= inicio) & (df_base['time'].dt.date <= fin)]
    else:
        df_final = df_base

    # 5. VISUALIZACIÓN
    if not df_final.empty:
        # Métricas
        m1, m2, m3 = st.columns(3)
        ultima = df_final.iloc[-1]
        m1.metric("Temperatura", f"{ultima.iloc[2]} °C")
        m2.metric("Humedad", f"{ultima.iloc[3]} %")
        m3.metric("Última Lectura", ultima['time'].strftime('%d/%m/%Y %H:%M'))

        # Gráfico
        st.subheader(f"📈 Visualización de Datos ({inicio} - {fin})")
        
        # Selector de variable
        vars_disp = [c for c in df_final.columns if c != 'time']
        seleccion = st.selectbox("Parámetro a graficar:", vars_disp)
        
        fig = px.line(df_final, x='time', y=seleccion, markers=True, template="plotly_white")
        fig.update_traces(line_color='#2E7D32', line_width=2)
        # Añadimos una barra deslizante abajo para navegar meses fácilmente
        fig.update_xaxes(rangeslider_visible=True)
        st.plotly_chart(fig, use_container_width=True)

        # 6. DESCARGA TXT (santarosa2026)
        st.divider()
        st.write("🔒 **Exportación de Datos Seleccionados**")
        col_p, col_b = st.columns([1, 1])
        with col_p:
            c_desc = st.text_input("Contraseña de descarga", type="password")
        with col_b:
            if c_desc == "santarosa2026":
                txt = df_final.to_csv(index=False, sep='\t').encode('utf-8')
                st.download_button(
                    label=f"💾 Descargar Rango Seleccionado ({len(df_final)} registros)",
                    data=txt,
                    file_name=f"FCA_SR_Datos_{inicio}_{fin}.txt",
                    mime="text/plain"
                )
    else:
        st.warning("No hay datos para el rango seleccionado.")
else:
    st.error("No se detectaron datos. El archivo 'datos_clima.csv' podría estar mal estructurado.")

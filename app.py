import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime, timedelta
import io

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

# 3. FUNCIÓN DE CARGA "ANTIBLOQUEO"
@st.cache_data
def cargar_datos(archivo):
    try:
        # Leemos el archivo saltando las 3 líneas de Open-Meteo
        # 'on_bad_lines' evita que se corte la lectura si hay una fila mal escrita
        df = pd.read_csv(
            archivo, 
            skiprows=3, 
            engine='python', 
            on_bad_lines='skip', 
            encoding='utf-8',
            sep=None # Detecta automáticamente si es coma o punto y coma
        )
        
        # Limpieza de nombres de columnas
        df.columns = [str(c).strip() for c in df.columns]
        
        if 'time' in df.columns:
            # Conversión de fecha ultra-flexible (ignora errores de texto)
            df['time'] = pd.to_datetime(df['time'], dayfirst=True, errors='coerce')
            
            # Eliminamos filas que no pudieron convertirse en fecha
            df = df.dropna(subset=['time'])
            
            # Filtro de Seguridad: Solo datos desde 2025 hasta hoy
            # (Esto elimina ese error de "diciembre 2026" que veíamos antes)
            fecha_maxima = datetime.now() + timedelta(days=1)
            df = df[(df['time'] >= '2025-01-01') & (df['time'] <= fecha_maxima)]
            
            # Ordenar para que el 2025 aparezca primero
            df = df.sort_values(by='time').reset_index(drop=True)
            
        return df
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
        return None

# Carga de la base de datos
nombre_archivo_base = 'datos_clima.csv'
df_base = cargar_datos(nombre_archivo_base)

if df_base is not None and not df_base.empty:
    # --- PANEL LATERAL ---
    st.sidebar.header("🔐 Administración")
    admin_pass = st.sidebar.text_input("Acceso Administrador", type="password")
    if admin_pass == "FCA2026":
        subida = st.sidebar.file_uploader("Actualizar datos_clima.csv", type=["csv"])
        if subida:
            df_base = cargar_datos(subida)

    st.sidebar.divider()
    
    # VERIFICACIÓN DE DATOS DETECTADOS
    min_f = df_base['time'].min().date()
    max_f = df_base['time'].max().date()
    total_filas = len(df_base)
    
    st.sidebar.header("📊 Resumen del Archivo")
    st.sidebar.success(f"**Inicio:** {min_f.strftime('%d/%m/%Y')}")
    st.sidebar.success(f"**Fin:** {max_f.strftime('%d/%m/%Y')}")
    st.sidebar.write(f"Total registros leídos: **{total_filas}**")

    # Selector de Rango (Por defecto: últimos 7 días)
    rango = st.sidebar.date_input(
        "Filtrar periodo a visualizar:",
        value=(max_f - timedelta(days=7), max_f),
        min_value=min_f,
        max_value=max_f
    )

    # 4. FILTRADO PARA DASHBOARD
    if isinstance(rango, tuple) and len(rango) == 2:
        inicio, fin = rango
        df_final = df_base[(df_base['time'].dt.date >= inicio) & (df_base['time'].dt.date <= fin)]
    else:
        df_final = df_base

    # 5. VISUALIZACIÓN
    if not df_final.empty:
        # Métricas
        m1, m2, m3 = st.columns(3)
        u = df_final.iloc[-1]
        m1.metric("Temperatura", f"{u.iloc[2]} °C")
        m2.metric("Humedad", f"{u.iloc[3]} %")
        m3.metric("Última Fecha", u['time'].strftime('%d/%m/%Y %H:%M'))

        # Gráfico
        st.subheader(f"📈 Gráfico Agrometeorológico ({inicio} - {fin})")
        variables = [c for c in df_final.columns if c != 'time']
        sel = st.selectbox("Parámetro:", variables)
        
        fig = px.line(df_final, x='time', y=sel, markers=True, template="plotly_white")
        fig.update_traces(line_color='#2E7D32', line_width=2)
        st.plotly_chart(fig, use_container_width=True)

        # 6. DESCARGA TXT PROTEGIDA (santarosa2026)
        st.divider()
        st.write("🔒 **Descarga de Datos Seleccionados**")
        col_p, col_b = st.columns([1, 1])
        with col_p:
            clave = st.text_input("Clave de descarga", type="password")
        with col_b:
            if clave == "santarosa2026":
                txt = df_final.to_csv(index=False, sep='\t').encode('utf-8')
                st.write("---")
                st.download_button(
                    label=f"💾 Descargar {len(df_final)} filas (.txt)",
                    data=txt,
                    file_name=f"FCA_SR_{inicio}_a_{fin}.txt",
                    mime="text/plain"
                )
    else:
        st.warning("No hay datos para este rango.")
else:
    st.error("Error crítico: El sistema no puede leer el 2025. Revisa que el archivo 'datos_clima.csv' en GitHub contenga realmente esos datos.")

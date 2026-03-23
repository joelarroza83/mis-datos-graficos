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

# 3. Función de carga con "LÓGICA DE PRECISIÓN"
@st.cache_data
def cargar_datos(archivo):
    try:
        # Cargamos saltando las líneas de Open-Meteo
        df = pd.read_csv(archivo, skiprows=3)
        df.columns = df.columns.str.strip()
        
        if 'time' in df.columns:
            # FORZAMOS el formato día-mes-año hora:minuto
            # Esto evita que se confunda 01/12 (1 de dic) con 12/01 (12 de ene)
            df['time'] = pd.to_datetime(df['time'], dayfirst=True, errors='coerce')
            
            # Limpiamos datos que no tengan fecha válida
            df = df.dropna(subset=['time'])
            
            # FILTRO CRÍTICO: Eliminamos cualquier dato posterior a HOY
            fecha_hoy = datetime.now()
            df = df[df['time'] <= fecha_hoy]
            
            # Ordenamos cronológicamente (Importante para que 2025 vaya primero)
            df = df.sort_values(by='time').reset_index(drop=True)
            
        return df
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
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
    
    # Verificación de rango real en la barra lateral
    min_f = df_base['time'].min().date()
    max_f = df_base['time'].max().date()
    
    st.sidebar.header("📅 Periodo de Datos")
    st.sidebar.info(f"Desde: {min_f.strftime('%d/%m/%Y')}")
    st.sidebar.info(f"Hasta: {max_f.strftime('%d/%m/%Y')}")

    # Selector de Rango (Inicia mostrando la última semana disponible)
    try:
        rango = st.sidebar.date_input(
            "Selecciona las fechas a visualizar:",
            value=(max_f - timedelta(days=7), max_f),
            min_value=min_f,
            max_value=max_f
        )
    except:
        # Fallback si el rango por defecto da problemas
        rango = (min_f, max_f)

    # 4. FILTRADO PARA GRÁFICOS
    if isinstance(rango, tuple) and len(rango) == 2:
        inicio, fin = rango
        df_final = df_base[(df_base['time'].dt.date >= inicio) & (df_base['time'].dt.date <= fin)]
    else:
        df_final = df_base # Muestra todo si no hay selección completa

    # 5. VISUALIZACIÓN
    if not df_final.empty:
        # Métricas del momento más reciente
        m1, m2, m3 = st.columns(3)
        ultima_fila = df_final.iloc[-1]
        m1.metric("Temperatura", f"{ultima_fila.iloc[2]} °C")
        m2.metric("Humedad", f"{ultima_fila.iloc[3]} %")
        m3.metric("Fecha del Registro", ultima_fila['time'].strftime('%d/%m/%Y %H:%M'))

        # Gráfico Agrometeorológico
        st.subheader(f"📈 Análisis del Periodo: {inicio} al {fin}")
        opciones = [c for c in df_final.columns if c != 'time']
        variable = st.selectbox("Parámetro:", opciones)
        
        fig = px.line(df_final, x='time', y=variable, markers=True, template="plotly_white")
        fig.update_traces(line_color='#2E7D32', line_width=2)
        fig.update_layout(xaxis_title="Fecha y Hora", yaxis_title=variable)
        st.plotly_chart(fig, use_container_width=True)

        # 6. DESCARGA TXT (santarosa2026)
        st.divider()
        st.write("🔒 **Descarga Protegida (Solo rango seleccionado)**")
        col_cl, col_bt = st.columns([1, 1])
        with col_cl:
            c_desc = st.text_input("Contraseña de descarga", type="password")
        with col_bt:
            if c_desc == "santarosa2026":
                txt_data = df_final.to_csv(index=False, sep='\t').encode('utf-8')
                st.download_button(
                    label=f"💾 Descargar {len(df_final)} registros en .TXT",
                    data=txt_data,
                    file_name=f"FCA_SR_Reporte_{inicio}_{fin}.txt",
                    mime="text/plain"
                )
    else:
        st.warning("No hay datos disponibles para el rango de fechas seleccionado.")
else:
    st.error("No se pudo leer la base de datos. Verifica el archivo 'datos_clima.csv'.")

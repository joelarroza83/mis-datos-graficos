import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime, timedelta

# 1. Configuración de la página
st.set_page_config(page_title="FCA UNA - Filial Santa Rosa", layout="wide", page_icon="🌱")

# 2. Encabezado institucional
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

# 3. FUNCIÓN DE CARGA "ULTRA-DETECTORA"
@st.cache_data
def cargar_datos(archivo):
    try:
        # Usamos engine='python' para mayor compatibilidad con archivos grandes
        df = pd.read_csv(archivo, skiprows=3, engine='python', sep=',')
        df.columns = df.columns.str.strip()
        
        if 'time' in df.columns:
            # Intentamos convertir fechas de forma flexible (detecta guiones y barras)
            df['time'] = pd.to_datetime(df['time'], dayfirst=True, errors='coerce')
            
            # Limpieza: eliminamos filas sin fecha y fechas futuras erróneas
            df = df.dropna(subset=['time'])
            
            # FILTRO DE SEGURIDAD: Solo fechas desde 2025 hasta HOY
            hoy = datetime.now()
            df = df[(df['time'] >= '2025-01-01') & (df['time'] <= hoy)]
            
            # ORDENAMIENTO CRÍTICO: Asegura que 2025 sea el inicio real
            df = df.sort_values(by='time', ascending=True).reset_index(drop=True)
            
        return df
    except Exception as e:
        st.error(f"Error técnico en la lectura: {e}")
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
    
    # Verificación del Rango Real
    min_f = df_base['time'].min().date()
    max_f = df_base['time'].max().date()
    
    st.sidebar.header("📅 Periodo Detectado")
    st.sidebar.success(f"**Inicio:** {min_f.strftime('%d/%m/%Y')}")
    st.sidebar.success(f"**Fin:** {max_f.strftime('%d/%m/%Y')}")
    st.sidebar.write(f"Total de registros: {len(df_base)}")

    # Selector de Rango
    rango = st.sidebar.date_input(
        "Filtrar periodo:",
        value=(max_f - timedelta(days=7), max_f),
        min_value=min_f,
        max_value=max_f
    )

    # 4. FILTRADO PARA EL DASHBOARD
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
        m3.metric("Última Actualización", ultima['time'].strftime('%d/%m/%Y %H:%M'))

        # Gráfico
        st.subheader(f"📈 Gráfico Agrometeorológico")
        variables = [c for c in df_final.columns if c != 'time']
        sel = st.selectbox("Seleccione parámetro:", variables)
        
        fig = px.line(df_final, x='time', y=sel, markers=True, template="plotly_white")
        fig.update_traces(line_color='#2E7D32', line_width=2)
        st.plotly_chart(fig, use_container_width=True)

        # 6. DESCARGA TXT (santarosa2026)
        st.divider()
        st.write("🔒 **Área de Descarga (Protegida)**")
        col_p, col_b = st.columns([1, 1])
        with col_p:
            clave = st.text_input("Contraseña de descarga", type="password")
        with col_b:
            if clave == "santarosa2026":
                txt = df_final.to_csv(index=False, sep='\t').encode('utf-8')
                st.write("---")
                st.download_button(
                    label=f"💾 Descargar reporte ({len(df_final)} filas)",
                    data=txt,
                    file_name=f"FCA_SR_{inicio}_a_{fin}.txt",
                    mime="text/plain"
                )
    else:
        st.warning("No hay datos en el rango seleccionado.")
else:
    st.error("No se detectaron datos. Revisa si el archivo en GitHub se llama exactamente 'datos_clima.csv'.")

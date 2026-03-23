import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime, timedelta

# 1. Configuración de la página
st.set_page_config(page_title="FCA UNA - Filial Santa Rosa", layout="wide", page_icon="🌱")

# 2. Encabezado: Logo y Títulos
try:
    logo = Image.open('logoproyecto.png')
    col_izq, col_centro, col_der = st.columns([0.5, 3, 0.5])
    with col_centro:
        st.image(logo, width=550)
    
    st.markdown("<h1 style='text-align: center; color: #1B5E20; margin-bottom: 0;'>Datos de la Facultad de Ciencias Agrarias UNA</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #4E342E; margin-top: 0;'>Filial Santa Rosa - Monitoreo Meteorológico</h3>", unsafe_allow_html=True)
except Exception:
    st.title("FCA UNA - Filial Santa Rosa")

st.divider()

# 3. Función de carga de datos
@st.cache_data
def cargar_datos(archivo):
    try:
        df = pd.read_csv(archivo, skiprows=3)
        df.columns = [c.strip() for c in df.columns]
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'])
        return df
    except Exception:
        return None

# Carga inicial
nombre_archivo_base = 'open-meteo-26.89S56.87W167m (1).csv'
df_base = cargar_datos(nombre_archivo_base)

if df_base is not None:
    # --- BARRA LATERAL ---
    st.sidebar.header("🔐 Administración")
    admin_pass = st.sidebar.text_input("Acceso Administrador (Subir datos)", type="password")
    
    if admin_pass == "FCA2026":
        nuevo_archivo = st.sidebar.file_uploader("Actualizar base CSV", type=["csv"])
        if nuevo_archivo:
            df_base = cargar_datos(nuevo_archivo)

    st.sidebar.divider()
    st.sidebar.header("📅 Filtro de Fechas")
    
    # Rango por defecto: Últimos 7 días
    max_fecha = df_base['time'].max().date()
    min_siete_dias = max_fecha - timedelta(days=7)
    min_absoluta = df_base['time'].min().date()

    rango = st.sidebar.date_input(
        "Seleccionar periodo:",
        value=(min_siete_dias, max_fecha),
        min_value=min_absoluta,
        max_value=max_fecha
    )

    # APLICACIÓN DEL FILTRO AL DATAFRAME
    if isinstance(rango, tuple) and len(rango) == 2:
        inicio, fin = rango
        # Filtramos el dataframe original para crear el "recorte" solicitado
        df_filtrado = df_base[(df_base['time'].dt.date >= inicio) & (df_base['time'].dt.date <= fin)]
    else:
        df_filtrado = df_base[df_base['time'].dt.date >= min_siete_dias]

    # 4. MÉTRICAS (Basadas en el último dato del rango filtrado)
    if not df_filtrado.empty:
        m1, m2, m3 = st.columns(3)
        t_act = df_filtrado.iloc[-1, 2]
        h_act = df_filtrado.iloc[-1, 3]
        f_act = df_filtrado['time'].iloc[-1].strftime('%H:%M hs - %d/%m/%Y')

        m1.metric("Temperatura", f"{t_act} °C")
        m2.metric("Humedad", f"{h_act} %")
        m3.metric("Último Registro en Rango", f_act)

        # 5. GRÁFICO (Solo del rango pulsado)
        st.subheader(f"📈 Análisis del Periodo Seleccionado")
        vars_disp = [c for c in df_filtrado.columns if c != 'time']
        sel = st.selectbox("Variable:", vars_disp)
        
        fig = px.line(df_filtrado, x='time', y=sel, markers=True, template="plotly_white")
        fig.update_traces(line_color='#2E7D32', line_width=3)
        st.plotly_chart(fig, use_container_width=True)

        # 6. TABLA Y DESCARGA PROTEGIDA (Solo datos filtrados)
        st.divider()
        col_tab, col_btn = st.columns([2, 1])
        
        with col_tab:
            st.write("📂 **Registros en el rango seleccionado**")
            st.dataframe(df_filtrado, use_container_width=True)

        with col_btn:
            st.write("🔒 **Área de Descarga (.txt)**")
            pass_descarga = st.text_input("Clave para exportar este rango", type="password")
            
            if pass_descarga == "santarosa2026":
                # La descarga usa df_filtrado, así que respeta el calendario
                txt_output = df_filtrado.to_csv(index=False, sep='\t').encode('utf-8')
                st.download_button(
                    label="💾 Descargar Rango Seleccionado",
                    data=txt_output,
                    file_name=f'FCA_SantaRosa_{inicio}_al_{fin}.txt',
                    mime='text/plain',
                )
            elif pass_descarga != "":
                st.error("Clave incorrecta")
    else:
        st.warning("No hay datos para el rango de fechas seleccionado.")

else:
    st.error("No se pudo cargar la base de datos.")

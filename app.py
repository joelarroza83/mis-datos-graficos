import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from datetime import datetime, timedelta
import os

# ==========================================
# 1. CONFIGURACIÓN Y ESTILO
# ==========================================
st.set_page_config(page_title="FCA UNA - Santa Rosa", layout="wide", page_icon="🌱")

# Ocultar menús innecesarios de Streamlit (Opcional)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. ENCABEZADO
# ==========================================
try:
    logo = Image.open('logoproyecto.png')
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.image(logo, use_container_width=True)
    st.markdown("<h1 style='text-align: center; color: #1B5E20;'>Monitoreo Meteorológico FCA UNA</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 20px;'>Filial Santa Rosa - Agrometeorología</p>", unsafe_allow_html=True)
except:
    st.title("FCA UNA - Filial Santa Rosa")

st.divider()

# ==========================================
# 3. MOTOR DE CARGA UNIVERSAL (INTELIGENTE)
# ==========================================
@st.cache_data(ttl=60)
def cargar_base_datos():
    archivos = ['datos_clima2025.csv', 'datos_clima2026.csv']
    dfs = []
    
    for nombre in archivos:
        if os.path.exists(nombre):
            try:
                # Motor python + skip bad lines para evitar el error del 21 de marzo
                df_t = pd.read_csv(nombre, skiprows=3, on_bad_lines='skip', engine='python', encoding='utf-8')
                
                # Normalizar nombres de columnas
                df_t.columns = [c.strip() for c in df_t.columns]
                
                # Identificar columna de tiempo
                col_tiempo = [c for c in df_t.columns if 'time' in c.lower()]
                
                if col_tiempo:
                    df_t = df_t.rename(columns={col_tiempo[0]: 'Fecha'})
                    df_t['Fecha'] = pd.to_datetime(df_t['Fecha'], errors='coerce')
                    dfs.append(df_t)
            except:
                continue
                
    if not dfs: return None
    
    # Unir archivos y limpiar
    df_full = pd.concat(dfs, ignore_index=True).dropna(subset=['Fecha'])
    
    # Convertir todas las variables detectadas a números
    for col in df_full.columns:
        if col != 'Fecha':
            df_full[col] = pd.to_numeric(df_full[col], errors='coerce')
            
    return df_full.sort_values('Fecha').drop_duplicates().reset_index(drop=True)

# ==========================================
# 4. PANEL DE ADMINISTRADOR (CARGA MANUAL)
# ==========================================
st.sidebar.header("🔐 Acceso Admin")
admin_pw = st.sidebar.text_input("Contraseña Administrador:", type="password")

if admin_pw == "FCA2026":
    st.sidebar.success("🔓 Modo Administrador Activo")
    st.sidebar.subheader("Actualizar Archivos")
    
    archivo_opcion = st.sidebar.selectbox("Archivo a reemplazar:", ["datos_clima2026.csv", "datos_clima2025.csv"])
    f_subido = st.sidebar.file_uploader(f"Cargar nuevo {archivo_opcion}", type=['csv'])
    
    if f_subido is not None:
        # Validación previa rápida
        try:
            test_df = pd.read_csv(f_subido, skiprows=3, nrows=5)
            st.sidebar.info(f"OK: Detectadas {len(test_df.columns)} variables.")
            
            if st.sidebar.button(f"🚀 Confirmar Reemplazo"):
                with open(archivo_opcion, "wb") as f:
                    f.write(f_subido.getbuffer())
                
                st.sidebar.balloons()
                st.sidebar.success("✅ ¡ARCHIVO ACTUALIZADO!")
                st.cache_data.clear()
                st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error en formato: {e}")

st.sidebar.divider()

# ==========================================
# 5. INTERFAZ DE USUARIO Y GRÁFICOS
# ==========================================
df_base = cargar_base_datos()

if df_base is not None and not df_base.empty:
    f_min, f_max = df_base['Fecha'].min(), df_base['Fecha'].max()
    
    # Información de estado en la barra lateral
    st.sidebar.header("📊 Estado de la Red")
    st.sidebar.write(f"**Último dato:** {f_max.strftime('%d/%m/%Y %H:%M')}")
    st.sidebar.write(f"**Total registros:** {len(df_base):,}")

    # Filtro de fecha
    rango = st.sidebar.date_input(
        "Rango de fechas:",
        value=(f_max.date() - timedelta(days=7), f_max.date()),
        min_value=f_min.date(),
        max_value=f_max.date()
    )

    if isinstance(rango, tuple) and len(rango) == 2:
        df_plot = df_base[(df_base['Fecha'].dt.date >= rango[0]) & (df_base['Fecha'].dt.date <= rango[1])]
        
        if not df_plot.empty:
            # Selector de todas las variables dinámicamente
            vars_encontradas = [c for c in df_plot.columns if c != 'Fecha']
            var_sel = st.selectbox("Seleccione la variable a visualizar:", vars_encontradas)

            # Métricas
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Máximo", f"{df_plot[var_sel].max():.1f}")
            m2.metric("Mínimo", f"{df_plot[var_sel].min():.1f}")
            m3.metric("Promedio", f"{df_plot[var_sel].mean():.1f}")
            m4.metric("Actual", f"{df_plot[var_sel].iloc[-1]:.1f}")

            # Gráfico Principal
            fig = px.line(df_plot, x='Fecha', y=var_sel, markers=True, template="plotly_white")
            fig.update_traces(line_color='#2E7D32', line_width=2)
            fig.update_xaxes(rangeslider_visible=True, title="Línea de Tiempo")
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)

            # ==========================================
            # 6. DESCARGA DE DATOS (SEGURA)
            # ==========================================
            st.divider()
            st.subheader("📥 Descarga de Reportes")
            col_pw, col_btn = st.columns([1, 1])
            
            with col_pw:
                pw_descarga = st.text_input("Ingrese clave de descarga:", type="password")
            
            with col_btn:
                st.write("") # Espaciador
                st.write("") 
                if pw_descarga == "santarosa2026":
                    csv_export = df_plot.to_csv(index=False, sep='\t').encode('utf-8')
                    st.download_button(
                        label=f"💾 Descargar {var_sel} ({len(df_plot)} filas)",
                        data=csv_export,
                        file_name=f"FCA_SR_{var_sel}_{rango[0]}.txt",
                        mime="text/plain"
                    )
                elif pw_descarga != "":
                    st.warning("Clave incorrecta")

        else:
            st.warning("No hay datos para el periodo seleccionado.")
else:
    st.warning("⚠️ No se encontraron datos. Por favor, use el modo Administrador para subir los archivos CSV.")

# Pie de página
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Sistema de Monitoreo Agrometeorológico - FCA UNA Santa Rosa © 2026</p>", unsafe_allow_html=True)

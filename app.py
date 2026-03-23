import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Monitor de Datos", layout="wide")

st.title("📊 Mi Panel de Control de Datos")

# Función para cargar datos
def cargar_datos():
    # CAMBIA 'tu_archivo.csv' por el nombre exacto de tu archivo
    df = pd.read_csv('tu_archivo.csv') 
    # Intentamos detectar la columna de tiempo automáticamente
    for col in df.columns:
        if 'hora' in col.lower() or 'fecha' in col.lower() or 'time' in col.lower():
            df[col] = pd.to_datetime(df[col])
    return df

try:
    df = cargar_datos()
    
    # Mostrar la tabla
    st.subheader("Datos actuales")
    st.write(df.head(10)) # Muestra las primeras 10 filas

    # Crear gráfico
    st.subheader("Gráfico Dinámico")
    columnas = df.columns.tolist()
    
    eje_x = st.selectbox("Selecciona el eje X (Tiempo/Hora):", columnas)
    eje_y = st.selectbox("Selecciona el dato a graficar (Eje Y):", columnas)

    fig = px.line(df, x=eje_x, y=eje_y, markers=True)
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Aún no encuentro el archivo o tiene un error: {e}")

# -*- coding: utf-8 -*-
"""
Dashboard Interactivo - Proyecto 1 Materiales II
Influencia de la temperatura de ensayo en el límite de fluencia
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Proyecto 1 - Materiales II",
    layout="wide"
)

# =====================================================================
# 1. CARGA Y LIMPIEZA DE DATOS (Igual al notebook)
# =====================================================================
@st.cache_data
def cargar_datos():
    df = pd.read_excel("MPEA_dataset.xlsx")
    
    # Identificar columnas
    col_temp = next(c for c in df.columns if "test temperature" in c.lower())
    col_ys = "PROPERTY: YS (MPa)"
    
    # Limpieza de duplicados
    df_limpio = df.drop_duplicates().copy()
    
    # Tabla de trabajo
    datos = df_limpio[["FORMULA", col_temp, col_ys]].copy()
    datos[col_temp] = pd.to_numeric(datos[col_temp], errors="coerce")
    datos[col_ys] = pd.to_numeric(datos[col_ys], errors="coerce")
    datos = datos.dropna(subset=[col_temp, col_ys])
    
    # Tabla agrupada con referencias
    columnas_ref = [
        "FORMULA",
        "PROPERTY: Processing method",
        "PROPERTY: Type of test",
        "IDENTIFIER: Reference ID",
        col_temp,
        col_ys
    ]
    datos_ref = df_limpio[columnas_ref].copy()
    datos_ref[col_temp] = pd.to_numeric(datos_ref[col_temp], errors="coerce")
    datos_ref[col_ys] = pd.to_numeric(datos_ref[col_ys], errors="coerce")
    datos_ref = datos_ref.dropna(subset=columnas_ref)
    
    return df, df_limpio, datos, datos_ref, col_temp, col_ys

df_original, df_limpio, datos, datos_ref, col_temp, col_ys = cargar_datos()

# =====================================================================
# INTERFAZ PRINCIPAL
# =====================================================================
st.title("Influencia de la temperatura de ensayo en el límite de fluencia")
st.markdown("**Proyecto 1 - Materiales II**")
st.markdown("**Pregunta de investigación:** ¿Cómo influye la temperatura de ensayo en el límite de fluencia de las aleaciones metálicas?")

st.divider()

# =====================================================================
# PESTAÑAS
# =====================================================================
tab_exploracion, tab_tendencias, tab_comparacion, tab_buscador = st.tabs([
    "Exploración inicial", 
    "Análisis general", 
    "Comparación de aleaciones",
    "Buscador de datos"
])

# =====================================================================
# PESTAÑA 1: EXPLORACIÓN INICIAL
# =====================================================================
with tab_exploracion:
    st.header("Exploración inicial y calidad del conjunto de datos")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Dimensiones de la base de datos**")
        st.write(f"Número de registros: {df_original.shape[0]}")
        st.write(f"Número de variables: {df_original.shape[1]}")
    
    with col2:
        st.write("**Valores faltantes**")
        faltantes = df_original.isnull().sum().sort_values(ascending=False)
        st.write(f"Total de valores faltantes: {faltantes.sum()}")
    
    st.subheader("Top 10 variables con más valores faltantes")
    st.dataframe(faltantes.head(10).to_frame(name="Valores faltantes"), use_container_width=True)
    
    st.subheader("Primeros 5 registros")
    st.dataframe(df_original.head(5), use_container_width=True)

# =====================================================================
# PESTAÑA 2: TENDENCIA GENERAL
# =====================================================================
with tab_tendencias:
    st.header("Análisis general de tendencias")
    st.markdown("""
    Se analizaron los grupos experimentales con al menos tres temperaturas diferentes, 
    conservando para cada grupo la composición química, el método de procesamiento, 
    el tipo de ensayo y la referencia científica.
    """)
    
    @st.cache_data
    def calcular_tendencias(datos_ref, col_temp, col_ys):
        resultados = []
        columnas_grupo = [
            "FORMULA",
            "PROPERTY: Processing method",
            "PROPERTY: Type of test",
            "IDENTIFIER: Reference ID"
        ]
        
        for clave, grupo in datos_ref.groupby(columnas_grupo):
            grupo = grupo.groupby(col_temp, as_index=False)[col_ys].mean()
            grupo = grupo.sort_values(col_temp)
            
            if len(grupo) < 3:
                continue
                
            sigma_inicial = grupo[col_ys].iloc[0]
            sigma_final = grupo[col_ys].iloc[-1]
            
            if sigma_inicial <= 0:
                continue
                
            variacion = ((sigma_final - sigma_inicial) / sigma_inicial) * 100
            
            if variacion < -5:
                tendencia = "Disminucion"
            elif variacion > 5:
                tendencia = "Aumento"
            else:
                tendencia = "Cambio menor o igual al 5%"
                
            diferencias = grupo[col_ys].diff().dropna()
            continua = (diferencias <= 0).all()
            
            resultados.append({
                "Aleacion": clave[0],
                "Procesamiento": clave[1],
                "Ensayo": clave[2],
                "Referencia": clave[3],
                "Temperaturas": len(grupo),
                "Variacion (%)": variacion,
                "Tendencia": tendencia,
                "Disminucion continua": continua
            })
            
        return pd.DataFrame(resultados)

    tabla_tendencias = calcular_tendencias(datos_ref, col_temp, col_ys)
    
    if not tabla_tendencias.empty:
        conteos = tabla_tendencias["Disminucion continua"].value_counts()
        continuos = conteos.get(True, 0)
        total = len(tabla_tendencias)
        
        st.write(f"**Total de grupos experimentales analizados:** {total}")
        st.write(f"**Disminución continua:** {continuos} grupos ({(continuos/total*100):.2f}%)")
        st.write(f"**Con aumentos intermedios:** {total-continuos} grupos ({((total-continuos)/total*100):.2f}%)")
        
        st.subheader("Tabla de clasificación de tendencias")
        st.dataframe(tabla_tendencias.round(2), use_container_width=True)
        
        # Botón para descargar (opcional, pero útil para la app)
        csv = tabla_tendencias.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Descargar tabla en CSV",
            data=csv,
            file_name="tendencias.csv",
            mime="text/csv"
        )

# =====================================================================
# PESTAÑA 3: COMPARACIÓN DE ALEACIONES
# =====================================================================
with tab_comparacion:
    st.header("Comparación del límite de fluencia de cuatro aleaciones")
    st.markdown("""
    Análisis de cuatro aleaciones bajo condiciones similares (referencia 238, ensayo de compresión), 
    para comparar su retención del límite de fluencia a diferentes temperaturas.
    """)
    
    aleaciones = [
        "Mo1 Nb1 Ta1 Ti1",
        "Nb1 Ta1 Ti1",
        "Nb1 Ta1 Ti1 W1",
        "Cr1 Mo1 Ta1 Ti1"
    ]
    
    comparacion = datos_ref[
        (datos_ref["FORMULA"].isin(aleaciones)) &
        (datos_ref["IDENTIFIER: Reference ID"] == 238) &
        (datos_ref["PROPERTY: Type of test"] == "C")
    ].copy()
    
    # --- Gráfica 1: YS vs Temperatura ---
    st.subheader("1. Influencia de la temperatura en el límite de fluencia")
    
    fig1 = px.line(
        comparacion.sort_values(col_temp),
        x=col_temp,
        y=col_ys,
        color="FORMULA",
        markers=True,
        labels={col_temp: "Temperatura de ensayo (°C)", col_ys: "Límite de fluencia (MPa)", "FORMULA": "Aleación"}
    )
    fig1.update_layout(template="plotly_white")
    st.plotly_chart(fig1, use_container_width=True)
    
    # --- Gráfica 2: Retención porcentual ---
    st.subheader("2. Retención del límite de fluencia con la temperatura")
    
    resultados_ret = []
    for formula, grupo in comparacion.groupby("FORMULA"):
        grupo = grupo.sort_values(col_temp).copy()
        sigma_inicial = grupo[col_ys].iloc[0]
        grupo["Retencion (%)"] = (grupo[col_ys] / sigma_inicial) * 100
        resultados_ret.append(grupo)
        
    df_retencion = pd.concat(resultados_ret) if resultados_ret else pd.DataFrame()
    
    if not df_retencion.empty:
        fig2 = px.line(
            df_retencion,
            x=col_temp,
            y="Retencion (%)",
            color="FORMULA",
            markers=True,
            labels={col_temp: "Temperatura de ensayo (°C)", "Retencion (%)": "Resistencia conservada (%)", "FORMULA": "Aleación"}
        )
        fig2.update_layout(template="plotly_white")
        st.plotly_chart(fig2, use_container_width=True)
        
        # --- Tabla resumen ---
        st.subheader("3. Resumen de resistencia conservada")
        resumen = []
        for formula, grupo in comparacion.groupby("FORMULA"):
            grupo = grupo.sort_values(col_temp)
            sig_ini = grupo[col_ys].iloc[0]
            sig_fin = grupo[col_ys].iloc[-1]
            perdida = ((sig_ini - sig_fin) / sig_ini) * 100
            resumen.append({
                "Aleación": formula,
                "YS inicial (MPa)": sig_ini,
                "YS final (MPa)": sig_fin,
                "Retención final (%)": 100 - perdida,
                "Pérdida (%)": perdida
            })
        st.dataframe(pd.DataFrame(resumen).round(2), use_container_width=True, hide_index=True)

# =====================================================================
# PESTAÑA 4: BUSCADOR
# =====================================================================
with tab_buscador:
    st.header("Buscador de registros")
    st.markdown("Filtra los datos seleccionando el rango de temperatura y límite de fluencia.")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        if not datos.empty:
            rango_temp = st.slider(
                "Temperatura de ensayo (°C)",
                min_value=float(datos[col_temp].min()),
                max_value=float(datos[col_temp].max()),
                value=(float(datos[col_temp].min()), float(datos[col_temp].max())),
                step=10.0
            )
    
    with col_b:
        if not datos.empty:
            rango_ys = st.slider(
                "Límite de fluencia (MPa)",
                min_value=float(datos[col_ys].min()),
                max_value=float(datos[col_ys].max()),
                value=(float(datos[col_ys].min()), float(datos[col_ys].max())),
                step=10.0
            )
            
    resultado = datos.copy()
    if not datos.empty:
        resultado = resultado[resultado[col_temp].between(*rango_temp)]
        resultado = resultado[resultado[col_ys].between(*rango_ys)]
        
    st.write(f"Registros encontrados: {len(resultado)}")
    
    if not resultado.empty:
        st.dataframe(resultado, use_container_width=True, hide_index=True)
        
        csv = resultado.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Descargar resultados (CSV)",
            data=csv,
            file_name="registros_filtrados.csv",
            mime="text/csv"
        )

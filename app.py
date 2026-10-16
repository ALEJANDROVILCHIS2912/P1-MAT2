# -*- coding: utf-8 -*-
"""
Dashboard Interactivo - Proyecto 1 Materiales II
Influencia de la temperatura de ensayo en el límite de fluencia
de aleaciones metálicas.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# =====================================================================
# CONFIGURACIÓN
# =====================================================================
st.set_page_config(
    page_title="Proyecto 1 - Materiales II",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================================
# 1. CARGA Y LIMPIEZA DE DATOS (lee XLSX)
# =====================================================================
@st.cache_data
def cargar_datos():
    # ⬇️ LECTURA DEL ARCHIVO EXCEL
    df = pd.read_excel("MPEA_dataset.xlsx")

    # Eliminar duplicados exactos (como en el notebook)
    df_limpio = df.drop_duplicates().copy()

    # Identificar columnas clave
    col_temp = next(c for c in df.columns if "test temperature" in c.lower())
    col_ys = "PROPERTY: YS (MPa)"

    # Tabla de trabajo
    datos = df_limpio[["FORMULA", col_temp, col_ys]].copy()
    datos[col_temp] = pd.to_numeric(datos[col_temp], errors="coerce")
    datos[col_ys] = pd.to_numeric(datos[col_ys], errors="coerce")
    datos = datos.dropna(subset=[col_temp, col_ys])

    return df, df_limpio, datos, col_temp, col_ys


df_original, df_limpio, datos, col_temp, col_ys = cargar_datos()

# =====================================================================
# 2. PREPARAR DATOS AGRUPADOS
# =====================================================================
@st.cache_data
def preparar_datos_agrupados(df_limpio, col_temp, col_ys):
    columnas = [
        "FORMULA",
        "PROPERTY: Processing method",
        "PROPERTY: Type of test",
        "IDENTIFIER: Reference ID",
        col_temp,
        col_ys
    ]
    datos_ref = df_limpio[columnas].copy()
    datos_ref[col_temp] = pd.to_numeric(datos_ref[col_temp], errors="coerce")
    datos_ref[col_ys] = pd.to_numeric(datos_ref[col_ys], errors="coerce")
    datos_ref = datos_ref.dropna(subset=columnas)
    return datos_ref


datos_ref = preparar_datos_agrupados(df_limpio, col_temp, col_ys)

# =====================================================================
# ENCABEZADO
# =====================================================================
st.title("🔥 Influencia de la temperatura en el límite de fluencia")
st.markdown("""
### Proyecto 1 - Materiales II  
**Pregunta de investigación:** ¿Cómo influye la temperatura de ensayo 
en el límite de fluencia de las aleaciones metálicas?
""")
st.divider()

# =====================================================================
# MÉTRICAS RÁPIDAS
# =====================================================================
col1, col2, col3, col4 = st.columns(4)
col1.metric("📊 Registros originales", len(df_original))
col2.metric("🧹 Registros sin duplicados", len(df_limpio))
col3.metric("🔬 Registros con T y YS", len(datos))
col4.metric("🧪 Aleaciones únicas", datos['FORMULA'].nunique())

st.divider()

# =====================================================================
# PESTAÑAS
# =====================================================================
tab_explora, tab_analisis, tab_comparacion, tab_buscador, tab_acerca = st.tabs([
    "📊 Exploración",
    "📈 Tendencia general",
    "🔬 Comparación de aleaciones",
    "🔍 Buscador",
    "📖 Acerca del proyecto"
])

# =====================================================================
# TAB 1: EXPLORACIÓN
# =====================================================================
with tab_explora:
    st.header("📊 Exploración inicial del dataset")

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Dimensiones")
        st.write(f"**Registros originales:** {df_original.shape[0]}")
        st.write(f"**Variables:** {df_original.shape[1]}")

    with col_b:
        st.subheader("Valores faltantes")
        faltantes = df_original.isnull().sum().sort_values(ascending=False)
        st.write(f"**Total de valores faltantes:** {faltantes.sum()}")

    st.subheader("Top 10 columnas con más valores faltantes")
    st.dataframe(
        faltantes.head(10).to_frame(name="Faltantes"),
        use_container_width=True
    )

    st.subheader("Primeros 5 registros")
    st.dataframe(df_original.head(5), use_container_width=True)

    st.info("""
    **Justificación de limpieza:** Se eliminaron únicamente los duplicados 
    exactos (20 registros). No se eliminaron registros con valores faltantes 
    en todas las columnas, sino solo los que carecían de las variables 
    necesarias para el análisis: temperatura de ensayo y límite de fluencia.
    """)

# =====================================================================
# TAB 2: TENDENCIA GENERAL
# =====================================================================
with tab_analisis:
    st.header("📈 Análisis general de tendencias")

    st.markdown("""
    Se analizaron **102 grupos experimentales** (agrupados por composición, 
    procesamiento, tipo de ensayo y referencia científica) con al menos 
    3 temperaturas diferentes.
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

            sigma_ini = grupo[col_ys].iloc[0]
            sigma_fin = grupo[col_ys].iloc[-1]

            if sigma_ini <= 0:
                continue

            variacion = ((sigma_fin - sigma_ini) / sigma_ini) * 100

            if variacion < -5:
                tendencia = "Disminución"
            elif variacion > 5:
                tendencia = "Aumento"
            else:
                tendencia = "Cambio menor al 5%"

            diferencias = grupo[col_ys].diff().dropna()
            continua = (diferencias <= 0).all()

            resultados.append({
                "Aleación": clave[0],
                "Procesamiento": clave[1],
                "Ensayo": clave[2],
                "Referencia": clave[3],
                "Temperaturas": len(grupo),
                "Variación (%)": variacion,
                "Tendencia": tendencia,
                "Disminución continua": continua
            })

        return pd.DataFrame(resultados)


    tabla_tendencias = calcular_tendencias(datos_ref, col_temp, col_ys)

    col1, col2, col3 = st.columns(3)
    total = len(tabla_tendencias)
    continuos = tabla_tendencias["Disminución continua"].sum()
    col1.metric("Grupos analizados", total)
    col2.metric("Con disminución continua", f"{continuos} ({continuos/total*100:.1f}%)")
    col3.metric("Con aumentos intermedios", f"{total-continuos} ({(total-continuos)/total*100:.1f}%)")

    fig = px.pie(
        values=[continuos, total - continuos],
        names=["Disminución continua", "Con aumentos intermedios"],
        title="Comportamiento del límite de fluencia frente al aumento de temperatura",
        color_discrete_sequence=["#2E86AB", "#F18F01"]
    )
    st.plotly_chart(fig, use_container_width=True)

    st.success(f"""
    **Hallazgo:** El 100% de los grupos presentó una disminución 
    del límite de fluencia > 5%. De estos, el {continuos/total*100:.2f}% 
    mostró una disminución continua, mientras que el {(total-continuos)/total*100:.2f}% 
    presentó aumentos intermedios.
    """)

    st.subheader("Tabla completa de tendencias")
    st.dataframe(tabla_tendencias.round(2), use_container_width=True)

    csv = tabla_tendencias.to_csv(index=False).encode('utf-8')
    st.download_button(
        "⬇️ Descargar tabla de tendencias (CSV)",
        data=csv,
        file_name="tendencias_mpea.csv",
        mime="text/csv"
    )

# =====================================================================
# TAB 3: COMPARACIÓN DE ALEACIONES
# =====================================================================
with tab_comparacion:
    st.header("🔬 Comparación de aleaciones seleccionadas")

    st.markdown("""
    Se seleccionaron 4 aleaciones de la referencia **238** 
    (Coury et al., 2019), todas ensayadas a compresión, para comparar 
    su retención del límite de fluencia a alta temperatura.
    """)

    aleaciones_disponibles = [
        "Mo1 Nb1 Ta1 Ti1",
        "Nb1 Ta1 Ti1",
        "Nb1 Ta1 Ti1 W1",
        "Cr1 Mo1 Ta1 Ti1"
    ]

    comparacion = datos_ref[
        (datos_ref["FORMULA"].isin(aleaciones_disponibles)) &
        (datos_ref["IDENTIFIER: Reference ID"] == 238) &
        (datos_ref["PROPERTY: Type of test"] == "C")
    ].copy()

    st.subheader("1️⃣ Límite de fluencia vs Temperatura")

    fig1 = px.line(
        comparacion.sort_values(col_temp),
        x=col_temp,
        y=col_ys,
        color="FORMULA",
        markers=True,
        title="Influencia de la temperatura en el límite de fluencia",
        labels={
            col_temp: "Temperatura de ensayo (°C)",
            col_ys: "Límite de fluencia (MPa)",
            "FORMULA": "Aleación"
        },
        template="plotly_white"
    )
    fig1.update_traces(line=dict(width=3), marker=dict(size=8))
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("2️⃣ Retención porcentual del límite de fluencia")

    resultados_ret = []
    for formula, grupo in comparacion.groupby("FORMULA"):
        grupo = grupo.sort_values(col_temp).copy()
        sigma_ini = grupo[col_ys].iloc[0]
        grupo["Retencion"] = (grupo[col_ys] / sigma_ini) * 100
        resultados_ret.append(grupo)

    df_retencion = pd.concat(resultados_ret)

    fig2 = px.line(
        df_retencion,
        x=col_temp,
        y="Retencion",
        color="FORMULA",
        markers=True,
        title="Resistencia conservada (%) respecto a temperatura ambiente",
        labels={
            col_temp: "Temperatura de ensayo (°C)",
            "Retencion": "Resistencia conservada (%)",
            "FORMULA": "Aleación"
        },
        template="plotly_white"
    )
    fig2.update_traces(line=dict(width=3), marker=dict(size=8))
    fig2.add_hline(y=100, line_dash="dash", line_color="gray", opacity=0.5)
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("3️⃣ Tabla resumen de retención")

    tabla_resumen = []
    for formula, grupo in comparacion.groupby("FORMULA"):
        grupo = grupo.sort_values(col_temp)
        sigma_ini = grupo[col_ys].iloc[0]
        sigma_fin = grupo[col_ys].iloc[-1]
        retencion = (sigma_fin / sigma_ini) * 100

        tabla_resumen.append({
            "Aleación": formula,
            "YS inicial (MPa)": round(sigma_ini, 1),
            "YS final (MPa)": round(sigma_fin, 1),
            "Retención (%)": round(retencion, 2),
            "Pérdida (%)": round(100 - retencion, 2)
        })

    st.dataframe(
        pd.DataFrame(tabla_resumen),
        use_container_width=True,
        hide_index=True
    )

    st.success("""
    **Hallazgo:** La aleación **Cr-Mo-Ta-Ti** presentó la mayor retención 
    (64.57%), conservando mejor su resistencia a 1000°C. Por el contrario, 
    **Nb-Ta-Ti** mostró la mayor pérdida (72.08%).
    """)

# =====================================================================
# TAB 4: BUSCADOR
# =====================================================================
with tab_buscador:
    st.header("🔍 Buscador interactivo de registros")
    st.markdown("Filtra los datos por temperatura, límite de fluencia y aleación.")

    col_a, col_b = st.columns(2)

    with col_a:
        rango_temp = st.slider(
            "Temperatura de ensayo (°C):",
            min_value=float(datos[col_temp].min()),
            max_value=float(datos[col_temp].max()),
            value=(float(datos[col_temp].min()), float(datos[col_temp].max())),
            step=10.0
        )

    with col_b:
        rango_ys = st.slider(
            "Límite de fluencia (MPa):",
            min_value=float(datos[col_ys].min()),
            max_value=float(datos[col_ys].max()),
            value=(float(datos[col_ys].min()), float(datos[col_ys].max())),
            step=10.0
        )

    formula_filtro = st.text_input("Filtrar por fórmula (ej: Mo1 Nb1 Ta1 Ti1):", "")

    resultado = datos.copy()
    resultado = resultado[resultado[col_temp].between(*rango_temp)]
    resultado = resultado[resultado[col_ys].between(*rango_ys)]
    if formula_filtro:
        resultado = resultado[
            resultado["FORMULA"].str.contains(formula_filtro, case=False, na=False)
        ]

    st.divider()
    st.success(f"🔍 Se encontraron **{len(resultado)}** registros.")

    if len(resultado) > 0:
        st.dataframe(resultado, use_container_width=True, hide_index=True)

        csv = resultado.to_csv(index=False).encode('utf-8')
        st.download_button(
            "⬇️ Descargar resultados (CSV)",
            data=csv,
            file_name="registros_filtrados.csv",
            mime="text/csv"
        )
    else:
        st.warning("No hay registros con esos filtros. Intenta ampliar los rangos.")

# =====================================================================
# TAB 5: ACERCA DEL PROYECTO
# =====================================================================
with tab_acerca:
    st.header("📖 Acerca del proyecto")

    st.subheader("🎯 Pregunta de investigación")
    st.markdown("""
    **¿Cómo influye la temperatura de ensayo en el límite de fluencia 
    de las aleaciones metálicas?**
    """)

    st.subheader("📊 Descripción del dataset")
    st.markdown(f"""
    - **Origen:** MPEA_dataset (Borg et al., 2020) - Figshare
    - **Registros originales:** {len(df_original)}
    - **Variables:** {df_original.shape[1]}
    - **Registros con T y YS disponibles:** {len(datos)}
    """)

    st.subheader("🧹 Limpieza realizada")
    st.markdown("""
    1. **Eliminación de duplicados exactos** (20 registros).  
       *Justificación:* evitar contar dos veces la misma observación experimental.
    2. **Conversión a valores numéricos** de temperatura y YS con `pd.to_numeric()`.
    3. **Eliminación de registros sin temperatura o YS.**  
       *Justificación:* son las variables indispensables para responder la pregunta.
    4. **NO se eliminaron todos los nulos** del dataset, para no perder 
       información valiosa en otras columnas.
    """)

    st.subheader("📈 Principales hallazgos")
    st.markdown("""
    - **100%** de los 102 grupos experimentales mostró una disminución 
      del límite de fluencia > 5% al aumentar la temperatura.
    - **98.04%** presentó una disminución continua (sin aumentos intermedios).
    - **1.96%** presentó comportamientos excepcionales con aumentos 
      intermedios (Al₀.₅CoCrCuFeNi y Al-Mo-Nb-Ti).
    - La aleación **Cr-Mo-Ta-Ti** conservó el **64.57%** de su resistencia 
      inicial a 1000°C, mientras que **Nb-Ta-Ti** solo el 27.92%.
    """)

    st.subheader("🔬 Interpretación desde Ingeniería de Materiales")
    st.markdown("""
    La disminución del límite de fluencia con la temperatura se explica por 
    el **movimiento de dislocaciones**: al aumentar la temperatura, la energía 
    térmica facilita que las dislocaciones superen obstáculos (solutos, 
    precipitados, bordes de grano), reduciendo el esfuerzo necesario para 
    iniciar la deformación plástica.

    A temperaturas elevadas se favorecen mecanismos como:
    - **Deslizamiento cruzado** (*cross-slip*)
    - **Recuperación** dinámica
    - **Recristalización** (según condiciones)

    Estos fenómenos contribuyen a la pérdida de resistencia observada.
    """)

    st.subheader("⚠️ Limitaciones")
    st.markdown("""
    - **Datos incompletos:** muchas propiedades tienen >50% de nulos.
    - **Diferencias entre aleaciones:** composición, procesamiento y estructura 
      cristalina varían entre grupos.
    - **Intervalos desiguales:** no todos los grupos tienen mediciones en las 
      mismas temperaturas.
    - **Temperaturas intermedias desconocidas:** el comportamiento entre 
      mediciones discretas no se puede afirmar.
    - **No universal:** los resultados aplican solo al conjunto analizado.
    """)

    st.subheader("🎓 Conclusión")
    st.markdown("""
    El análisis confirma que el aumento de la temperatura de ensayo está 
    asociado predominantemente con una **disminución del límite de fluencia** 
    en las aleaciones metálicas del dataset. Sin embargo, la magnitud de la 
    pérdida depende de cada aleación, evidenciando la influencia de la 
    composición química, la microestructura y el procesamiento.

    La aleación Cr-Mo-Ta-Ti destacó por su mayor retención de resistencia 
    a alta temperatura, lo cual resulta relevante para aplicaciones 
    estructurales en condiciones severas.
    """)

    st.subheader("📚 Referencias")
    st.markdown("""
    1. Borg, C. K. H., et al. (2020). *Expanded dataset of mechanical 
       properties and observed phases of multi-principal element alloys*. 
       Scientific Data, 7, 430.
    2. Coury, F. G., Kaufman, M., & Clarke, A. J. (2019). *Solid-solution 
       strengthening in refractory high entropy alloys*. Acta Materialia, 
       175, 66–81.
    3. Wu, P., Gan, K., Yan, D., & Li, Z. (2021). *The temperature dependence 
       of deformation behaviors in high-entropy alloys: A review*. Metals, 
       11(12), 2005.
    """)

# =====================================================================
# FOOTER
# =====================================================================
st.divider()
st.caption("🔥 Proyecto 1 - Materiales II | Análisis de datos de aleaciones metálicas")
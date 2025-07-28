import streamlit as st
import pandas as pd
import sqlite3
import os
import base64
from datetime import datetime

# Configurar interfaz
st.set_page_config(page_title="Captura de Consumo Eléctrico", layout="wide")
st.title("⚡ Captura de kW Diario")

# Selector de capturista
capturista = st.selectbox("👤 ¿Quién está capturando?", [
    "Hector Bustamante", "Jose Ochoa", "Marto Acevedo",
    "Orlando Ramirez", "Guillermo Mendoza", "Nahum Zavala"
])

# Captura de fecha
if capturista == "Jose Ochoa" or capturista == "Nahum Zavala":
    fecha_seleccionada = st.date_input("📅 Fecha de captura", value=datetime.today())
    fecha = fecha_seleccionada.strftime('%Y-%m-%d')
else:
    fecha = datetime.today().strftime('%Y-%m-%d')
    st.text_input("📅 Fecha de captura (bloqueada)", value=fecha, disabled=True)

mes_actual = fecha[:7].replace("-", "_")  # ejemplo: "2025_07"

# Datos por área
areas = {
    "Alimentador 1": 0.0,
    "Alimentador 2": 0.0,
    "Alimentador 3": 0.0,
    "Primario C1": 0.0,
    "Secundario C1": 0.0,
    "Primario y Secundario C2": 0.0,
    "Merril": 0.0,
    "Barren": 0.0,
    "Pozo 7A y 7B": 0.0,
    "Pozo 7C": None,
    "Pozo 7D": None,
    "Oficinas": 0.0,
    "Taller de Mantenimiento": 0.0
}

datos = {}
cols = st.columns(len(areas))

for i, area in enumerate(areas):
    if area in ["Pozo 7C", "Pozo 7D"]:
        with cols[i]:
            st.text_input(area, value="(Inactivo)", disabled=True)
            datos[area] = ""
    else:
        with cols[i]:
            valor = st.number_input(area, min_value=0.0, format="%.2f")
            datos[area] = "" if valor == 0.0 else valor

# Conexión SQLite
conn = sqlite3.connect("base_kw.db")
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS registros (
        fecha TEXT,
        capturista TEXT,
        alimentador1 TEXT,
        alimentador2 TEXT,
        alimentador3 TEXT,
        primario_c1 TEXT,
        secundario_c1 TEXT,
        prim_sec_c2 TEXT,
        merril TEXT,
        barren TEXT,
        pozo_7a_7b TEXT,
        pozo_7c TEXT,
        pozo_7d TEXT,
        oficinas TEXT,
        taller TEXT
    )
''')
conn.commit()

# Guardar registro con ajustes
if st.button("💾 Guardar registro"):
    primario_c1_modificado = (
        "" if datos["Primario C1"] == "" else str(f"10{datos['Primario C1']}")
    )
    prim_sec_c2_modificado = (
        "" if datos["Primario y Secundario C2"] == "" else str(f"1{datos['Primario y Secundario C2']}")
    )

    valores = [
        fecha, capturista,
        str(datos["Alimentador 1"]) if datos["Alimentador 1"] != "" else "",
        str(datos["Alimentador 2"]) if datos["Alimentador 2"] != "" else "",
        str(datos["Alimentador 3"]) if datos["Alimentador 3"] != "" else "",
        primario_c1_modificado,
        str(datos["Secundario C1"]) if datos["Secundario C1"] != "" else "",
        prim_sec_c2_modificado,
        str(datos["Merril"]) if datos["Merril"] != "" else "",
        str(datos["Barren"]) if datos["Barren"] != "" else "",
        str(datos["Pozo 7A y 7B"]) if datos["Pozo 7A y 7B"] != "" else "",
        datos["Pozo 7C"],
        datos["Pozo 7D"],
        str(datos["Oficinas"]) if datos["Oficinas"] != "" else "",
        str(datos["Taller de Mantenimiento"]) if datos["Taller de Mantenimiento"] != "" else ""
    ]

    cursor.execute('''
        INSERT INTO registros VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', valores)
    conn.commit()
    st.success("✅ Registro guardado correctamente sin ceros visibles.")

# Mostrar registros (debug opcional)
if st.checkbox("🔍 Ver registros guardados"):
    df_debug = pd.read_sql("SELECT * FROM registros", conn)
    st.write(df_debug)

# Función para generar enlace de descarga
def obtener_descarga_excel(ruta_archivo):
    with open(ruta_archivo, "rb") as f:
        contenido = f.read()
        b64 = base64.b64encode(contenido).decode()
        enlace = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{os.path.basename(ruta_archivo)}">📥 Descargar historial mensual</a>'
        return enlace

# Botón para exportar Excel
if st.button("📤 Exportar historial mensual"):
    carpeta_local = r"C:\Users\fullm\OneDrive\Escritorio\Registros_KW"
    os.makedirs(carpeta_local, exist_ok=True)

    nombre_archivo = f"historial_{mes_actual}.xlsx"
    ruta_archivo = os.path.join(carpeta_local, nombre_archivo)

    cursor.execute("SELECT * FROM registros WHERE strftime('%Y_%m', fecha) = ?", [mes_actual])
    filas = cursor.fetchall()

    if filas:
        columnas = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(filas, columns=columnas)
        df.to_excel(ruta_archivo, index=False)
        st.markdown(obtener_descarga_excel(ruta_archivo), unsafe_allow_html=True)
    else:
        st.warning("⚠️ No hay registros para ese mes.")

conn.close()



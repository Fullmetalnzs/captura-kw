import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

# Configurar interfaz
st.set_page_config(page_title="Captura de Consumo Eléctrico", layout="wide")
st.title("⚡ Captura de kW Diario")

# Fecha y usuario
from datetime import datetime

if capturista == "Jose Ochoa" or "Nahum Zavala":
    fecha_seleccionada = st.date_input("📅 Fecha de captura", value=datetime.today())
    fecha = fecha_seleccionada.strftime('%Y-%m-%d')
else:
    fecha = datetime.today().strftime('%Y-%m-%d')
    st.text_input("📅 Fecha de captura (bloqueada)", value=fecha, disabled=True)


capturista = st.selectbox("👤 ¿Quién está capturando?", [
    "Hector Bustamante", "Jose Ochoa", "Marto Acevedo",
    "Orlando Ramirez", "Guillermo Mendoza", "Nahum Zavala"
])


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
            datos[area] = st.number_input(area, min_value=0.0, format="%.2f")

# Conexión a base SQLite
conn = sqlite3.connect("base_kw.db")
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS registros (
        fecha TEXT,
        capturista TEXT,
        alimentador1 REAL,
        alimentador2 REAL,
        alimentador3 REAL,
        primario_c1 REAL,
        secundario_c1 REAL,
        prim_sec_c2 REAL,
        merril REAL,
        barren REAL,
        pozo_7a_7b REAL,
        pozo_7c TEXT,
        pozo_7d TEXT,
        oficinas REAL,
        taller REAL
    )
''')
conn.commit()

# Guardar en base de datos
if st.button("💾 Guardar registro"):
    cursor.execute('''
        INSERT INTO registros (
            fecha, capturista, alimentador1, alimentador2, alimentador3,
            primario_c1, secundario_c1, prim_sec_c2, merril, barren,
            pozo_7a_7b, pozo_7c, pozo_7d, oficinas, taller
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        fecha, capturista,
        datos["Alimentador 1"], datos["Alimentador 2"], datos["Alimentador 3"],
        datos["Primario C1"], datos["Secundario C1"], datos["Primario y Secundario C2"],
        datos["Merril"], datos["Barren"], datos["Pozo 7A y 7B"],
        datos["Pozo 7C"], datos["Pozo 7D"],
        datos["Oficinas"], datos["Taller de Mantenimiento"]
    ))
    conn.commit()
    st.success("✅ Registro guardado correctamente.")

# Exportar historial por mes
if st.button("📤 Exportar historial mensual"):
    carpeta_onedrive = os.path.expanduser("~/OneDrive/Escritorio/Registros_KW")
    os.makedirs(carpeta_onedrive, exist_ok=True)
    nombre_archivo = os.path.join(carpeta_onedrive, f"kw_historial_{mes_actual}.xlsx")

    df = pd.read_sql("SELECT * FROM registros WHERE strftime('%Y_%m', fecha) = ?", conn, params=(mes_actual,))
    df.to_excel(nombre_archivo, index=False)

    st.success(f"📁 Historial mensual exportado a:\n{nombre_archivo}")
import streamlit as st
import pandas as pd
import sqlite3
import os
import base64
from datetime import datetime

# Configurar la interfaz
st.set_page_config(page_title="Captura de Consumo Eléctrico", layout="wide")
st.title("⚡ Captura de kW Diario")

# Selector de capturista
capturista = st.selectbox("👤 ¿Quién está capturando?", [
    "Hector Bustamante", "Jose Ochoa", "Marto Acevedo",
    "Orlando Ramirez", "Guillermo Mendoza", "Nahum Zavala", "Jose Angel Carmona"
])

# Fecha de captura
if capturista in ["Jose Ochoa", "Nahum Zavala"]:
    fecha_seleccionada = st.date_input("📅 Fecha de captura", value=datetime.today())
    fecha = fecha_seleccionada.strftime('%Y-%m-%d')
else:
    fecha = datetime.today().strftime('%Y-%m-%d')
    st.text_input("📅 Fecha de captura (bloqueada)", value=fecha, disabled=True)

mes_actual = fecha[:7].replace("-", "_")  # ej: "2025_07"

# Áreas
areas = {
    "Alimentador 1": 0.0, "Alimentador 2": 0.0, "Alimentador 3": 0.0,
    "Primario C1": 0.0, "Secundario C1": 0.0, "Primario y Secundario C2": 0.0,
    "Merril": 0.0, "Barren": 0.0, "Pozo 7A y 7B": 0.0,
    "Pozo 7C": None, "Pozo 7D": None,
    "Oficinas": 0.0, "Taller de Mantenimiento": 0.0
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
            valor = st.number_input(area, min_value=0.0, format="%.2f", key=f"input_{area}")
            datos[area] = "" if valor == 0.0 else valor

# Conexión SQLite
conn = sqlite3.connect("base_kw.db")
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS registros (
        fecha TEXT,
        capturista TEXT,
        alimentador1 TEXT, alimentador2 TEXT, alimentador3 TEXT,
        primario_c1 TEXT, secundario_c1 TEXT, prim_sec_c2 TEXT,
        merril TEXT, barren TEXT, pozo_7a_7b TEXT,
        pozo_7c TEXT, pozo_7d TEXT,
        oficinas TEXT, taller TEXT
    )
''')
conn.commit()

# Guardar registro
if st.button("💾 Guardar registro"):
    primario_c1_mod = "" if datos["Primario C1"] == "" else f"10{datos['Primario C1']}"
    prim_sec_c2_mod = "" if datos["Primario y Secundario C2"] == "" else f"1{datos['Primario y Secundario C2']}"

    valores = [
        fecha, capturista,
        str(datos["Alimentador 1"]), str(datos["Alimentador 2"]), str(datos["Alimentador 3"]),
        primario_c1_mod, str(datos["Secundario C1"]), prim_sec_c2_mod,
        str(datos["Merril"]), str(datos["Barren"]), str(datos["Pozo 7A y 7B"]),
        datos["Pozo 7C"], datos["Pozo 7D"],
        str(datos["Oficinas"]), str(datos["Taller de Mantenimiento"])
    ]

    cursor.execute("INSERT INTO registros VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", valores)
    conn.commit()
    st.success("✅ Registro guardado correctamente.")

# 🛠️ Editar registros anteriores
if capturista in ["Nahum Zavala", "Jose Ochoa"]:
    st.markdown("---")
    st.subheader("✏️ Editar un registro existente")
    fecha_editar = st.date_input("Selecciona la fecha a editar", key="fecha_editar")
    fecha_str = fecha_editar.strftime('%Y-%m-%d')

    cursor.execute("SELECT * FROM registros WHERE fecha = ?", (fecha_str,))
    registro = cursor.fetchone()

    if registro:
        st.write("Registro original:", registro)
        editar_cols = st.columns(len(areas))
        datos_edit = {}

        for i, area in enumerate(areas):
            if area in ["Pozo 7C", "Pozo 7D"]:
                with editar_cols[i]:
                    st.text_input(f"{area} (Inactivo)", value="(Inactivo)", disabled=True, key=f"edit_{area}")
                    datos_edit[area] = ""
            else:
                val_actual = registro[i+2]  # saltar fecha y capturista
                with editar_cols[i]:
                    nuevo_val = st.number_input(
                        f"{area} (Editar)", min_value=0.0, format="%.2f",
                        value=float(val_actual) if val_actual not in ["", None] else 0.0,
                        key=f"edit_{area}"
                    )
                    datos_edit[area] = "" if nuevo_val == 0.0 else nuevo_val

        if st.button("🔄 Actualizar registro"):
            prim_c1_edit = "" if datos_edit["Primario C1"] == "" else f"10{datos_edit['Primario C1']}"
            prim_sec_c2_edit = "" if datos_edit["Primario y Secundario C2"] == "" else f"1{datos_edit["Primario y Secundario C2"]}"

            nuevos_valores = [
                capturista,
                str(datos_edit["Alimentador 1"]), str(datos_edit["Alimentador 2"]), str(datos_edit["Alimentador 3"]),
                prim_c1_edit, str(datos_edit["Secundario C1"]), prim_sec_c2_edit,
                str(datos_edit["Merril"]), str(datos_edit["Barren"]), str(datos_edit["Pozo 7A y 7B"]),
                datos_edit["Pozo 7C"], datos_edit["Pozo 7D"],
                str(datos_edit["Oficinas"]), str(datos_edit["Taller de Mantenimiento"]),
                fecha_str
            ]

            cursor.execute('''
                UPDATE registros SET
                    capturista=?, alimentador1=?, alimentador2=?, alimentador3=?,
                    primario_c1=?, secundario_c1=?, prim_sec_c2=?,
                    merril=?, barren=?, pozo_7a_7b=?,
                    pozo_7c=?, pozo_7d=?, oficinas=?, taller=?
                WHERE fecha=?
            ''', nuevos_valores)
            conn.commit()
            st.success("✅ Registro actualizado correctamente.")
    else:
        st.info("ℹ️ No hay registros para esa fecha.")

# 📤 Exportar historial mensual
def obtener_descarga_excel(ruta_archivo):
    with open(ruta_archivo, "rb") as f:
        contenido = f.read()
        b64 = base64.b64encode(contenido).decode()
        enlace = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{os.path.basename(ruta_archivo)}">📥 Descargar historial mensual</a>'
        return enlace

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
# 📅 Exportar mes personalizado con diseño ejecutivo
st.markdown("---")
st.markdown("## 📊 Historial por mes seleccionado")
st.markdown("Exporta registros anteriores con solo elegir el mes. El archivo se descarga en Excel con nombre ejecutivo y estructura profesional.")

# Estilo de tarjeta elegante
st.markdown("""
<div style="background-color:#f3f6fa; padding:20px; border-radius:10px; border:1px solid #d0d7de">
    <h4 style="color:#2b2b2b;">📅 Elegir mes para exportar</h4>
</div>
""", unsafe_allow_html=True)

mes_exportar = st.date_input("🗓️ Selecciona un mes", value=datetime.today(), format="YYYY-MM")
mes_exportar_str = mes_exportar.strftime('%Y_%m')

if st.button("📁 Exportar registros ejecutivos"):
    carpeta_local = r"C:\Users\fullm\OneDrive\Escritorio\Registros_KW"
    os.makedirs(carpeta_local, exist_ok=True)

    nombre_archivo = f"historial_{mes_exportar_str}.xlsx"
    ruta_archivo = os.path.join(carpeta_local, nombre_archivo)

    conn = sqlite3.connect("base_kw.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registros WHERE strftime('%Y_%m', fecha) = ?", [mes_exportar_str])
    filas = cursor.fetchall()

    if filas:
        columnas = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(filas, columns=columnas)
        df.to_excel(ruta_archivo, index=False)

        with open(ruta_archivo, "rb") as f:
            contenido = f.read()
            b64 = base64.b64encode(contenido).decode()
            enlace = f'''
            <div style="padding:10px; background-color:#d0e6ff; border-radius:8px; margin-top:15px;">
                <a style="font-weight:bold; color:#004085;" href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" 
                download="{os.path.basename(ruta_archivo)}">⬇️ Descargar historial {mes_exportar_str}</a>
            </div>
            '''
            st.markdown(enlace, unsafe_allow_html=True)
    else:
        st.warning("🚫 No se encontraron registros para ese mes.")

    conn.close()



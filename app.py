import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
from dotenv import load_dotenv
import pandas as pd
import time

# Cargar credenciales y configuración
env = os.getenv('GCP_ENV', 'local')
if env == 'local':
    load_dotenv()

credentials_dict = {
    "type": os.getenv("GCP_TYPE"),
    "project_id": os.getenv("GCP_PROJECT_ID"),
    "private_key_id": os.getenv("GCP_PRIVATE_KEY_ID"),
    "private_key": os.getenv("GCP_PRIVATE_KEY").replace('\\n', '\n'),
    "client_email": os.getenv("GCP_CLIENT_EMAIL"),
    "client_id": os.getenv("GCP_CLIENT_ID"),
    "auth_uri": os.getenv("GCP_AUTH_URI"),
    "token_uri": os.getenv("GCP_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("GCP_AUTH_PROVIDER_CERT_URL"),
    "client_x509_cert_url": os.getenv("GCP_CLIENT_CERT_URL")
}

# Guardar credenciales temporalmente para autenticación
with open("temp_credentials.json", "w") as f:
    json.dump(credentials_dict, f)

# Configuración de Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

try:
    credentials = ServiceAccountCredentials.from_json_keyfile_name("temp_credentials.json", scope)
    client = gspread.authorize(credentials)
    st.write("✅ Conexión exitosa con Google Sheets.")
except Exception as e:
    st.error(f"Error en la autenticación con Google Sheets: {e}")
    st.stop()

# Eliminar archivo temporal de credenciales para seguridad
os.remove("temp_credentials.json")

# Intentar abrir la hoja de Google
try:
    sheet_name = os.getenv("GCP_GOOGLE_SHEET_NAME")
    sheet = client.open(sheet_name).sheet1
    st.write("✅ Hoja de Google abierta correctamente.")
except Exception as e:
    st.error(f"Error al abrir la hoja de Google: {e}")
    st.stop()

# Cargar preguntas desde archivo JSON y mapearlas a "Pregunta 1", "Pregunta 2", etc.
try:
    with open("preguntas.json", "r") as file:
        survey_data = json.load(file)
except FileNotFoundError:
    st.error("No se encontró el archivo questions.json")
    st.stop()

# Crear un diccionario que asocia "Pregunta X" con el texto de cada pregunta
pregunta_map = {}
question_num = 1
for section in survey_data["sections"]:
    for question in section["questions"]:
        pregunta_map[f"Pregunta {question_num}"] = question
        question_num += 1

# Leer todas las respuestas de Google Sheets y crear un DataFrame
try:
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
except Exception as e:
    st.error(f"Error al leer los datos de Google Sheets: {e}")
    st.stop()

# Verificar si el DataFrame está vacío
if df.empty:
    st.warning("No hay respuestas almacenadas en la hoja de Google Sheets.")
else:
    # Mapear cada columna de pregunta en el DataFrame al texto completo de la pregunta
    df = df.rename(columns=pregunta_map)

    # Mostrar datos de manera amigable
    st.title("Respuestas de la Encuesta")
    st.write("Esta aplicación muestra las respuestas recopiladas en la encuesta, asociadas a cada pregunta.")

    # Seleccionar una fila específica para ver respuestas de un usuario individual
    selected_user = st.selectbox("Selecciona un usuario para ver sus respuestas:", df["Email"].unique())
    user_data = df[df["Email"] == selected_user]
    user_name =  df[df["Nombre"] == selected_user]

    # Mostrar preguntas y respuestas de ese usuario
    if not user_data.empty:
        st.subheader(f"Respuestas de {selected_user}")
        for column in user_data.columns[2:]:  # Saltar nombre y correo electrónico
            st.write(f"**{column}:** {user_data.iloc[0][column]}")
    else:
        st.write("No se encontraron respuestas para el usuario seleccionado.")

# Configurar actualización automática cada 10 segundos usando query params
refresh_interval = 10  # Intervalo en segundos para la actualización automática
st.write(f"La aplicación se actualizará automáticamente cada {refresh_interval} segundos para cargar nuevas respuestas.")

# Simular recarga automática mediante query params
time.sleep(refresh_interval)
st.query_params()

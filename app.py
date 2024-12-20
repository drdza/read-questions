import streamlit as st
import gspread
from google.oauth2 import service_account
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
from dotenv import load_dotenv
import pandas as pd
import time

st.set_page_config(
   page_title="Análisis de Datos",
   page_icon="🧊",
   layout="wide",
   initial_sidebar_state="expanded",
)

# Cargar credenciales y configuración
env = os.getenv('GCP_ENV', 'local')

# Configuración de Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

if env == 'prod':
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
    
   # Guardar credenciales temporalmente para la autenticación
   with open("temp_credentials.json", "w") as f:
      json.dump(credentials_dict, f)
   
   try:
      credentials = ServiceAccountCredentials.from_json_keyfile_name("temp_credentials.json", scope)
      client = gspread.authorize(credentials)    
      os.remove("temp_credentials.json")
   except Exception as e:
      st.error(f"Error en la autenticación - Prod: {e}")
      st.stop()
else:
   try:      
      st.write(os.getenv("GCP_GOOGLE_APPLICATION_CREDENTIALS"))     
      credentials = service_account.Credentials.from_service_account_file(os.getenv("GCP_GOOGLE_APPLICATION_CREDENTIALS"), scopes=scope)
      client = gspread.authorize(credentials)
   except Exception as e:
      st.error(f"Error en la autenticación - Local: {e}")
      st.stop()

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
   selected_user = st.selectbox("Selecciona un usuario para ver sus respuestas:", df["Nombre"].unique())
   user_data = df[df["Nombre"] == selected_user]
   user_data["Nombre"] = user_data["Nombre"]

   # Mostrar preguntas y respuestas de ese usuario
   if not user_data.empty:
      st.subheader(f"Respuestas de {selected_user}")
      for column in user_data.columns:  # Saltar nombre y correo electrónico
         st.write(f"**{column}:** {user_data.iloc[0][column]}")
   else:
      st.write("No se encontraron respuestas para el usuario seleccionado.")

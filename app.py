from dotenv import load_dotenv
import os
import streamlit as st
import pandas as pd
import google.generativeai as genai
import re
from PIL import Image
import requests



# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Configurar la API key de Google AI utilizando la variable de entorno
google_api_key = os.getenv('GOOGLE_API_KEY')


st.set_page_config(
    page_title="Google AI Chat",
    page_icon="https://seeklogo.com/images/G/google-ai-logo-996E85F6FD-seeklogo.com.png",
    layout="wide",
)
# Path: app.py
#Author: Cristian Olivares S.
#------------------------------------------------------------
#HEADER


#------------------------------------------------------------
#LANGUAGE
# Columna de idioma
lang = 'Español'
st.divider()

#------------------------------------------------------------
#FUNCTIONS
def extract_graphviz_info(text: str) -> list[str]:
  """
  The function `extract_graphviz_info` takes in a text and returns a list of graphviz code blocks found in the text.

  :param text: The `text` parameter is a string that contains the text from which you want to extract Graphviz information
  :return: a list of strings that contain either the word "graph" or "digraph". These strings are extracted from the input
  text.
  """

  graphviz_info  = text.split('```')

  return [graph for graph in graphviz_info if ('graph' in graph or 'digraph' in graph) and ('{' in graph and '}' in graph)]

def append_message(message: dict) -> None:
    """
    The function appends a message to a chat session.

    :param message: The `message` parameter is a dictionary that represents a chat message. It typically contains
    information such as the user who sent the message and the content of the message
    :type message: dict
    :return: The function is not returning anything.
    """
    st.session_state.chat_session.append({'user': message})
    return

@st.cache_resource
def load_model() -> genai.GenerativeModel:
    """
    The function `load_model()` returns an instance of the `genai.GenerativeModel` class initialized with the model name
    'gemini-2.0-flash' and configured with appropriate generation parameters.
    :return: an instance of the `genai.GenerativeModel` class.
    """
    model = genai.GenerativeModel('gemini-2.0-flash',
        generation_config={
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048
        })
    return model

@st.cache_resource
def load_modelvision() -> genai.GenerativeModel:
    """
    The function `load_modelvision` loads a generative model for vision tasks using the `gemini-2.0-flash-vision` model
    with appropriate generation and safety settings.
    :return: an instance of the `genai.GenerativeModel` class.
    """
    model = genai.GenerativeModel('gemini-2.0-flash-vision',
        generation_config={
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048
        },
        safety_settings=[
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ])
    return model



#------------------------------------------------------------
#CONFIGURATION
genai.configure(api_key=google_api_key)

model = load_model()

vision = load_modelvision()

if 'chat' not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

if 'chat_session' not in st.session_state:
    st.session_state.chat_session = []

#st.session_state.chat_session

#------------------------------------------------------------
#CHAT

if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'welcome' not in st.session_state or lang != st.session_state.lang:
    st.session_state.lang = lang
    welcome = model.generate_content(f'''
    Saluda al usuario con el siguiente mensaje:
    "¡Hola! Soy un chatbot de IA aquí para ayudarte. ¿En qué puedo ayudarte hoy? Cuéntame qué texto, guión, copy, frase radial, o cualquier otro contenido necesitas que te ayude a desarrollar para que comencemos..."
    
    Luego agrega:
    (Para ayudarte, puedo ver imágenes, responder preguntas, leer archivos de texto, leer tablas y más. ¡Solo pregunta!)
    
    Genera la respuesta en {lang}
    ''')
    welcome.resolve()
    st.session_state.welcome = welcome

    with st.chat_message('ai'):
        st.write(st.session_state.welcome.text)
else:
    with st.chat_message('ai'):
        st.write(st.session_state.welcome.text)

if len(st.session_state.chat_session) > 0:
    count = 0
    for message in st.session_state.chat_session:

        if message['user']['role'] == 'model':
            with st.chat_message('ai'):
                st.write(message['user']['parts'])
                graphs = extract_graphviz_info(message['user']['parts'])
                if len(graphs) > 0:
                    for graph in graphs:
                        st.graphviz_chart(graph,use_container_width=False)
                        if lang == 'Español':
                          view = "Ver texto"
                        else:
                          view = "View text"
                        with st.expander(view):
                          st.code(graph, language='dot')
        else:
            with st.chat_message('user'):
                st.write(message['user']['parts'][0])
                if len(message['user']['parts']) > 1:
                    st.image(message['user']['parts'][1], width=200)
        count += 1



#st.session_state.chat.history

cols=st.columns(4)

with cols[0]:
    if lang == 'Español':
      image_atachment = st.toggle("Adjuntar imagen", value=False, help="Activa este modo para adjuntar una imagen y que el chatbot pueda leerla")
    else:
      image_atachment = st.toggle("Attach image", value=False, help="Activate this mode to attach an image and let the chatbot read it")

with cols[1]:
    if lang == 'Español':
      txt_atachment = st.toggle("Adjuntar archivo de texto", value=False, help="Activa este modo para adjuntar un archivo de texto y que el chatbot pueda leerlo")
    else:
      txt_atachment = st.toggle("Attach text file", value=False, help="Activate this mode to attach a text file and let the chatbot read it")
with cols[2]:
    if lang == 'Español':
      csv_excel_atachment = st.toggle("Adjuntar CSV o Excel", value=False, help="Activa este modo para adjuntar un archivo CSV o Excel y que el chatbot pueda leerlo")
    else:
      csv_excel_atachment = st.toggle("Attach CSV or Excel", value=False, help="Activate this mode to attach a CSV or Excel file and let the chatbot read it")
with cols[3]:
    if lang == 'Español':
      graphviz_mode = st.toggle("Modo graphviz", value=False, help="Activa este modo para generar un grafo con graphviz en .dot a partir de tu mensaje")
    else:
      graphviz_mode = st.toggle("Graphviz mode", value=False, help="Activate this mode to generate a graph with graphviz in .dot from your message")
if image_atachment:
    if lang == 'Español':
      image = st.file_uploader("Sube tu imagen", type=['png', 'jpg', 'jpeg'])
      url = st.text_input("O pega la url de tu imagen")
    else:
      image = st.file_uploader("Upload your image", type=['png', 'jpg', 'jpeg'])
      url = st.text_input("Or paste your image url")
else:
    image = None
    url = ''



if txt_atachment:
    if lang == 'Español':
      txtattachment = st.file_uploader("Sube tu archivo de texto", type=['txt'])
    else:
      txtattachment = st.file_uploader("Upload your text file", type=['txt'])
else:
    txtattachment = None

if csv_excel_atachment:
    if lang == 'Español':
      csvexcelattachment = st.file_uploader("Sube tu archivo CSV o Excel", type=['csv', 'xlsx'])
    else:
      csvexcelattachment = st.file_uploader("Upload your CSV or Excel file", type=['csv', 'xlsx'])
else:
    csvexcelattachment = None
if lang == 'Español':
  prompt = st.chat_input("Escribe tu mensaje")
else:
  prompt = st.chat_input("Write your message")

if prompt:
    txt = ''
    if txtattachment:
        txt = txtattachment.getvalue().decode("utf-8")
        if lang == 'Español':
          txt = '   Archivo de texto: \n' + txt
        else:
          txt = '   Text file: \n' + txt

    if csvexcelattachment:
        try:
            df = pd.read_csv(csvexcelattachment)
        except:
            df = pd.read_excel(csvexcelattachment)
        txt += '   Dataframe: \n' + str(df)

    if graphviz_mode:
        if lang == 'Español':
          txt += '   Genera un grafo con graphviz en .dot \n'
        else:
          txt += '   Generate a graph with graphviz in .dot \n'

    if len(txt) > 5000:
        txt = txt[:5000] + '...'
    if image or url != '':
        if url != '':
            img = Image.open(requests.get(url, stream=True).raw)
        else:
            img = Image.open(image)
        prmt  = {'role': 'user', 'parts':[prompt+txt, img]}
    else:
        prmt  = {'role': 'user', 'parts':[prompt+txt]}

    append_message(prmt)

    if lang == 'Español':
      spinertxt = 'Espera un momento, estoy pensando...'
    else:
      spinertxt = 'Wait a moment, I am thinking...'
    with st.spinner(spinertxt):
        if len(prmt['parts']) > 1:
            try:
                response = vision.generate_content(
                    prmt['parts'],
                    stream=True
                )
                response.resolve()
            except Exception as e:
                error_message = f"Error al procesar la imagen: {str(e)}"
                if 'NotFound' in str(e):
                    error_message = "Error: El modelo de visión no está disponible en este momento. Por favor, inténtalo de nuevo más tarde."
                elif 'InvalidArgument' in str(e):
                    error_message = "Error: Los argumentos proporcionados no son válidos. Por favor, revisa tu entrada."
                append_message({'role': 'model', 'parts': error_message})
                st.rerun()
        else:
            try:
                response = st.session_state.chat.send_message(prmt['parts'][0])
            except Exception as e:
                error_message = f"Error al procesar el mensaje: {str(e)}"
                if 'NotFound' in str(e):
                    error_message = "Error: El modelo no está disponible en este momento. Por favor, inténtalo de nuevo más tarde."
                elif 'InvalidArgument' in str(e):
                    error_message = "Error: Los argumentos proporcionados no son válidos. Por favor, revisa tu entrada."
                append_message({'role': 'model', 'parts': error_message})
                st.rerun()

        try:
            append_message({'role': 'model', 'parts':response.text})
        except Exception as e:
            error_message = f"Error al procesar la respuesta: {str(e)}"
            if 'NotFound' in str(e):
                error_message = "Error: El modelo no está disponible en este momento. Por favor, inténtalo de nuevo más tarde."
            elif 'InvalidArgument' in str(e):
                error_message = "Error: Los argumentos proporcionados no son válidos. Por favor, revisa tu entrada."
            append_message({'role': 'model', 'parts': error_message})


        st.rerun()



#st.session_state.chat_session



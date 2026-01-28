import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Matemáticas III - Economía UCAB",
    page_icon="📈",
    layout="wide"
)

# --- CONFIGURACIÓN DE GEMINI ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ Falta la API Key. Configúrala en los Secrets.")

model = genai.GenerativeModel('gemini-1.5-flash')

# --- INICIALIZACIÓN DEL CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Hola. Soy tu tutor virtual de Matemáticas III para Economía. ¿En qué tema de Cálculo Integral o Ecuaciones Diferenciales trabajaremos hoy?"
    })

# --- BARRA LATERAL (NAVEGACIÓN) ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/f/f0/Logo_UCAB_H.png", width=200)
    st.markdown("### 🏛️ Escuela de Economía")
    
    ruta = st.radio(
        "Modo de Estudio:",
        ["a) Entrenamiento (Temario)", 
         "b) Respuesta Guiada (Consultas)", 
         "c) Autoevaluación (Quiz)"]
    )
    
    st.divider()
    
    # CONTEXTO BASE (IDENTIDAD)
    base_context = """
    Actúa como un profesor titular de la cátedra de Matemáticas III de la carrera de Economía 
    en la Universidad Católica Andrés Bello (UCAB). 
    
    TU ENFOQUE:
    1. Tus dos pilares fundamentales son: CÁLCULO INTEGRAL y ECUACIONES DIFERENCIALES.
    2. Cuando expliques, trata de buscar aplicaciones económicas (Excedente del consumidor/productor, modelos de crecimiento, curvas de oferta/demanda).
    3. Sé riguroso pero cercano. No resuelvas los ejercicios por el alumno, guíalo socráticamente.
    """

    # LÓGICA RUTA A: TEMARIO DETALLADO
    if ruta == "a) Entrenamiento (Temario)":
        st.write("### 📘 Temario Detallado")
        
        # Lista exacta solicitada
        temas_detallados = [
            "1.1.1 Integrales Directas (Tabla)",
            "1.1.2 Cambios de variables (Sustitución)",
            "1.1.3 División de Polinomios",
            "1.1.4 Fracciones Simples",
            "1.1.5 Completación de Cuadrados",
            "1.1.7 Integral por partes",
            "1.2.1 Áreas entre curvas",
            "1.2.2 Excedentes del consumidor y productor",
            "1.2.3 Volúmenes de sólidos de revolución",
            "1.2.4 Integrales dobles (Cálculo directo)",
            "2.1.1 ED 1er Orden: Separación de Variables",
            "2.1.2 ED 1er Orden: Homogéneas",
            "2.1.3 ED 1er Orden: Exactas",
            "2.1.4 ED 1er Orden: Lineales",
            "2.1.5 ED 1er Orden: Bernoulli",
            "2.2.1 ED Orden Superior: Homogéneas",
            "2.2.2 ED Orden Superior: No Homogéneas",
            "2.3 Aplicaciones de Ecuaciones Diferenciales en Economía"
        ]
        
        tema = st.selectbox("Selecciona el punto específico:", temas_detallados)
        
        contexto_sistema = f"{base_context}\nEl alumno quiere repasar el punto: '{tema}'. Explica el método o concepto, sus condiciones de uso y da un ejemplo relevante para economía."

    # LÓGICA RUTA B: CONSULTA ABIERTA
    elif ruta == "b) Respuesta Guiada (Consultas)":
        st.info("Sube tu ejercicio. Te ayudaré a plantearlo.")
        contexto_sistema = f"{base_context}\nEl alumno te consultará un ejercicio específico. Identifica errores, sugiere estrategias de resolución (ej: validar si es exacta o lineal) y guía su razonamiento."

    # LÓGICA RUTA C: QUIZ
    else:
        st.warning("Generando Quiz de 8 preguntas...")
        contexto_sistema = f"{base_context}\nGenera 8 preguntas de selección simple variadas que cubran tanto Integrales (Métodos y Aplicaciones) como Ecuaciones Diferenciales (1er orden y Superior). Al final, evalúa las respuestas."

    if st.button("Borrar Historial"):
        st.session_state.messages = []
        st.rerun()

# --- INTERFAZ PRINCIPAL ---

st.title("Matemáticas III - Economía UCAB")
st.markdown("""
<div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #00aeef;">
    <h4>👋 Bienvenidos al curso de Matemáticas III</h4>
    <p>Bienvenidos al curso de Matemáticas III en la Carrera de Economía en la Universidad Católica Andrés Bello.</p>
    <p>Este curso centra sus esfuerzos en dos grandes pilares: <strong>Cálculo Integral</strong> y <strong>Ecuaciones Diferenciales</strong>.</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# CHAT
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# INPUT
imagen_upload = None
if ruta == "b) Respuesta Guiada (Consultas)":
    imagen_upload = st.file_uploader("Adjuntar imagen del problema", type=["png", "jpg", "jpeg"])

prompt = st.chat_input("Escribe tu consulta aquí...")

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
        if imagen_upload:
            st.image(imagen_upload, width=300)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        placeholder = st.empty()
        try:
            full_prompt = f"SISTEMA: {contexto_sistema}\nUSUARIO: {prompt}"
            
            if imagen_upload:
                img = Image.open(imagen_upload)
                response = model.generate_content([full_prompt, img])
            else:
                chat = model.start_chat(history=[])
                response = chat.send_message(full_prompt)
                
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            placeholder.error(f"Error: {e}")

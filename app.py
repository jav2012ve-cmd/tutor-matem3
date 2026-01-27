import streamlit as st
import os
import google.generativeai as genai
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

# --- CONFIGURACIÓN BÁSICA ---
st.set_page_config(page_title="Tutor Mate III", page_icon="🎓")
st.title("🎓 Tutor de Matemáticas III")

# --- CONFIGURACIÓN DE API KEY ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    else:
        st.error("⚠️ Falta la API KEY en los Secrets.")
        st.stop()
except Exception as e:
    st.error(f"Error de configuración: {e}")

# --- AUTO-DETECCIÓN DE MODELO (SIN CACHÉ PARA EVITAR ERRORES) ---
def get_working_model():
    # Intentamos listar los modelos disponibles para tu cuenta
    try:
        model_name = None
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name: # Prioridad a Flash (más rápido y barato)
                    return m.name
        
        # Si no encontramos Flash, devolvemos el primero que sirva
        for m in genai.list_models():
             if 'generateContent' in m.supported_generation_methods:
                return m.name
                
        return "gemini-1.5-flash" # Fallback por defecto si no encuentra nada
    except Exception as e:
        return "gemini-1.5-flash" # Fallback en caso de error

# Ejecutamos la búsqueda (Directo, sin guardar en memoria)
nombre_modelo_real = get_working_model()

# --- INICIALIZACIÓN DEL MODELO ---
try:
    SYSTEM_PROMPT = """
    Eres un profesor experto en Matemáticas III (Cálculo Vectorial).
    1. Usa LaTeX ($...$) para fórmulas.
    2. Si graficas: usa código Python (matplotlib) en bloques ```python.
       - Usa plt.title('Texto Simple') sin LaTeX.
       - Usa plt.grid(True).
    """
    
    model = genai.GenerativeModel(
        model_name=nombre_modelo_real,
        system_instruction=SYSTEM_PROMPT,
        generation_config={"temperature": 0.1}
    )
    st.caption(f"✅ Conectado a: `{nombre_modelo_real}`")
except Exception as e:
    st.error(f"Error iniciando el modelo: {e}")
    st.stop()

# --- INTERFAZ DE USUARIO ---
with st.sidebar:
    st.header("📂 Subir Ejercicio")
    uploaded_file = st.file_uploader("Sube foto", type=["jpg", "png", "jpeg"])
    image_data = None
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Imagen cargada")
        image_data = image

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for role, text, img in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(text)
        if img: st.image(img, width=300)

if prompt := st.chat_input("Escribe tu pregunta..."):
    with st.chat_message("user"):
        st.write(prompt)
        if image_data: st.image(image_data, width=300)
    
    st.session_state.chat_history.append(("user", prompt, image_data))
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("Pensando..."):
            try:
                content = [prompt]
                if image_data: content.append(image_data)
                
                response = model.generate_content(content)
                text = response.text
                
                # Procesar respuesta
                text = text.replace(" , dx", " \, dx")
                parts = text.split("```python")
                
                message_placeholder.markdown(parts[0])
                
                if len(parts) > 1:
                    code = parts[1].split("```")[0]
                    try:
                        plt.clf()
                        exec(code, {"plt": plt, "np": np})
                        st.pyplot(plt.gcf())
                    except: pass
                
                st.session_state.chat_history.append(("assistant", parts[0], None))
                
            except Exception as e:
                st.error(f"Error generando respuesta: {e}")
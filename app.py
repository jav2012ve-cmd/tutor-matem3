import streamlit as st
import os
import google.generativeai as genai
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Tutor Mate III", page_icon="🎓")
st.title("🎓 Tutor de Matemáticas III (Conexión Directa)")

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

# --- CONFIGURACIÓN DEL MODELO ---
# Instrucciones para el profesor
SYSTEM_PROMPT = """
Eres un profesor experto en Matemáticas III (Cálculo Vectorial).
1. Usa LaTeX ($...$) para fórmulas matemáticas.
2. NO repitas la fórmula en texto antes del LaTeX.
3. Si graficas: usa código Python (matplotlib) en bloques ```python.
   - Usa plt.title('Texto Simple') sin LaTeX.
   - Usa plt.grid(True).
"""

# Configuración del modelo (Gemini 1.5 Flash - Estándar)
generation_config = {
    "temperature": 0.1,
    "max_output_tokens": 2048,
}

# Iniciamos el modelo directamnte
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash", 
    generation_config=generation_config,
    system_instruction=SYSTEM_PROMPT
)

# --- BARRA LATERAL (IMAGEN) ---
with st.sidebar:
    st.header("📂 Subir Ejercicio")
    uploaded_file = st.file_uploader("Sube foto del problema", type=["jpg", "png", "jpeg"])
    
    image_data = None
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Imagen cargada")
        image_data = image # Guardamos el objeto PIL Image directo para Gemini
        st.success("✅ Imagen lista")

# --- HISTORIAL DE CHAT ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Mostrar historial en pantalla
for role, text, img in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(text)
        if img:
            st.image(img, width=300)

# --- LÓGICA DE ENVÍO ---
if prompt := st.chat_input("Escribe tu pregunta aquí..."):
    
    # 1. Mostrar mensaje usuario
    with st.chat_message("user"):
        st.write(prompt)
        if image_data:
            st.image(image_data, width=300)
    
    # Guardar en historial visual
    st.session_state.chat_history.append(("user", prompt, image_data))
    
    # 2. Generar respuesta
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("Conectando con Google..."):
            try:
                # Preparamos el contenido para enviar
                # Gemini acepta una lista: [texto, imagen]
                content_to_send = [prompt]
                if image_data:
                    content_to_send.append(image_data)
                
                # ENVIAMOS EL MENSAJE (SIN HISTORIAL AUTOMÁTICO PARA EVITAR ERRORES)
                # Usamos generate_content que es "sin memoria" pero más robusto para empezar
                # (Le pasamos el contexto básico si fuera necesario, pero por ahora pregunta-respuesta)
                response = model.generate_content(content_to_send)
                
                full_text = response.text
                
                # --- PROCESAMIENTO DE RESPUESTA ---
                # Limpieza LaTeX
                full_text = full_text.replace(" , dx", " \, dx")
                
                # Separar código de gráfico
                parts = full_text.split("```python")
                text_part = parts[0]
                
                # Mostrar texto
                message_placeholder.markdown(text_part)
                
                # Ejecutar gráfico
                if len(parts) > 1:
                    code_block = parts[1].split("```")[0]
                    try:
                        plt.clf()
                        local_context = {"plt": plt, "np": np}
                        exec(code_block, {}, local_context)
                        st.pyplot(plt.gcf())
                    except Exception as e:
                        st.warning(f"Gráfico no disponible: {e}")
                
                # Guardar respuesta en historial
                st.session_state.chat_history.append(("assistant", text_part, None))
                
            except Exception as e:
                st.error(f"❌ Error crítico: {e}")
                st.info("Intenta refrescar la página.")
import streamlit as st
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Tutor Mate III", page_icon="🎓")
st.title("🎓 Tutor de Matemáticas III")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("📂 Subir Ejercicio")
    uploaded_file = st.file_uploader("Sube foto del problema", type=["jpg", "png", "jpeg"])
    
    image_content = None
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Imagen cargada")
        import io, base64
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        image_content = {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_str}"}}
        st.success("✅ Imagen lista")

# --- API KEY ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
    else:
        st.error("Falta la API KEY en Secrets.")
        st.stop()
except:
    pass

# --- MODELO (USANDO LA VERSIÓN MÁS ESTABLE) ---
if "llm" not in st.session_state:
    try:
        st.session_state.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",  # Este es el modelo estándar gratuito
            temperature=0.1,
            convert_system_message_to_human=True
        )
    except Exception as e:
        st.error(f"Error conectando: {e}")

# --- CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        SystemMessage(content="Eres un profesor de Matemáticas III. Usa LaTeX ($) para fórmulas. Si graficas, usa código Python (matplotlib) con plt.grid(True) y sin LaTeX en títulos.")
    ]

# MOSTRAR HISTORIAL
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            # Mostrar texto si es string, o manejar lista si tiene imagen
            if isinstance(msg.content, str):
                st.write(msg.content)
            elif isinstance(msg.content, list):
                st.write(msg.content[0]['text']) # Mostrar solo el texto de la pregunta
                
    elif not isinstance(msg, SystemMessage):
        with st.chat_message("assistant"):
            st.markdown(msg.content.split("```python")[0]) # Mostrar solo texto, no código crudo

# INPUT USUARIO
if prompt := st.chat_input("Pregunta aquí..."):
    # Mostrar usuario
    with st.chat_message("user"):
        st.write(prompt)
    
    # Preparar datos
    content = [{"type": "text", "text": prompt}]
    if image_content: content.append(image_content)
    
    # Guardar y enviar
    st.session_state.messages.append(HumanMessage(content=content))
    
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                response = st.session_state.llm.invoke(st.session_state.messages)
                text_resp = response.content
                if isinstance(text_resp, list): text_resp = "".join(str(x) for x in text_resp)
                
                # Separar gráfico
                parts = text_resp.split("```python")
                st.markdown(parts[0].replace(" , dx", " \, dx"))
                
                if len(parts) > 1:
                    code = parts[1].split("```")[0]
                    try:
                        plt.clf()
                        exec(code, {"plt": plt, "np": np})
                        st.pyplot(plt.gcf())
                    except: pass
                
                st.session_state.messages.append(response)
            except Exception as e:
                st.error(f"Error: {e}")
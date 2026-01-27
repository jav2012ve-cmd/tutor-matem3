import streamlit as st
import os
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Tutor IA - Matemáticas III",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 Tutor de Matemáticas III (Cálculo Vectorial)")
st.markdown("""
**Instrucciones:**
1. Escribe tu duda en el chat.
2. Si tienes un ejercicio en imagen, **súbelo en la barra lateral** antes de preguntar.
""")

# --- BARRA LATERAL (SUBIDA DE IMAGEN) ---
with st.sidebar:
    st.header("📂 Subir Ejercicio")
    uploaded_file = st.file_uploader("Sube una foto del problema", type=["jpg", "png", "jpeg"])
    
    image_content = None
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Imagen cargada", use_column_width=True)
        # Preparar imagen para la IA
        import io
        import base64
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        image_content = {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_str}"}}
        st.success("✅ Imagen lista para analizar")

# --- GESTIÓN DE SECRETOS (API KEY) ---
# Intentamos obtener la clave desde los secretos de Streamlit
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    os.environ["GOOGLE_API_KEY"] = api_key
except:
    st.error("⚠️ No se encontró la API KEY. Configúrala en los 'Secrets' de Streamlit Cloud.")
    st.stop()

# --- CONFIGURACIÓN DEL MODELO ---
if "llm" not in st.session_state:
    try:
        st.session_state.llm = ChatGoogleGenerativeAI(
            model="gemini-flash-latest", 
            temperature=0.1,
            convert_system_message_to_human=True
        )
    except:
        st.session_state.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash", 
            temperature=0.1
        )

# --- INICIALIZAR HISTORIAL ---
if "messages" not in st.session_state:
    system_prompt = """
    Eres un profesor experto en Matemáticas III (Cálculo Vectorial).
    
    INSTRUCCIONES DE FORMATO:
    1. Usa LaTeX estándar para fórmulas: $ \int x dx $.
    2. Ecuaciones grandes centradas con $$.
    
    INSTRUCCIONES GRÁFICAS (PYTHON):
    Si necesitas graficar:
    1. Genera código Python dentro de triples comillas (```python).
    2. USA TEXTO SIMPLE para títulos y etiquetas (No LaTeX en plt.title).
       MAL: plt.title(r'$\int f(x)$')
       BIEN: plt.title('Integral de f(x)')
    3. Usa plt.grid(True).
    """
    st.session_state.messages = [SystemMessage(content=system_prompt)]
    st.session_state.chat_display = [] # Para mostrar en pantalla (separado de la memoria interna)

# --- MOSTRAR CHAT PREVIO ---
for msg in st.session_state.chat_display:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "image" in msg:
            st.pyplot(msg["image"])

# --- LÓGICA DEL CHAT ---
if prompt := st.chat_input("Escribe tu pregunta aquí..."):
    
    # 1. Mostrar mensaje del usuario
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 2. Preparar mensaje para la IA
    content_payload = []
    content_payload.append({"type": "text", "text": prompt})
    
    # Si hay imagen en la barra lateral, la adjuntamos
    if image_content:
        content_payload.append(image_content)
        st.sidebar.info("📎 Enviando imagen con la pregunta...")

    # Guardar en historial interno y display
    st.session_state.messages.append(HumanMessage(content=content_payload))
    st.session_state.chat_display.append({"role": "user", "content": prompt})

    # 3. Generar Respuesta
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("El profesor está pensando..."):
            try:
                response = st.session_state.llm.invoke(st.session_state.messages)
                full_response = response.content
                
                # Unificar lista si es necesario
                if isinstance(full_response, list):
                    full_response = "".join([str(x) for x in full_response])
                
                # --- SEPARAR TEXTO Y CÓDIGO ---
                parts = full_response.split("```python")
                text_part = parts[0]
                
                # Renderizar Texto
                message_placeholder.markdown(text_part)
                
                # Ejecutar Gráfico si existe
                chart_fig = None
                if len(parts) > 1:
                    code_block = parts[1].split("```")[0]
                    try:
                        # Limpiar figura anterior
                        plt.clf()
                        
                        # Contexto seguro
                        local_context = {"plt": plt, "np": np}
                        exec(code_block, {}, local_context)
                        
                        # Obtener figura actual
                        fig = plt.gcf()
                        st.pyplot(fig)
                        chart_fig = fig
                    except Exception as e:
                        st.error(f"Error generando gráfico: {e}")

                # Guardar respuesta en historial
                st.session_state.messages.append(response)
                
                # Guardar en display
                display_entry = {"role": "assistant", "content": text_part}
                if chart_fig:
                    display_entry["image"] = chart_fig
                st.session_state.chat_display.append(display_entry)
                
            except Exception as e:
                st.error(f"Ocurrió un error: {e}")
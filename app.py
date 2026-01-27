import streamlit as st
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
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

# --- BARRA LATERAL (CONFIGURACIÓN Y FOTOS) ---
with st.sidebar:
    st.header("⚙️ Configuración Técnica")
    
    # AQUÍ ESTÁ LA SOLUCIÓN: Un selector para que pruebes cuál te funciona
    modelo_seleccionado = st.selectbox(
        "Selecciona el Modelo de IA:",
        [
            "gemini-1.5-flash-001",   # Opción 1: Versión específica (Suele funcionar cuando la normal falla)
            "gemini-1.5-flash-8b",    # Opción 2: Versión ligera nueva
            "gemini-pro",             # Opción 3: Versión 1.0 (La vieja confiable)
            "gemini-1.5-pro",         # Opción 4: Versión Potente
            "gemini-1.5-flash"        # Opción 5: La estándar (que te dio error)
        ],
        index=0 # Por defecto probamos la primera
    )
    
    st.info(f"Usando motor: {modelo_seleccionado}")
    
    st.divider()
    
    st.header("📂 Subir Ejercicio")
    uploaded_file = st.file_uploader("Sube una foto del problema", type=["jpg", "png", "jpeg"])
    
    image_content = None
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Imagen cargada", use_column_width=True)
        # Preparar imagen
        import io
        import base64
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        image_content = {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_str}"}}
        st.success("✅ Imagen lista")

# --- GESTIÓN DE SECRETOS ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
    else:
        st.error("⚠️ Falta la API KEY en los 'Secrets'.")
        st.stop()
except:
    st.warning("Nota: Ejecutando sin secretos configurados.")

# --- INICIALIZAR EL MODELO (Con el que seleccionaste en el menú) ---
if "llm" not in st.session_state or st.session_state.get("last_model") != modelo_seleccionado:
    try:
        st.session_state.llm = ChatGoogleGenerativeAI(
            model=modelo_seleccionado,
            temperature=0.1,
            convert_system_message_to_human=True
        )
        st.session_state.last_model = modelo_seleccionado
    except Exception as e:
        st.error(f"Error cargando modelo: {e}")

# --- INICIALIZAR HISTORIAL ---
if "messages" not in st.session_state:
    system_prompt = """
    Eres un profesor experto en Matemáticas III (Cálculo Vectorial).
    
    REGLA DE FORMATO:
    1. Escribe fórmulas DIRECTAMENTE en LaTeX usando signos de dólar ($).
       - BIEN: "La función es $f(x)=x^2$"
    2. NO repitas la fórmula en texto plano antes del LaTeX.
    
    REGLAS GRÁFICAS (PYTHON):
    Si necesitas graficar:
    1. Genera código Python (matplotlib) dentro de ```python.
    2. Usa TEXTO SIMPLE para títulos (nada de LaTeX en plt.title).
    3. Usa plt.grid(True).
    """
    st.session_state.messages = [SystemMessage(content=system_prompt)]
    st.session_state.chat_display = [] 

# --- MOSTRAR CHAT ---
for msg in st.session_state.chat_display:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "image" in msg:
            st.pyplot(msg["image"])

# --- LÓGICA DEL CHAT ---
if prompt := st.chat_input("Escribe tu pregunta aquí..."):
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    content_payload = []
    content_payload.append({"type": "text", "text": prompt})
    
    if image_content:
        content_payload.append(image_content)
        st.sidebar.info("📎 Enviando imagen...")

    st.session_state.messages.append(HumanMessage(content=content_payload))
    st.session_state.chat_display.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner(f"Pensando con {modelo_seleccionado}..."):
            try:
                response = st.session_state.llm.invoke(st.session_state.messages)
                full_response = response.content
                
                if isinstance(full_response, list):
                    full_response = "".join([str(x) for x in full_response])
                
                full_response = full_response.replace(" , dx", " \, dx")
                
                parts = full_response.split("```python")
                text_part = parts[0]
                
                message_placeholder.markdown(text_part)
                
                chart_fig = None
                if len(parts) > 1:
                    code_block = parts[1].split("```")[0]
                    try:
                        plt.clf()
                        local_context = {"plt": plt, "np": np}
                        exec(code_block, {}, local_context)
                        fig = plt.gcf()
                        st.pyplot(fig)
                        chart_fig = fig
                    except Exception:
                        pass

                st.session_state.messages.append(response)
                
                display_entry = {"role": "assistant", "content": text_part}
                if chart_fig:
                    display_entry["image"] = chart_fig
                st.session_state.chat_display.append(display_entry)
                
            except Exception as e:
                st.error(f"❌ Error con {modelo_seleccionado}: {e}")
                st.info("💡 PRUEBA CAMBIAR EL MODELO EN LA BARRA LATERAL IZQUIERDA")
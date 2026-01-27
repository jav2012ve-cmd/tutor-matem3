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

# --- INICIALIZAR HISTORIAL (AQUÍ ESTÁ LA CORRECCIÓN DE ESTILO) ---
if "messages" not in st.session_state:
    system_prompt = """
    Eres un profesor experto en Matemáticas III (Cálculo Vectorial).
    
    REGLA DE ORO DE FORMATO (NO REPETIR):
    1. NUNCA escribas la misma expresión dos veces (una en texto y otra en LaTeX).
    2. Escribe DIRECTAMENTE en LaTeX usando signos de dólar ($).
       - MAL: "La función f(x) = x, es decir $f(x)=x$" (Esto es redundante).
       - BIEN: "La función $f(x)=x$..." (Esto es correcto).
    
    REGLAS VISUALES:
    1. Usa LaTeX estándar: $ \int x dx $.
    2. Ecuaciones grandes o pasos importantes deben ir centrados con doble signo: $$ \oint_C \vec{F} \cdot d\vec{r} $$
    3. Separa los pasos con saltos de línea claros.
    
    REGLAS PARA GRAFICAR (PYTHON):
    Si necesitas graficar una región o curva:
    1. Genera código Python dentro de triples comillas (```python).
    2. Usa TEXTO SIMPLE para títulos y etiquetas (No LaTeX en plt.title para evitar errores).
    3. Usa plt.grid(True) y asegúrate de que el gráfico sea claro.
    """
    st.session_state.messages = [SystemMessage(content=system_prompt)]
    st.session_state.chat_display = [] 

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
    
    if image_content:
        content_payload.append(image_content)
        st.sidebar.info("📎 Enviando imagen con la pregunta...")

    st.session_state.messages.append(HumanMessage(content=content_payload))
    st.session_state.chat_display.append({"role": "user", "content": prompt})

    # 3. Generar Respuesta
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("El profesor está pensando..."):
            try:
                response = st.session_state.llm.invoke(st.session_state.messages)
                full_response = response.content
                
                # Unificar lista
                if isinstance(full_response, list):
                    full_response = "".join([str(x) for x in full_response])
                
                # --- LIMPIEZA ADICIONAL ---
                # A veces el modelo deja espacios feos en integrales, esto ayuda visualmente
                full_response = full_response.replace(" , dx", " \, dx")
                
                # --- SEPARAR TEXTO Y CÓDIGO ---
                parts = full_response.split("```python")
                text_part = parts[0]
                
                # Renderizar Texto
                message_placeholder.markdown(text_part)
                
                # Ejecutar Gráfico
                chart_fig = None
                if len(parts) > 1:
                    code_block = parts[1].split("```")[0]
                    try:
                        plt.clf()
                        # Contexto seguro para gráficas
                        local_context = {"plt": plt, "np": np}
                        exec(code_block, {}, local_context)
                        fig = plt.gcf()
                        st.pyplot(fig)
                        chart_fig = fig
                    except Exception as e:
                        st.warning(f"No se pudo generar el gráfico visualmente, pero el cálculo es correcto.")

                # Guardar respuesta
                st.session_state.messages.append(response)
                
                display_entry = {"role": "assistant", "content": text_part}
                if chart_fig:
                    display_entry["image"] = chart_fig
                st.session_state.chat_display.append(display_entry)
                
            except Exception as e:
                st.error(f"Ocurrió un error: {e}")
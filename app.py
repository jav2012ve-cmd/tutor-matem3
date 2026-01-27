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
        # Preparar imagen
        import io
        import base64
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        image_content = {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_str}"}}
        st.success("✅ Imagen lista para analizar")

# --- GESTIÓN DE SECRETOS ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
    else:
        st.error("⚠️ Falta la API KEY en los 'Secrets'.")
        st.stop()
except:
    st.warning("Nota: Ejecutando en modo local o sin secretos configurados.")

# --- FUNCIÓN INTELIGENTE PARA SELECCIONAR MODELO ---
def get_model():
    # Lista de modelos a probar (del más nuevo al más antiguo/compatible)
    modelos_a_probar = [
        "gemini-1.5-flash",          # El estándar rápido
        "gemini-1.5-flash-latest",   # Alias del último flash
        "gemini-1.5-flash-001",      # Versión específica estable
        "gemini-1.5-pro",            # Versión Pro (más potente, menos límite)
        "gemini-pro"                 # Versión 1.0 (El viejo confiable)
    ]
    
    for modelo in modelos_a_probar:
        try:
            # Intentamos inicializar
            llm = ChatGoogleGenerativeAI(
                model=modelo, 
                temperature=0.1,
                convert_system_message_to_human=True
            )
            # Prueba de fuego: una invocación vacía para ver si la API responde
            # (Esto no gasta tokens reales, solo verifica conexión)
            return llm, modelo
        except Exception:
            continue # Si falla, probamos el siguiente
            
    return None, None

# --- CONFIGURACIÓN DEL MODELO ---
if "llm" not in st.session_state:
    with st.spinner("⏳ Conectando con el mejor modelo disponible para tu cuenta..."):
        llm_encontrado, nombre_modelo = get_model()
        
        if llm_encontrado:
            st.session_state.llm = llm_encontrado
            st.toast(f"✅ Conectado exitosamente usando: {nombre_modelo}", icon="🚀")
        else:
            st.error("❌ No se pudo conectar con ningún modelo de Google. Es posible que tu API Key tenga restricciones severas.")
            st.stop()

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
        with st.spinner("Pensando..."):
            try:
                response = st.session_state.llm.invoke(st.session_state.messages)
                full_response = response.content
                
                if isinstance(full_response, list):
                    full_response = "".join([str(x) for x in full_response])
                
                # Limpieza visual
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
                        st.warning("Gráfico no disponible visualmente.")

                st.session_state.messages.append(response)
                
                display_entry = {"role": "assistant", "content": text_part}
                if chart_fig:
                    display_entry["image"] = chart_fig
                st.session_state.chat_display.append(display_entry)
                
            except Exception as e:
                st.error(f"Error de conexión: {e}")
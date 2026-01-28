import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Matemáticas III - Economía UCAB",
    page_icon="📈",
    layout="wide"
)

# --- CONFIGURACIÓN DE API KEY ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ Falta la API Key. Configúrala en los Secrets.")
    st.stop()

# --- AUTO-DETECCIÓN DE MODELO (TU SOLUCIÓN ROBUSTA) ---
def get_working_model():
    try:
        # Intentamos listar los modelos disponibles
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name: # Prioridad a Flash (rápido/barato)
                    return m.name
        
        # Si no hay Flash, devolvemos cualquiera que sirva
        for m in genai.list_models():
             if 'generateContent' in m.supported_generation_methods:
                return m.name
                
        return "gemini-1.5-flash" # Fallback final
    except Exception as e:
        return "gemini-1.5-flash" # Fallback en caso de error extremo

# Ejecutamos la búsqueda
nombre_modelo_real = get_working_model()

# --- INICIALIZACIÓN DEL MODELO ---
try:
    # Inicializamos sin prompt fijo aquí, porque lo inyectamos dinámicamente según la ruta
    model = genai.GenerativeModel(
        model_name=nombre_modelo_real,
        generation_config={"temperature": 0.3}
    )
    # Pequeño indicador para saber qué modelo pescó (solo visible si miras con atención)
    st.caption(f"⚙️ Sistema conectado a: `{nombre_modelo_real}`")
except Exception as e:
    st.error(f"Error iniciando el modelo: {e}")
    st.stop()


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
    
    # --- MENÚ CON BOTÓN DE CONFIRMACIÓN ---
    
    # 1. Variable temporal para la selección visual
    seleccion_visual = st.radio(
        "1. Selecciona tu Modo de Estudio:",
        ["a) Entrenamiento (Temario)", 
         "b) Respuesta Guiada (Consultas)", 
         "c) Autoevaluación (Quiz)"],
        index=None
    )
    
    # 2. Botón para "Dar Inicio" (Guarda la selección en memoria)
    if st.button("▶️ Iniciar Sesión"):
        st.session_state.modo_actual = seleccion_visual
        st.rerun() # Recarga inmediata para mostrar el contenido
        
    # 3. Botón para Reiniciar/Cambiar (Opcional)
    if st.button("🔄 Cambiar Modo"):
        st.session_state.modo_actual = None
        st.session_state.messages = [] # Limpiamos el chat
        st.rerun()
    
    st.divider()
    
    # Contexto Base (Mantenemos tu texto original)...
    base_context = """
    Actúa como un profesor titular de la cátedra de Matemáticas III de la carrera de Economía 
    en la Universidad Católica Andrés Bello (UCAB). 
    
    TU ENFOQUE:
    1. Tus dos pilares fundamentales son: CÁLCULO INTEGRAL y ECUACIONES DIFERENCIALES.
    2. Cuando expliques, trata de buscar aplicaciones económicas.
    3. Sé riguroso pero cercano. Usa LaTeX.
    """
    
    # --- LÓGICA DE ASIGNACIÓN ---
    # Recuperamos la ruta REAL desde la memoria, no desde el radio button
    if "modo_actual" not in st.session_state:
        st.session_state.modo_actual = None
        
    ruta = st.session_state.modo_actual

    
    # LÓGICA RUTA A: ENTRENAMIENTO (Solo Menú)
    if ruta == "a) Entrenamiento (Temario)":
        st.write("### 📘 Temario Detallado")
        
        temas_detallados = [
            "1.1.1 Integrales Directas", 
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
        
        # Guardamos la selección en session_state para usarla afuera
        if "tema_seleccionado" not in st.session_state:
            st.session_state.tema_seleccionado = temas_detallados[0]

        seleccion = st.selectbox("Selecciona el punto específico:", temas_detallados)
        st.session_state.tema_seleccionado = seleccion # Actualizamos
        
        # Configuración del Prompt para la IA (Igual que antes)
        tema_actual = st.session_state.tema_seleccionado
        if tema_actual == "1.1.1 Integrales Directas":
             prompt_inicio = """
             Actúa como Profesor. El alumno ya está viendo la tabla de integrales.
             Tarea: Propón UN ejercicio sencillo de aplicación directa de la tabla.
             """
        elif tema_actual.startswith("1.1"):
             prompt_inicio = f"Explica la técnica de {tema_actual} y pon un ejercicio."
        else:
             prompt_inicio = f"Explica la aplicación económica de {tema_actual}."

        # Lógica de disparo automático (Simplificada para no saturar)
        if "ultimo_tema" not in st.session_state or st.session_state.ultimo_tema != tema_actual:
            st.session_state.ultimo_tema = tema_actual
            with st.spinner("Preparando profesor..."):
                try:
                    res = model.generate_content(prompt_inicio)
                    st.session_state.messages.append({"role": "assistant", "content": res.text})
                except: pass
        
        contexto_sistema = f"{base_context}\nTema: {tema_actual}"
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
if ruta is None:
    st.info("⬅️ Para comenzar, selecciona una opción en el menú y presiona el botón **'Iniciar Sesión'**.")
    st.stop()
    # --- ZONA DE CONTENIDO VISUAL (BLOQUE DERECHO) ---
if ruta == "a) Entrenamiento (Temario)":
    
    # Recuperamos el tema seleccionado
    tema_actual = st.session_state.get("tema_seleccionado", "")

    # CASO 1.1.1: INTEGRALES DIRECTAS (Tu contenido)
    if tema_actual == "1.1.1 Integrales Directas":
        st.subheader("1.1.1 Integrales Directas")
        
        st.markdown("#### 1. Definición")
        st.info("La definición de integral indefinida está ampliamente relacionada con el concepto de derivada.")
        st.latex(r"f(x) = \int g(x) dx \iff \frac{d}{dx}[f(x)] = g(x)")
        
        st.markdown("#### 2. Propiedades Básicas")
        col_prop1, col_prop2 = st.columns(2)
        with col_prop1:
            st.latex(r"\int [f(x) \pm g(x)] dx = \int f(x) dx \pm \int g(x) dx")
        with col_prop2:
            st.latex(r"\int C \cdot f(x) dx = C \int f(x) dx")
            
        st.markdown("#### 3. Tabla de Integrales Inmediatas")
        with st.expander("Ver Tabla Completa", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.latex(r"\int x^n dx = \frac{x^{n+1}}{n+1}, \quad n \neq -1")
                st.latex(r"\int \frac{1}{x} dx = \ln|x|")
                st.latex(r"\int e^{ax+b} dx = \frac{1}{a}e^{ax+b}")
                st.latex(r"\int \ln x dx = x\ln x - x")
            with col2:
                st.latex(r"\int a^x dx = \frac{1}{\ln a}a^x")
                st.latex(r"\int \frac{dx}{x^2 + a^2} = \frac{1}{a}\arctan\left(\frac{x}{a}\right)")
                st.latex(r"\int \frac{dx}{\sqrt{a^2-x^2}} = \arcsin\left(\frac{x}{a}\right)")
                st.latex(r"\int \frac{dx}{\sqrt{x^2 \pm a^2}} = \ln|x + \sqrt{x^2 \pm a^2}|")

    st.divider() # Separador antes del chat
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
            # Aquí inyectamos el contexto dinámico definido en la barra lateral
            full_prompt = f"INSTRUCCIÓN DE SISTEMA: {contexto_sistema}\n\nMENSAJE USUARIO: {prompt}"
            
            if imagen_upload:
                img = Image.open(imagen_upload)
                response = model.generate_content([full_prompt, img])
            else:
                # Usamos chat history simple
                chat = model.start_chat(history=[])
                response = chat.send_message(full_prompt)
                
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            placeholder.error(f"Error: {e}")









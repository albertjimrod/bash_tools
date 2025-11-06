import re
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.llms import Ollama

# Tu código original para cargar el archivo y extraer el texto
def completer(text, state):
    """Función para el autocompletado de rutas de archivos."""
    text = os.path.expanduser(text)
    if text.startswith('~'):
        text = os.path.join(os.path.expanduser('~'), text[2:])
    dirname = os.path.dirname(text)
    if not dirname:
        dirname = '.'
    filenames = os.listdir(dirname)
    matches = [filename for filename in filenames if filename.startswith(os.path.basename(text))]
    if state < len(matches):
        return os.path.join(dirname, matches[state])
    else:
        return None

import readline
import os

# Configurar el autocompletado
readline.set_completer_delims(' \t\n;')
readline.set_completer(completer)
readline.parse_and_bind("tab: complete")

# Pedir al usuario la ruta del archivo
ruta_archivo = input("Por favor, introduce la ruta del archivo a analizar (puedes usar Tab para autocompletar): ")

# Cargar el documento desde la ruta proporcionada
try:
    with open(ruta_archivo, 'r', encoding='utf-8') as f:
        document_text_xml = f.read()
except FileNotFoundError:
    print(f"Error: El archivo en la ruta '{ruta_archivo}' no fue encontrado.")
    exit()
except Exception as e:
    print(f"Ocurrió un error al leer el archivo: {e}")
    exit()

# **Extracción básica de texto desde XML (eliminar etiquetas)**
extracted_text = re.sub(r'<[^>]+>', '', document_text_xml)
# Eliminar posibles saltos de línea o espacios en blanco extra
extracted_text = ' '.join(extracted_text.split())

# Lista de funciones de Fabric (simplificada para el ejemplo)
fabric_functions = [
    "agility_story",
    "ai",
    "analyze_answers",
    "analyze_claims",
    "analyze_debate",
    "analyze_incident",
    "analyze_logs",
    "analyze_malware",
    "analyze_paper",
    "analyze_patent",
    "analyze_personality",
    "analyze_presentation",
    "analyze_prose",
    "analyze_spiritual_text",
    "analyze_tech_impact",
    "analyze_threat_report",
    "answer_interview_question",
    "create_summary",
    "extract_ideas",
    "extract_insights",
    "explain_code",
    "explain_docs",
    "summarize",
]

# Función para analizar el texto y sugerir la función de Fabric
def suggest_fabric_function(text, functions):
    """Analiza el texto y sugiere la función de Fabric más adecuada."""

    text = text.lower() # Convertir a minúsculas para facilitar la búsqueda

    # Criterios básicos para la selección (puedes hacer esto mucho más sofisticado)
    if "incidente" in text or "reporte" in text and "seguridad" in text:
        return "analyze_incident"
    elif "log" in text or "registro" in text:
        return "analyze_logs"
    elif "malware" in text or "amenaza" in text and "código" in text:
        return "analyze_malware"
    elif "paper" in text or "articulo" in text and "investigación" in text:
        return "analyze_paper"
    elif "patente" in text:
        return "analyze_patent"
    elif "personalidad" in text or "rasgos" in text:
        return "analyze_personality"
    elif "presentación" in text or "diapositivas" in text:
        return "analyze_presentation"
    elif "código" in text and ("explicar" in text or "entender" in text):
        return "explain_code"
    elif "documento" in text and ("explicar" in text or "entender" in text):
        return "explain_docs"
    elif "resumen" in text or "sumario" in text:
        # Aquí podríamos ser más específicos si el texto tiene indicadores de qué tipo de resumen se necesita
        return "summarize"
    elif "idea" in text or "pensamiento" in text:
        return "extract_ideas"
    elif "conocimiento" in text or "aprendizaje" in text:
        return "extract_insights"
    elif "entrevista" in text and "pregunta" in text and ("responder" in text or "contestar" in text):
        return "answer_interview_question"
    elif "debate" in text or "discusión" in text:
        return "analyze_debate"
    elif "reclamo" in text or "afirmación" in text:
        return "analyze_claims"
    elif "respuesta" in text and "analizar" in text:
        return "analyze_answers"
    elif "historia" in text and "agilidad" in text:
        return "agility_story"
    elif "ia" in text or "inteligencia artificial" in text:
        return "ai"
    elif "texto" in text or "prosa" in text:
        return "analyze_prose"
    elif "espiritual" in text or "religioso" in text:
        return "analyze_spiritual_text"
    elif "tecnología" in text and "impacto" in text:
        return "analyze_tech_impact"
    elif "amenaza" in text and "reporte" in text:
        return "analyze_threat_report"
    else:
        return "No se pudo determinar una función específica con los criterios actuales."

# Sugerir la función de Fabric
suggested_function = suggest_fabric_function(extracted_text, fabric_functions)
print(f"\nBasado en el análisis del texto, la función de Fabric sugerida es: {suggested_function}")

# Opcional: Podrías intentar ejecutar la función aquí si tuvieras la integración con Fabric en este entorno.
# Por ejemplo (esto es solo un ejemplo conceptual y requeriría la implementación real de las funciones de Fabric):
# if suggested_function == "create_summary":
#     from fabric_integration import create_summary  # Imagina que tienes un módulo así
#     summary = create_summary(extracted_text)
#     print("\nResultado de la función:")
#     print(summary)

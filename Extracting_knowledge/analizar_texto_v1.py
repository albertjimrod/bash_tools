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

# Diccionario con la descripción de cada patrón de Fabric
fabric_descriptions = {
    "analyze_answers": "Analiza respuestas, posiblemente evaluando su precisión o calidad.",
    "analyze_claims": "Evalúa afirmaciones, posiblemente para verificar su veracidad o argumentos.",
    "analyze_debate": "Analiza debates, probablemente identificando argumentos y posturas.",
    "analyze_incident": "Revisión de incidentes, quizás en ciberseguridad o gestión de crisis.",
    "analyze_logs": "Analiza registros (logs), útil en depuración y seguridad informática.",
    "analyze_malware": "Examina malware para detectar amenazas y vulnerabilidades.",
    "analyze_paper": "Analiza artículos académicos o documentos técnicos.",
    "analyze_patent": "Revisión y análisis de patentes.",
    "analyze_personality": "Evaluación de personalidad a partir de texto (quizás usando modelos de análisis psicológico).",
    "analyze_presentation": "Examina la calidad de una presentación.",
    "analyze_prose": "Analiza prosa, probablemente en términos de estilo, coherencia y gramática.",
    "analyze_prose_json": "Similar a analyze_prose, pero probablemente devuelve resultados en JSON.",
    "analyze_prose_pinker": "Podría estar basado en el análisis lingüístico de Steven Pinker.",
    "analyze_spiritual_text": "Analiza textos espirituales o religiosos.",
    "analyze_tech_impact": "Evalúa el impacto de la tecnología en diversos ámbitos.",
    "analyze_threat_report": "Analiza informes de amenazas en ciberseguridad.",
    "analyze_threat_report_trends": "Identifica tendencias en informes de amenazas.",
    "answer_interview_question": "Responde a preguntas de entrevista.",
    "create_5_sentence_summary": "Crea un resumen en 5 frases.",
    "create_academic_paper": "Genera un artículo académico.",
    "create_ai_jobs_analysis": "Analiza el mercado laboral en inteligencia artificial.",
    "create_aphorisms": "Genera aforismos o frases concisas con significado profundo.",
    "create_art_prompt": "Crea indicaciones para generar arte (AI art prompts).",
    "create_better_frame": "Probablemente reformula ideas para hacerlas más efectivas.",
    "create_command": "Genera comandos (¿CLI, SQL, Bash?).",
    "create_cyber_summary": "Crea un resumen relacionado con ciberseguridad.",
    "create_idea_compass": "Podría generar mapas de ideas o explorar conceptos.",
    "create_keynote": "Ayuda a crear discursos o presentaciones principales.",
    "create_logo": "Genera logotipos.",
    "create_markmap_visualization": "Crea visualizaciones con Markmap (mapas mentales interactivos).",
    "create_mermaid_visualization": "Usa Mermaid.js para crear diagramas.",
    "create_micro_summary": "Genera un resumen muy breve.",
    "create_network_threat_landscape": "Mapea el panorama de amenazas en redes.",
    "create_npc": "Genera personajes para juegos de rol (NPCs).",
    "create_pattern": "Genera patrones, quizás de comportamiento, diseño o seguridad.",
    "create_quiz": "Genera cuestionarios.",
    "create_reading_plan": "Diseña un plan de lectura.",
    "create_report_finding": "Genera hallazgos en un informe.",
    "create_security_update": "Crea actualizaciones de seguridad.",
    "create_show_intro": "Genera introducciones para programas o podcasts.",
    "create_stride_threat_model": "Genera modelos de amenazas basados en STRIDE.",
    "create_summary": "Genera resúmenes en general.",
    "create_threat_scenarios": "Crea escenarios de amenazas.",
    "create_upgrade_pack": "Probablemente crea paquetes de actualización.",
    "create_video_chapters": "Segmenta un video en capítulos.",
    "create_visualization": "Genera visualizaciones de datos.",
    "extract_algorithm_update_recommendations": "Extrae recomendaciones para actualizar algoritmos.",
    "extract_article_wisdom": "Extrae ideas clave de un artículo.",
    "extract_book_ideas": "Extrae ideas de un libro.",
    "extract_book_recommendations": "Extrae recomendaciones de libros.",
    "extract_business_ideas": "Identifica ideas de negocio en textos.",
    "extract_extraordinary_claims": "Identifica afirmaciones extraordinarias (posible verificación de hechos).",
    "extract_ideas": "Extrae ideas clave en general.",
    "extract_insights": "Extrae información relevante.",
    "extract_main_idea": "Encuentra la idea principal de un texto.",
    "extract_patterns": "Detecta patrones en datos o texto.",
    "extract_poc": "Extrae pruebas de concepto (PoC).",
    "extract_predictions": "Extrae predicciones de un texto.",
    "extract_questions": "Identifica preguntas en un texto.",
    "extract_recommendations": "Extrae recomendaciones.",
    "extract_references": "Extrae referencias bibliográficas o enlaces.",
    "extract_song_meaning": "Analiza el significado de una canción.",
    "extract_sponsors": "Extrae patrocinadores de un documento o video.",
    "extract_videoid": "Extrae el ID de un video (probablemente de YouTube).",
    "extract_wisdom": "Extrae conocimiento o sabiduría de un texto.",
    "find_hidden_message": "Encuentra mensajes ocultos en un texto.",
    "find_logical_fallacies": "Detecta falacias lógicas en un argumento.",
    "get_wow_per_minute": "Quizás mide cuántas veces alguien dice 'wow' por minuto en un video.",
    "improve_academic_writing": "Mejora la escritura académica.",
    "improve_prompt": "Mejora prompts para IA.",
    "improve_report_finding": "Mejora hallazgos en un informe.",
    "improve_writing": "Mejora la escritura en general.",
    "label_and_rate": "Etiqueta y califica contenido.",
    "rate_ai_response": "Califica respuestas generadas por IA.",
    "rate_ai_result": "Evalúa resultados de IA.",
    "rate_content": "Evalúa la calidad de un contenido.",
    "rate_value": "Evalúa el valor de algo.",
    "raw_query": "Probablemente ejecuta consultas en bruto (SQL, API, etc.).",
    "recommend_artists": "Recomienda artistas (música, arte, etc.).",
    "show_fabric_options_markmap": "Muestra opciones en formato Markmap.",
    "summarize": "Resume información.",
    "summarize_debate": "Resume debates.",
    "summarize_git_changes": "Resume cambios en un repositorio Git.",
    "summarize_git_diff": "Resume diferencias entre versiones de código.",
    "summarize_micro": "Genera un resumen muy breve.",
    "summarize_newsletter": "Resume boletines informativos.",
    "summarize_paper": "Resume artículos académicos.",
    "summarize_pull-requests": "Resume solicitudes de extracción en Git.",
    "summarize_rpg_session": "Resume sesiones de juegos de rol.",
    "to_flashcards": "Convierte información en tarjetas de estudio.",
    "tweet": "Genera tweets.",
    "write_essay": "Escribe ensayos.",
    "write_micro_essay": "Escribe micro-ensayos.",
    "write_nuclei_template_rule": "Escribe reglas para Nuclei (herramienta de seguridad).",
    "write_pull-request": "Genera solicitudes de extracción (pull requests) en Git.",
    "write_semgrep_rule": "Crea reglas para Semgrep (análisis de código estático).",
    "coding_master": "Posiblemente ayuda en programación o generación de código.",
    "explain_code": "Explica fragmentos de código.",
    "explain_docs": "Explica documentación técnica.",
    "explain_project": "Resume o explica proyectos.",
    "explain_terms": "Explica términos específicos.",
    "summarize_rpg_session": "Resume sesiones de juegos de rol.",
}

# Función para analizar el texto y sugerir la función de Fabric (con más precisión)
def suggest_fabric_function_refined(text, descriptions):
    """Analiza el texto y sugiere la función de Fabric más adecuada basándose en sus descripciones."""

    text = text.lower()
    best_match = None
    max_score = 0

    for function, description in descriptions.items():
        score = 0
        description_lower = description.lower()

        # Buscar palabras clave específicas en la descripción y el texto
        keywords = function.split('_') # Separar el nombre de la función por guiones bajos

        # Ponderar las palabras clave de la función
        for keyword in keywords:
            if keyword in text:
                score += 2  # Dar más peso a las palabras clave del nombre de la función

        # Buscar palabras clave importantes de la descripción
        important_words = re.findall(r'\b\w+\b', description_lower) # Obtener todas las palabras
        for word in important_words:
            if word in text:
                score += 1

        # Considerar frases clave de la descripción (puedes añadir más)
        if "análisis de" in description_lower and "análisis de" in text:
            score += 3
        if "genera" in description_lower and "genera" in text:
            score += 2
        if "extrae" in description_lower and "extrae" in text:
            score += 2
        if "resume" in description_lower and "resume" in text:
            score += 2
        if "evalúa" in description_lower and "evalúa" in text:
            score += 2
        if "identifica" in description_lower and "identifica" in text:
            score += 2
        if "mejora" in description_lower and "mejora" in text:
            score += 2
        if "crea" in description_lower and "crea" in text:
            score += 2
        if "explica" in description_lower and "explica" in text:
            score += 2
        if "recomienda" in description_lower and "recomienda" in text:
            score += 2
        if "detecta" in description_lower and "detecta" in text:
            score += 2
        if "califica" in description_lower and "califica" in text:
            score += 2

        # Criterios más específicos basados en las descripciones
        if function == "analyze_answers" and ("respuesta" in text or "contesta" in text) and ("precisión" in text or "calidad" in text):
            score += 3
        elif function == "analyze_claims" and ("afirmación" in text or "argumento" in text) and ("verificar" in text or "veracidad" in text):
            score += 3
        elif function == "analyze_debate" and ("debate" in text or "discusión" in text) and ("argumento" in text or "postura" in text):
            score += 3
        elif function == "analyze_incident" and ("incidente" in text or "crisis" in text) and ("seguridad" in text or "revisión" in text):
            score += 3
        # ... (añade más condiciones específicas para cada función basándote en su descripción)
        elif function == "analyze_logs" and ("log" in text or "registro" in text) and ("depuración" in text or "seguridad informática" in text):
            score += 3
        elif function == "analyze_malware" and ("malware" in text or "amenaza" in text) and ("vulnerabilidad" in text or "detectar" in text):
            score += 3
        elif function == "analyze_paper" and ("artículo" in text or "documento técnico" in text or "académico" in text):
            score += 3
        elif function == "analyze_patent" and "patente" in text and ("revisión" in text or "análisis" in text):
            score += 3
        elif function == "analyze_personality" and ("personalidad" in text or "rasgos" in text) and ("psicológico" in text or "evaluación" in text):
            score += 3
        elif function == "analyze_presentation" and ("presentación" in text or "diapositivas" in text) and ("calidad" in text or "examina" in text):
            score += 3
        elif function == "analyze_prose" and "prosa" in text and ("estilo" in text or "coherencia" in text or "gramática" in text):
            score += 3
        elif function == "analyze_spiritual_text" and ("espiritual" in text or "religioso" in text) and "texto" in text:
            score += 3
        elif function == "analyze_tech_impact" and ("tecnología" in text or "impacto" in text) and ("ámbito" in text or "evalúa" in text):
            score += 3
        elif function == "analyze_threat_report" and ("amenaza" in text or "ciberseguridad" in text) and ("informe" in text or "reporte" in text):
            score += 3
        elif function == "analyze_threat_report_trends" and ("amenaza" in text or "ciberseguridad" in text) and ("informe" in text or "reporte" in text) and ("tendencia" in text or "identifica" in text):
            score += 3
        elif function == "answer_interview_question" and ("entrevista" in text or "pregunta" in text) and ("responder" in text or "contestar" in text):
            score += 3
        elif function == "create_5_sentence_summary" and ("resumen" in text or "sumario" in text) and ("5 frases" in text or "cinco frases" in text):
            score += 3
        elif function == "create_academic_paper" and ("artículo académico" in text or "investigación" in text) and "genera" in text:
            score += 3
        # ... (continúa añadiendo condiciones específicas para el resto de las funciones)
        elif function == "create_summary" and ("resumen" in text or "sumario" in text) and "genera" in text:
            score += 3
        elif function == "extract_ideas" and "idea" in text and ("extrae" in text or "identifica" in text or "obtener" in text):
            score += 3
        elif function == "extract_insights" and ("información relevante" in text or "conocimiento" in text) and ("extrae" in text or "identifica" in text):
            score += 3
        elif function == "explain_code" and ("código" in text or "programa" in text) and ("explica" in text or "entender" in text):
            score += 3
        elif function == "explain_docs" and ("documentación" in text or "manual" in text) and ("explica" in text or "entender" in text):
            score += 3
        elif function == "summarize" and ("resumen" in text or "sumario" in text) and ("información" in text or "texto" in text):
            score += 3

        if score > max_score:
            max_score = score
            best_match = function

    return best_match if best_match else "No se pudo determinar una función específica con los criterios actuales."

# Sugerir la función de Fabric (usando la lógica refinada)
suggested_function = suggest_fabric_function_refined(extracted_text, fabric_descriptions)
print(f"\nBasado en el análisis del texto, la función de Fabric sugerida es: {suggested_function}")

# Opcional: Podrías intentar ejecutar la función aquí si tuvieras la integración con Fabric en este entorno.
# Por ejemplo (esto es solo un ejemplo conceptual y requeriría la implementación real de las funciones de Fabric):
# if suggested_function == "create_summary":
#     from fabric_integration import create_summary  # Imagina que tienes un módulo así
#     summary = create_summary(extracted_text)
#     print("\nResultado de la función:")
#     print(summary)

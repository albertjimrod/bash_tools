import os
import json
import tarfile
import markdown
import subprocess
import tempfile
from pdfminer.high_level import extract_text
from PIL import Image
import pytesseract
from odf.opendocument import load
from odf.text import P
import re
import requests

def extract_text_from_pdf(pdf_path):
    try:
        return extract_text(pdf_path)
    except Exception as e:
        print(f"Error al extraer texto del PDF {pdf_path}: {e}")
        return ""

def extract_text_from_image(image_path):
    try:
        return pytesseract.image_to_string(Image.open(image_path))
    except Exception as e:
        print(f"Error al extraer texto de la imagen {image_path}: {e}")
        return ""

def extract_text_from_odt(odt_path):
    try:
        doc = load(odt_path)
        paragraphs = doc.getElementsByType(P)
        text_parts = []
        
        for p in paragraphs:
            paragraph_text = ""
            for child in p.childNodes:
                if hasattr(child, 'data'):
                    paragraph_text += child.data
            text_parts.append(paragraph_text)
            
        return "\n".join(text_parts)
    except Exception as e:
        print(f"Error al extraer texto del ODT {odt_path}: {e}")
        return ""

def extract_text_from_jex(jex_path, extract_folder):
    try:
        os.makedirs(extract_folder, exist_ok=True)
        with tarfile.open(jex_path, 'r') as tar:
            tar.extractall(path=extract_folder)
        
        notes = []
        for root, _, files in os.walk(extract_folder):
            for file in files:
                if file.endswith('.json'):
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        try:
                            data = json.load(f)
                            if 'body' in data:
                                notes.append({
                                    "titulo": data.get("title", "Nota sin título"),
                                    "contenido": data["body"]
                                })
                        except json.JSONDecodeError:
                            print(f"Error al decodificar JSON en {os.path.join(root, file)}")
        return notes
    except Exception as e:
        print(f"Error al procesar el archivo JEX {jex_path}: {e}")
        return []

def process_file(file_path):
    ext = file_path.split('.')[-1].lower()
    if ext in ['txt', 'md']:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
            return {"titulo": os.path.basename(file_path).split('.')[0], "contenido": text}
    elif ext == 'pdf':
        text = extract_text_from_pdf(file_path)
        return {"titulo": os.path.basename(file_path).split('.')[0], "contenido": text}
    elif ext in ['jpg', 'png', 'jpeg']:
        text = extract_text_from_image(file_path)
        return {"titulo": os.path.basename(file_path).split('.')[0], "contenido": text}
    elif ext == 'odt':
        text = extract_text_from_odt(file_path)
        return {"titulo": os.path.basename(file_path).split('.')[0], "contenido": text}
    elif ext == 'jex':
        return extract_text_from_jex(file_path, "./extracted_jex")
    else:
        print(f"Formato no soportado: {file_path}")
        return None

def translate_to_spanish(text):
    """
    Función para traducir texto a español si está en otro idioma.
    Esta es una implementación simple - puedes usar un servicio externo más avanzado.
    """
    try:
        # Heurística simple: si más del 50% de palabras son en inglés, traducir
        english_words = ["the", "and", "in", "to", "of", "a", "for", "is", "on", "that", "by", "this", "with", "you", "it"]
        words = re.findall(r'\b\w+\b', text.lower())
        
        if not words:
            return text
            
        english_count = sum(1 for word in words if word in english_words)
        
        # Si parece estar en inglés u otro idioma no español
        if english_count / len(words) > 0.2 and len(words) > 10:
            print("Detectado texto en idioma no español. Intentando traducir...")
            
            # Opción 1: Usar Fabric para traducir (modelo de LLM)
            with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', suffix='.txt', delete=False) as temp_file:
                temp_file.write(f"Traduce el siguiente texto al español:\n\n{text}")
                temp_file_path = temp_file.name
            
            cmd = f'cat "{temp_file_path}" | fabric --model deepseek-r1:14b'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            os.unlink(temp_file_path)
            
            if result.returncode == 0:
                # Intentar extraer solo la traducción
                output = result.stdout
                
                # Buscar patrones comunes de respuesta
                matches = re.search(r'(?:Traducción:|Texto traducido:|En español:)\s*([\s\S]+)', output, re.IGNORECASE)
                if matches:
                    return matches.group(1).strip()
                
                # Si no encuentra patrones específicos, tomar la última parte de la respuesta
                lines = output.strip().split('\n')
                if len(lines) > 3:  # Ignorar posibles líneas de proceso de pensamiento
                    return '\n'.join(lines[-len(text.split('\n')):])
                
                return output.strip()
        
        # Si no parece estar en otro idioma, devolver el texto original
        return text
        
    except Exception as e:
        print(f"Error al traducir: {e}")
        return text  # En caso de error, devolver el texto original

def analyze_with_fabric_cli(text, title="", analysis_type="auto"):
    fabric_param = None

    if analysis_type == "code":
        fabric_param = "explain_code"
    elif analysis_type == "academic":
        fabric_param = "analyze_paper"
    elif analysis_type == "summary":
        fabric_param = "create_summary"
    elif analysis_type == "prose":
        fabric_param = "analyze_prose"
    elif analysis_type == "auto":
        is_code = re.search(r'(def |class |import |function|public class|async |\.map\(|\.filter\()', text) is not None
        is_academic = re.search(r'(Abstract|Introduction|Methodology|Conclusion|References|Fig\. \d|Table \d)', text) is not None

        if is_code:
            fabric_param = "explain_code"
        elif is_academic:
            fabric_param = "analyze_paper"
        elif len(text.split()) > 1000:
            fabric_param = "create_summary"
        else:
            fabric_param = "analyze_prose"
    else:
        print(f"Tipo de análisis no válido: {analysis_type}. Usando análisis automático.")

    if fabric_param:
        print(f"Usando el parámetro de Fabric: {fabric_param}")

        cmd = ['fabric', '--model', 'deepseek-r1:14b', '-sp', fabric_param]

        try:
            result = subprocess.run(cmd, input=text, capture_output=True, text=True, check=True)
            output = result.stdout.strip()

            print("--- Salida de Fabric: ---")
            print(output)

            # Para depuración: guardar la salida completa en un archivo
            with open("debug_fabric_output.txt", "w", encoding="utf-8") as f:
                f.write(output)

            if fabric_param == "create_summary":
                return process_summary_output(output)
            elif fabric_param == "analyze_paper":
                return process_paper_analysis(output)
            elif fabric_param == "explain_code":
                return process_code_explanation(output)
            else:
                return process_prose_analysis(output)

        except subprocess.CalledProcessError as e:
            print("--- Error al ejecutar Fabric: ---")
            print(f"Código de retorno: {e.returncode}")
            print(f"Salida estándar: {e.stdout}")
            print(f"Salida de error: {e.stderr}")
            return {"temas": [], "resumen": "Error en el análisis", "notas_relacionadas": []}
        except FileNotFoundError:
            print("Error: El comando 'fabric' no se encontró. Asegúrate de que esté en tu PATH.")
            return {"temas": [], "resumen": "Error: 'fabric' no encontrado", "notas_relacionadas": []}
        except Exception as e:
            print(f"Error inesperado al ejecutar Fabric: {e}")
            return {"temas": [], "resumen": f"Error inesperado: {str(e)}", "notas_relacionadas": []}

    else:
        print("No se seleccionó un tipo de análisis válido.")
        return {"temas": [], "resumen": "No se seleccionó un tipo de análisis válido", "notas_relacionadas": []}

def process_summary_output(output):
    """Procesa la salida del parámetro create_summary"""
    # Extraer resumen
    resumen = output.strip()
    
    # Extraer conceptos clave
    temas = []
    
    # Buscar secciones de "Puntos clave", "Ideas principales", etc.
    section_matches = re.search(r'(?:Puntos clave|Ideas principales|Conceptos clave|Temas principales)[:]\s*([\s\S]*?)(?=\n\n|$)', output, re.IGNORECASE)
    if section_matches:
        section_text = section_matches.group(1).strip()
        # Buscar puntos enumerados o con viñetas
        points = re.findall(r'(?:^|\n)(?:[•\-\*]|\d+\.)\s+(.*?)(?=\n[•\-\*]|\n\d+\.|\n\n|$)', section_text, re.DOTALL)
        temas.extend([p.strip() for p in points if p.strip()])
    
    # Si no se encontraron temas en secciones específicas, buscar frases o sentencias importantes
    if not temas:
        # Identificar frases con palabras clave como "importante", "fundamental", "clave", etc.
        key_phrases = re.findall(r'(?:important[e]|fundamental|clave|principal|esencial)[^.!?]*[.!?]', output, re.IGNORECASE)
        temas.extend([phrase.strip() for phrase in key_phrases[:5]])
    
    # Asegurar que tenemos al menos algunos temas
    if len(temas) < 3:
        # Extraer frases del principio del resumen que parezcan temáticas
        first_sentences = re.findall(r'[^.!?]+[.!?]', resumen)[:5]
        for sentence in first_sentences:
            if len(sentence.split()) > 3 and len(sentence.split()) < 20 and sentence not in temas:
                temas.append(sentence.strip())
            if len(temas) >= 5:
                break
    
    return {
        "temas": temas[:5],  # Limitar a 5 temas
        "resumen": resumen,
        "notas_relacionadas": []
    }

def process_paper_analysis(output):
    """Procesa la salida del parámetro analyze_paper"""
    # Extraer resumen
    resumen = output.strip()
    
    # Buscar secciones específicas para artículos académicos
    temas = []
    
    # Buscar la sección de resultados o conclusiones
    findings_match = re.search(r'(?:Resultados|Conclusiones|Hallazgos|Findings)[:]\s*([\s\S]*?)(?=\n\n|$)', output, re.IGNORECASE)
    if findings_match:
        findings = findings_match.group(1).strip()
        # Extraer puntos clave de los resultados
        points = re.findall(r'(?:^|\n)(?:[•\-\*]|\d+\.)\s+(.*?)(?=\n[•\-\*]|\n\d+\.|\n\n|$)', findings, re.DOTALL)
        temas.extend([p.strip() for p in points if p.strip()])
    
    # Buscar la sección de metodología o enfoque
    method_match = re.search(r'(?:Metodología|Método|Enfoque|Approach)[:]\s*([\s\S]*?)(?=\n\n|$)', output, re.IGNORECASE)
    if method_match:
        method = method_match.group(1).strip()
        # Extraer puntos clave de la metodología
        temas.append(f"Metodología: {method.split('.')[0].strip()}")
    
    # Asegurar que tenemos suficientes temas
    if len(temas) < 5:
        # Buscar frases con términos académicos como "estudio", "análisis", "investigación", etc.
        academic_phrases = re.findall(r'(?:estudio|análisis|investigación|experimento|teoría)[^.!?]*[.!?]', output, re.IGNORECASE)
        for phrase in academic_phrases:
            if phrase.strip() not in temas:
                temas.append(phrase.strip())
            if len(temas) >= 5:
                break
    
    return {
        "temas": temas[:5],
        "resumen": resumen,
        "notas_relacionadas": []
    }

def process_code_explanation(output):
    """Procesa la salida del parámetro explain_code"""
    # Extraer resumen
    resumen = output.strip()
    
    # Buscar secciones específicas para código
    temas = []
    
    # Buscar funciones o clases mencionadas
    functions = re.findall(r'(?:función|function|método|class|clase)\s+`?(\w+)`?', output, re.IGNORECASE)
    temas.extend([f"Función/Clase: {func}" for func in functions[:3]])
    
    # Buscar propósito o funcionalidad principal
    purpose_match = re.search(r'(?:El código|Este programa|El script|La aplicación)\s+([^.!?]+)[.!?]', output, re.IGNORECASE)
    if purpose_match:
        temas.append(f"Propósito: {purpose_match.group(1).strip()}")
    
    # Buscar tecnologías o librerías mencionadas
    libraries = re.findall(r'(?:utiliza|usa|importa|librería|biblioteca|framework)\s+(\w+)', output, re.IGNORECASE)
    if libraries:
        temas.append(f"Tecnologías: {', '.join(libraries[:3])}")
    
    # Asegurar que tenemos suficientes temas
    if len(temas) < 5:
        # Buscar frases con términos técnicos como "algoritmo", "implementa", "procesa", etc.
        tech_phrases = re.findall(r'(?:algoritmo|implementa|procesa|ejecuta|calcula)[^.!?]*[.!?]', output, re.IGNORECASE)
        for phrase in tech_phrases:
            if phrase.strip() not in temas:
                temas.append(phrase.strip())
            if len(temas) >= 5:
                break
    
    return {
        "temas": temas[:5],
        "resumen": resumen,
        "notas_relacionadas": []
    }

def process_prose_analysis(output):
    """Procesa la salida del parámetro analyze_prose"""
    # Extraer resumen
    resumen = output.strip()
    
    # Buscar temas o conceptos clave
    temas = []
    
    # Buscar secciones de análisis
    themes_match = re.search(r'(?:Temas|Conceptos|Ideas principales|Análisis)[:]\s*([\s\S]*?)(?=\n\n|$)', output, re.IGNORECASE)
    if themes_match:
        themes_section = themes_match.group(1).strip()
        # Extraer puntos enumerados o con viñetas
        points = re.findall(r'(?:^|\n)(?:[•\-\*]|\d+\.)\s+(.*?)(?=\n[•\-\*]|\n\d+\.|\n\n|$)', themes_section, re.DOTALL)
        temas.extend([p.strip() for p in points if p.strip()])
    
    # Si no se encontraron temas específicos, buscar frases clave
    if not temas:
        # Extraer oraciones cortas que parezcan temáticas
        sentences = re.findall(r'[^.!?]{15,100}[.!?]', resumen)
        for sentence in sentences:
            if len(sentence.split()) > 3 and len(sentence.split()) < 15:
                temas.append(sentence.strip())
            if len(temas) >= 5:
                break
    
    # Si aún necesitamos más temas, buscar frases con palabras clave
    if len(temas) < 5:
        key_concept_phrases = re.findall(r'(?:concepto|idea|tema|aspecto|característica)[^.!?]*[.!?]', output, re.IGNORECASE)
        for phrase in key_concept_phrases:
            if phrase.strip() not in temas:
                temas.append(phrase.strip())
            if len(temas) >= 5:
                break
    
    return {
        "temas": temas[:5],
        "resumen": resumen,
        "notas_relacionadas": []
    }

def create_markdown_file(data, output_folder):
    # Sanitizar el título para usarlo como nombre de archivo
    file_name = re.sub(r'[^\w\s-]', '', data['titulo']).replace(' ', '_') + '.md'
    file_path = os.path.join(output_folder, file_name)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"---\n")
        
        # Asegurarse de que los temas sean strings para evitar errores de codificación JSON
        clean_temas = [str(tema) for tema in data['temas']]
        f.write(f"tags: {json.dumps(clean_temas)}\n")
        
        clean_relaciones = [str(rel) for rel in data['notas_relacionadas']]
        f.write(f"relaciones: {json.dumps(clean_relaciones)}\n")
        f.write(f"---\n\n")
        f.write(f"# {data['titulo']}\n\n")
        f.write(f"{data['resumen']}\n\n")
        
        if data['temas']:
            f.write(f"## Conceptos clave\n")
            for concepto in data['temas']:
                f.write(f"- {concepto}\n")
        
        if data['notas_relacionadas']:
            f.write(f"\n## Relacionado\n")
            for relacion in data['notas_relacionadas']:
                f.write(f"- [[{relacion}]]\n")
    
    print(f"Nota creada: {file_path}")

def main():
    input_folder = "./input_docs"
    output_folder = "./obsidian_vault"

    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)

    analysis_choice = input("Elige el tipo de análisis ('auto', 'code', 'academic', 'summary', 'prose'): ").lower()

    for file_name in os.listdir(input_folder):
        file_path = os.path.join(input_folder, file_name)

        if file_name.startswith('.~lock.'):
            print(f"Ignorando archivo de bloqueo: {file_name}")
            continue

        if os.path.isfile(file_path):
            print(f"Procesando: {file_name}")
            result = process_file(file_path)

            if result is None:
                continue

            if isinstance(result, list):
                for note in result:
                    try:
                        print(f"Analizando nota: {note['titulo']}")
                        analysis_result = analyze_with_fabric_cli(note['contenido'], note['titulo'], analysis_choice)
                        if analysis_result and analysis_result["resumen"]:
                            analysis_result["resumen"] = translate_to_spanish(analysis_result["resumen"])
                        if analysis_result and analysis_result["temas"]:
                            analysis_result["temas"] = [translate_to_spanish(tema) for tema in analysis_result["temas"]]
                        if analysis_result:
                            note_data = {
                                "titulo": note['titulo'],
                                "temas": analysis_result.get("temas", []),
                                "resumen": analysis_result.get("resumen", ""),
                                "notas_relacionadas": analysis_result.get("notas_relacionadas", [])
                            }
                            create_markdown_file(note_data, output_folder)
                    except Exception as e:
                        print(f"Error al procesar nota {note['titulo']}: {e}")
            else:
                try:
                    print(f"Analizando: {result['titulo']}")
                    analysis_result = analyze_with_fabric_cli(result['contenido'], result['titulo'], analysis_choice)
                    if analysis_result and analysis_result["resumen"]:
                        analysis_result["resumen"] = translate_to_spanish(analysis_result["resumen"])
                    if analysis_result and analysis_result["temas"]:
                        analysis_result["temas"] = [translate_to_spanish(tema) for tema in analysis_result["temas"]]
                    if analysis_result:
                        note_data = {
                            "titulo": result['titulo'],
                            "temas": analysis_result.get("temas", []),
                            "resumen": analysis_result.get("resumen", ""),
                            "notas_relacionadas": analysis_result.get("notas_relacionadas", [])
                        }
                        create_markdown_file(note_data, output_folder)
                except Exception as e:
                    print(f"Error al procesar {file_name}: {e}")

if __name__ == "__main__":
    main()

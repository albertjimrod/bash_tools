import os
import subprocess
import tempfile
import re
import json  # Importar la biblioteca json
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
        print(f"extract_text_from_pdf: Iniciando extracción de {pdf_path}")
        text = extract_text(pdf_path)
        print(f"extract_text_from_pdf: Extracción completada de {pdf_path}. Primeros 100 caracteres: {text[:100]}")
        return text
    except Exception as e:
        print(f"extract_text_from_pdf: Error al extraer texto del PDF {pdf_path}: {e}")
        return ""

def extract_text_from_image(image_path):
    try:
        print(f"extract_text_from_image: Iniciando extracción de {image_path}")
        text = pytesseract.image_to_string(Image.open(image_path))
        print(f"extract_text_from_image: Extracción completada de {image_path}. Primeros 100 caracteres: {text[:100]}")
        return text
    except Exception as e:
        print(f"extract_text_from_image: Error al extraer texto de la imagen {image_path}: {e}")
        return ""

def extract_text_from_odt(odt_path):
    try:
        print(f"extract_text_from_odt: Iniciando extracción de {odt_path}")
        doc = load(odt_path)
        paragraphs = doc.getElementsByType(P)
        text_parts = []

        for p in paragraphs:
            paragraph_text = ""
            for child in p.childNodes:
                if hasattr(child, 'data'):
                    paragraph_text += child.data
            text_parts.append(paragraph_text)

        text = "\n".join(text_parts)
        print(f"extract_text_from_odt: Extracción completada de {odt_path}. Primeros 100 caracteres: {text[:100]}")
        return text
    except Exception as e:
        print(f"extract_text_from_odt: Error al extraer texto del ODT {odt_path}: {e}")
        return ""

def extract_text_from_jex(jex_path, extract_folder):
    try:
        print(f"extract_text_from_jex: Iniciando extracción de {jex_path}")
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
                            print(f"extract_text_from_jex: Error al decodificar JSON en {os.path.join(root, file)}")
        print(f"extract_text_from_jex: Extracción completada de {jex_path}. Número de notas: {len(notes)}")
        return notes
    except Exception as e:
        print(f"extract_text_from_jex: Error al procesar el archivo JEX {jex_path}: {e}")
        return []

def process_file(file_path):
    print(f"process_file: Procesando archivo: {file_path}")
    ext = file_path.split('.')[-1].lower()
    print(f"process_file: Extensión del archivo: {ext}")
    if ext in ['txt', 'md']:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        print(f"process_file: Archivo de texto leído. Primeros 100 caracteres: {text[:100]}")
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
        print(f"process_file: Formato no soportado: {file_path}")
        return None

def translate_to_spanish(text):
    try:
        english_words = ["the", "and", "in", "to", "of", "a", "for", "is", "on", "that", "by", "this", "with", "you", "it"]
        words = re.findall(r'\b\w+\b', text.lower())

        if not words:
            return text

        english_count = sum(1 for word in words if word in english_words)

        if english_count / len(words) > 0.2 and len(words) > 10:
            print("translate_to_spanish: Detectado texto en idioma no español. Intentando traducir...")

            with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', suffix='.txt', delete=False) as temp_file:
                temp_file.write(f"Traduce el siguiente texto al español:\n\n{text}")
                temp_file_path = temp_file.name

            cmd = f'cat "{temp_file_path}" | fabric --model deepseek-r1:14b'
            print(f"translate_to_spanish: Comando de traducción: {cmd}")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            os.unlink(temp_file_path)

            print(f"translate_to_spanish: Código de retorno de Fabric: {result.returncode}")
            print(f"translate_to_spanish: Salida estándar de Fabric:\n{result.stdout}")
            print(f"translate_to_spanish: Salida de error de Fabric:\n{result.stderr}")

            if result.returncode == 0:
                output = result.stdout
                matches = re.search(r'(?:Traducción:|Texto traducido:|En español:)\s*([\s\S]+)', output, re.IGNORECASE)
                if matches:
                    translated_text = matches.group(1).strip()
                    print(f"translate_to_spanish: Texto traducido encontrado: {translated_text[:100]}...")
                    return translated_text
                lines = output.strip().split('\n')
                if len(lines) > 3:
                    translated_text = '\n'.join(lines[-len(text.split('\n')):])
                    print(f"translate_to_spanish: Texto traducido (últimas líneas): {translated_text[:100]}...")
                    return translated_text
                translated_text = output.strip()
                print(f"translate_to_spanish: Texto traducido (salida completa): {translated_text[:100]}...")
                return translated_text
            else:
                print("translate_to_spanish: Error en la traducción con Fabric.")
                return text  # Devolver el texto original en caso de error de traducción

        return text

    except Exception as e:
        print(f"translate_to_spanish: Error al traducir: {e}")
        return text

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

            with open("debug_fabric_output.txt", "w", encoding="utf-8") as f:
                f.write(output)

            analysis_result = process_fabric_output(output, fabric_param)
            return analysis_result

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

def process_fabric_output(output, fabric_param):
    """Procesa la salida de Fabric y extrae la información relevante."""

    resumen = ""
    temas = []

    output = re.sub(r"^(Okay,|Certainly,|Alright,|Sure,|Yes,|No problem,|I'm happy to help!)", "", output, flags=re.IGNORECASE)
    output = re.sub(r"^(Please go ahead and share your content,|Here's the analysis:|Here is the summary:)", "", output, flags=re.IGNORECASE)

    resumen_match = re.search(r"(ONE SENTENCE SUMMARY:\s*(.*?)\n)", output, re.IGNORECASE)
    if resumen_match:
        resumen = resumen_match.group(2).strip()
    else:
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', output)
        resumen = " ".join(sentences[:2])

    temas_match = re.search(r"(MAIN POINTS:\s*(.*?)\n)", output, re.IGNORECASE)
    if temas_match:
        temas_text = temas_match.group(2).strip()
        temas = re.findall(r"\d+\.\s*(.*?)(?:\n|$)", temas_text)

    if not temas:
        temas_match = re.search(r"(TAKEAWAYS:\s*(.*?)\n)", output, re.IGNORECASE)
        if temas_match:
            temas_text = temas_match.group(2).strip()
            temas = re.findall(r"\d+\.\s*(.*?)(?:\n|$)", temas_text)

    if not temas:
        temas = re.findall(r"[-*]\s*(.*?)(?:\n|$)", output)

    temas = temas[:5]

    return {
        "temas": temas,
        "resumen": resumen,
        "notas_relacionadas": []
    }

def create_markdown_file(data, output_folder):
    # Sanitizar el título para usarlo como nombre de archivo
    file_name = re.sub(r'[^\w\s-]', '', data['titulo']).replace(' ', '_') + '.md'
    file_path = os.path.join(output_folder, file_name)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"---\n")
        clean_temas = [str(tema) for tema in data['temas']]
        f.write(f"tags: {json.dumps(clean_temas, ensure_ascii=False)}\n")
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
    print(f"main: Opción de análisis elegida: {analysis_choice}")

    for file_name in os.listdir(input_folder):
        file_path = os.path.join(input_folder, file_name)
        print(f"main: Procesando archivo: {file_path}")

        if file_name.startswith('.~lock.'):
            print(f"main: Ignorando archivo de bloqueo: {file_name}")
            continue

        if os.path.isfile(file_path):
            print(f"main: El archivo es un fichero.")
            result = process_file(file_path)
            print(f"main: Resultado de process_file: {result}")

            if result is None:
                print(f"main: process_file devolvió None, continuando.")
                continue

            if isinstance(result, list):
                print(f"main: El resultado es una lista de notas.")
                for note in result:
                    try:
                        print(f"main: Analizando nota: {note['titulo']}")
                        analysis_result = analyze_with_fabric_cli(note['contenido'], note['titulo'], analysis_choice)
                        # if analysis_result and analysis_result["resumen"]:
                        #     analysis_result["resumen"] = translate_to_spanish(analysis_result["resumen"])
                        # if analysis_result and analysis_result["temas"]:
                        #     analysis_result["temas"] = [translate_to_spanish(tema) for tema in analysis_result["temas"]]
                        if analysis_result:
                            note_data = {
                                "titulo": note['titulo'],
                                "temas": analysis_result.get("temas", []),
                                "resumen": analysis_result.get("resumen", ""),
                                "notas_relacionadas": analysis_result.get("notas_relacionadas", [])
                            }
                            create_markdown_file(note_data, output_folder)
                    except Exception as e:
                        print(f"main: Error al procesar nota {note['titulo']}: {e}")
            else:
                print(f"main: El resultado es una sola nota.")
                try:
                    print(f"main: Analizando: {result['titulo']}")
                    analysis_result = analyze_with_fabric_cli(result['contenido'], result['titulo'], analysis_choice)
                    # if analysis_result and analysis_result["resumen"]:
                    #     analysis_result["resumen"] = translate_to_spanish(analysis_result["resumen"])
                    # if analysis_result and analysis_result["temas"]:
                    #     analysis_result["temas"] = [translate_to_spanish(tema) for tema in analysis_result["temas"]]
                    if analysis_result:
                        note_data = {
                            "titulo": result['titulo'],
                            "temas": analysis_result.get("temas", []),
                            "resumen": analysis_result.get("resumen", ""),
                            "notas_relacionadas": analysis_result.get("notas_relacionadas", [])
                        }
                    create_markdown_file(note_data, output_folder)
                except Exception as e:
                    print(f"main: Error al procesar {file_name}: {e}")

if __name__ == "__main__":
    main()

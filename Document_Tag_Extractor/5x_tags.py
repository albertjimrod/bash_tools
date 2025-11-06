import readline
import os
import re  # Importar la librería de expresiones regulares
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.llms import Ollama

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

# Dividir el texto en fragmentos (opcional, pero útil para documentos grandes)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = text_splitter.split_text(extracted_text)

# Configurar embeddings con Ollama (esto sigue siendo útil si quieres usar los embeddings para otras tareas)
embeddings = OllamaEmbeddings(model="phi3")

# Crear el almacén vectorial FAISS (opcional, dependiendo de si necesitas realizar búsquedas semánticas)
vector_store = FAISS.from_texts(chunks, embeddings)
print("Vector store creado exitosamente.")
print(vector_store)

# Configurar el modelo de lenguaje Ollama
llm = Ollama(model="phi3")

# Crear un prompt para pedirle al modelo que extraiga las etiquetas (palabras clave) del texto extraído
prompt = f"""Por favor, extrae las palabras clave o frases cortas más relevantes del siguiente texto. Estas etiquetas deben representar los temas principales del documento.

{extracted_text}

Devuelve una lista de estas etiquetas separadas por comas."""

# Ejecutar el modelo de lenguaje para obtener las etiquetas
tags_output = llm.invoke(prompt)

# Imprimir las etiquetas extraídas
print("\nEtiquetas extraídas:")
tags_list = [tag.strip() for tag in tags_output.split(',')]
for tag in tags_list:
    print(f"- {tag}")

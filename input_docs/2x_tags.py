import readline
import os
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
        document_text = f.read()
except FileNotFoundError:
    print(f"Error: El archivo en la ruta '{ruta_archivo}' no fue encontrado.")
    exit()
except Exception as e:
    print(f"Ocurrió un error al leer el archivo: {e}")
    exit()

# Dividir el texto en fragmentos (opcional, pero útil para documentos grandes)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = text_splitter.split_text(document_text)

# Configurar embeddings con Ollama (esto sigue siendo útil si quieres usar los embeddings para otras tareas)
embeddings = OllamaEmbeddings(model="phi3")

# Crear el almacén vectorial FAISS (opcional, dependiendo de si necesitas realizar búsquedas semánticas)
vector_store = FAISS.from_texts(chunks, embeddings)
print("Vector store creado exitosamente.")
print(vector_store)

# Configurar el modelo de lenguaje Ollama
llm = Ollama(model="phi3")

# Crear un prompt para pedirle al modelo que extraiga las etiquetas
prompt = f"""Por favor, extrae algunas etiquetas relevantes (indicando el índice de inicio y fin de cada etiqueta) del siguiente texto:

{document_text}

Devuelve cada etiqueta en el formato 'inicio,fin' en líneas separadas."""

# Ejecutar el modelo de lenguaje para obtener las etiquetas (ahora esperamos índices)
indices_tags = llm.invoke(prompt)

# Imprimir las etiquetas extraídas mostrando las palabras correspondientes
print("\nEtiquetas extraídas (palabras):")
for line in indices_tags.strip().split('\n'):
    try:
        start_index, end_index = map(int, line.split(','))
        # Asegurarse de que los índices sean válidos
        if 0 <= start_index < len(document_text) and start_index <= end_index <= len(document_text):
            tag = document_text[start_index:end_index]
            print(f"[{start_index}-{end_index}]: {tag}")
        else:
            print(f"Advertencia: Índices fuera de rango: {line}")
    except ValueError:
        print(f"Advertencia: Formato de índice incorrecto: {line}")
    except IndexError:
        print(f"Advertencia: Error al acceder al texto con los índices: {line}")

from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.llms import Ollama

# Pedir al usuario la ruta del archivo
ruta_archivo = input("Por favor, introduce la ruta del archivo a analizar: ")

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
prompt = f"""Por favor, extrae algunas etiquetas relevantes (palabras clave o frases cortas) del siguiente texto:

{document_text}

Devuelve las etiquetas separadas por comas."""

# Ejecutar el modelo de lenguaje para obtener las etiquetas
tags = llm.invoke(prompt)

# Imprimir las etiquetas extraídas
print("\nEtiquetas extraídas:")
print(tags)

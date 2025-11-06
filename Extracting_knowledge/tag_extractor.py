# tag_extractor.py
import os
import re
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.llms import Ollama

def extract_tags(ruta_archivo):
    """Extrae palabras clave/etiquetas relevantes de un archivo de texto."""
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            document_text_xml = f.read()
    except FileNotFoundError:
        print(f"Error: El archivo en la ruta '{ruta_archivo}' no fue encontrado.")
        return []
    except Exception as e:
        print(f"Ocurrió un error al leer el archivo: {e}")
        return []

    extracted_text = re.sub(r'<[^>]+>', '', document_text_xml)
    extracted_text = ' '.join(extracted_text.split())

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_text(extracted_text)

    embeddings = OllamaEmbeddings(model="phi3")
    vector_store = FAISS.from_texts(chunks, embeddings)
    llm = Ollama(model="phi3")

    prompt = f"""Por favor, extrae las palabras clave o frases cortas más relevantes del siguiente texto. Estas etiquetas deben representar los temas principales del documento.

    {extracted_text}

    Devuelve una lista de estas etiquetas separadas por comas."""

    tags_output = llm.invoke(prompt)
    tags_list = [tag.strip() for tag in tags_output.split(',')]
    return tags_list

if __name__ == "__main__":
    # Ejemplo de uso si se ejecuta directamente
    import readline
    def completer(text, state):
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

    readline.set_completer_delims(' \t\n;')
    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")

    ruta_archivo = input("Por favor, introduce la ruta del archivo a analizar (puedes usar Tab para autocompletar): ")
    extracted_tags = extract_tags(ruta_archivo)
    if extracted_tags:
        print("\nEtiquetas extraídas:")
        for tag in extracted_tags:
            print(f"- {tag}")

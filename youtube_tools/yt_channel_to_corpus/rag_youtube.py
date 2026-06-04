#!/usr/bin/env python3
"""
rag_youtube.py — RAG para corpus de transcripciones de YouTube.
Uso: python rag_youtube.py <modelo_ollama> <ruta_corpus.md>
"""
import sys
import os
import shutil

from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

EMBED_MODEL  = "nomic-embed-text"
DB_DIR       = "./chroma_yt_db"
CHUNK_SIZE   = 800
CHUNK_OVERLAP = 150
TOP_K        = 6


# ─── CARGA ───────────────────────────────────────────────────────────────────

def cargar_corpus(ruta: str) -> list[Document]:
    with open(ruta, "r", encoding="utf-8") as f:
        texto = f.read()

    secciones = texto.split("\n## ")
    documentos = []

    for i, bloque in enumerate(secciones):
        if i == 0:          # cabecera del corpus, no es una transcripción
            continue
        bloque  = "## " + bloque
        lineas  = bloque.split("\n")
        titulo  = lineas[0].replace("## ", "").strip()

        # Extraer URL si el corpus la incluye
        url = ""
        for linea in lineas[1:6]:
            if "**URL:**" in linea:
                url = linea.replace("**URL:**", "").strip()
                break

        # Contenido = todo menos el encabezado y metadatos (líneas con **)
        contenido_lineas = [
            l for l in lineas[1:]
            if not l.strip().startswith("**") and l.strip() != "---"
        ]
        contenido = "\n".join(contenido_lineas).strip()

        if len(contenido) < 50:   # secciones vacías o solo metadatos
            continue

        documentos.append(Document(
            page_content=contenido,
            metadata={"titulo": titulo, "url": url}
        ))

    return documentos


# ─── VECTOR STORE ─────────────────────────────────────────────────────────────

BATCH_SIZE = 2000   # ChromaDB max ~5461; usamos 2000 por margen

def construir_vectorstore(documentos: list[Document]) -> Chroma:
    if os.path.exists(DB_DIR):
        shutil.rmtree(DB_DIR)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(documentos)
    total  = len(chunks)
    print(f"   {len(documentos)} transcripciones → {total} fragmentos")

    embedding = OllamaEmbeddings(model=EMBED_MODEL)
    print(f"   Generando embeddings con {EMBED_MODEL} (lotes de {BATCH_SIZE})...")

    # Primer lote — crea la colección
    vs = Chroma.from_documents(
        chunks[:BATCH_SIZE],
        embedding=embedding,
        persist_directory=DB_DIR,
    )
    print(f"   Lote 1/{-(-total // BATCH_SIZE)} indexado")

    # Lotes siguientes
    for i, inicio in enumerate(range(BATCH_SIZE, total, BATCH_SIZE), start=2):
        vs.add_documents(chunks[inicio:inicio + BATCH_SIZE])
        print(f"   Lote {i}/{-(-total // BATCH_SIZE)} indexado")

    return vs


# ─── RESPUESTA ────────────────────────────────────────────────────────────────

PROMPT_TEMPLATE = """\
Eres un asistente que responde preguntas basándote exclusivamente en \
transcripciones de vídeos de YouTube proporcionadas a continuación.

Responde de forma clara y directa. Si la información no aparece en las \
transcripciones, dilo explícitamente en lugar de inventar una respuesta.

PREGUNTA:
{pregunta}

FRAGMENTOS DE TRANSCRIPCIONES:
{contexto}

RESPUESTA:"""


def responder(pregunta: str, vs: Chroma, llm: OllamaLLM) -> str:
    docs     = vs.as_retriever(search_kwargs={"k": TOP_K}).invoke(pregunta)
    contexto = "\n\n---\n\n".join(
        f"[{doc.metadata.get('titulo', '')}]\n{doc.page_content}"
        for doc in docs
    )
    prompt   = PROMPT_TEMPLATE.format(pregunta=pregunta, contexto=contexto)
    return llm.invoke(prompt)


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    modelo = sys.argv[1] if len(sys.argv) > 1 else None
    corpus = sys.argv[2] if len(sys.argv) > 2 else None

    if not modelo or not corpus:
        print("Uso: python rag_youtube.py <modelo_ollama> <ruta_corpus.md>")
        sys.exit(1)

    if not os.path.exists(corpus):
        print(f"❌ Corpus no encontrado: {corpus}")
        sys.exit(1)

    corpus_nombre = os.path.basename(os.path.dirname(corpus)) or os.path.basename(corpus)

    print(f"\n{'='*60}")
    print(f"🎬  RAG — {corpus_nombre.upper()}")
    print(f"{'='*60}")
    print(f"   Corpus   : {corpus}")
    print(f"   Modelo   : {modelo}")
    print(f"   Embeddings: {EMBED_MODEL}")

    print("\n📂 Cargando corpus...")
    docs = cargar_corpus(corpus)
    if not docs:
        print("❌ No se encontraron transcripciones en el corpus.")
        sys.exit(1)
    print(f"   ✅ {len(docs)} transcripciones cargadas")

    print("\n🧠 Construyendo base vectorial...")
    vs  = construir_vectorstore(docs)
    llm = OllamaLLM(model=modelo)
    print("   ✅ Lista")

    print(f"\n{'='*60}")
    print("💬  Pregunta lo que quieras sobre el contenido del canal.")
    print("    'salir' para terminar.")
    print(f"{'='*60}\n")

    while True:
        try:
            pregunta = input("🤔  ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nHasta luego.")
            break

        if not pregunta:
            continue
        if pregunta.lower() in ("salir", "exit", "quit"):
            print("Hasta luego.")
            break

        print("⏳  Buscando...")
        try:
            respuesta = responder(pregunta, vs, llm)
            print(f"\n🤖  {respuesta}\n")
        except Exception as e:
            print(f"❌  Error: {e}\n")


if __name__ == "__main__":
    main()

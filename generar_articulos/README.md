# 🧠 Generador de Artículos Técnicos con IA (Ollama + LLMs)

Este script automatiza la conversión de archivos Markdown técnicos en artículos redactados con un lenguaje más accesible, claro y divulgativo utilizando modelos de lenguaje locales a través de [Ollama](https://ollama.com/).

---

## ✨ ¿Por qué usar este script?

En el mundo de la ciencia de datos, ingeniería de datos y machine learning, es común generar grandes cantidades de notas, experimentos y documentación técnica en archivos `.md`. Sin embargo, estas notas no siempre están preparadas para ser leídas por una audiencia más amplia (por ejemplo, lectores de blogs, colegas no técnicos, o estudiantes).

Este script resuelve eso:

✅ Convierte notas técnicas en artículos comprensibles  
✅ Utiliza tu propia GPU o servidor con [Ollama](https://ollama.com/)  
✅ No depende de servicios en la nube o APIs externas  
✅ Compatible con múltiples modelos como `llama3`, `deepseek`, `mistral`, etc.

---

## 🚀 ¿Cómo funciona?

1. **Entrada**: Directorio que contiene archivos `.md` con contenido técnico.
2. **Procesamiento**: Se recorre recursivamente cada archivo, se genera un prompt instructivo, y se envía al endpoint `/api/chat` de Ollama.
3. **Salida**: Se genera un nuevo archivo `_articulo.md` con el contenido transformado en estilo divulgativo y se guarda en un directorio con sufijo `_procesado`.

---

## 🛠️ Requisitos

- Tener instalado y funcionando [Ollama](https://ollama.com/)
- Tener modelos descargados (por ejemplo: `deepseek-r1:14b`)
- Python 3.7+
- `curl` instalado (utilizado internamente para llamar a Ollama)

---

## 📦 Instalación

```bash
git clone https://github.com/tu_usuario/generador-articulos-ollama.git
cd generador-articulos-ollama




# 🧠 Technical Article Generator with AI (Ollama + LLMs)

This script automates the conversion of technical Markdown notes into clear, educational, and accessible articles using local large language models (LLMs) via [Ollama](https://ollama.com/).

---

## ✨ Why use this script?

In the fields of data science, data engineering, and machine learning, it’s common to produce large amounts of technical notes in `.md` files. However, these notes aren’t always suitable for broader audiences (e.g., blog readers, non-technical colleagues, or students).

This script solves that:

✅ Converts technical notes into readable, engaging articles  
✅ Uses your own GPU/server via [Ollama](https://ollama.com/)  
✅ No need for cloud APIs or external services  
✅ Works with multiple models like `llama3`, `deepseek`, `mistral`, etc.

---

## 🚀 How it works

1. **Input**: A directory containing `.md` files with technical content.
2. **Processing**: It walks through each file recursively, creates an instructive prompt, and sends it to Ollama’s `/api/chat` endpoint.
3. **Output**: A new `_articulo.md` file is generated with accessible, well-structured article content and saved in a `_processed` directory.

---

## 🛠️ Requirements

- A working installation of [Ollama](https://ollama.com/)
- Downloaded LLMs (e.g., `deepseek-r1:14b`)
- Python 3.7+
- `curl` installed (used internally to call the Ollama API)

---

## 📦 Installation

```bash
git clone git@github.com:albertjimrod/bash_tools.git
cd article-generator-ollama


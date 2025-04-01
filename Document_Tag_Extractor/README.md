# Document Tag Extractor with Ollama and Langchain

This project is a Python script that allows extracting relevant tags (keywords or short phrases) from a text or XML document using the `phi3` language model via Ollama and the Langchain library. Additionally, it uses FAISS for creating a vector store (optional) and offers file path autocompletion in the terminal.

## Features

* **Tag Extraction:** Identifies and extracts keywords or short phrases that represent the main topics of a document.
* **Support for Text and XML:** Allows analyzing text files (`*.txt`) and XML files (`*.xml`). For XML files, it performs a basic extraction by removing tags.
* **Integration with Ollama:** Utilizes the `phi3` language model running locally via Ollama for tag extraction.
* **Use of Langchain:** Leverages the Langchain library for interaction with the language model and vector store creation.
* **Optional Vector Store with FAISS:** Creates a vector index of the document content using FAISS and Ollama embeddings, which can be useful for future semantic search or document comparison tasks.
* **File Path Autocompletion:** When requesting the file path to analyze, the script offers autocompletion with the Tab key (primarily in Unix-like systems).

## Prerequisites

Before running the script, ensure you have the following installed and configured:

1.  **Python 3.7 or higher:** You can download it from [https://www.python.org/downloads/](https://www.python.org/downloads/)
2.  **pip:** The Python package manager, which usually comes with Python.
3.  **Ollama:** You need to have Ollama installed and running on your system. You can find the installation instructions at [https://ollama.ai/download](https://ollama.ai/download).
4.  **`phi3` Model for Ollama:** Make sure you have downloaded the `phi3` model in Ollama. You can do this by executing the following command in your terminal:
    ```bash
    ollama pull phi3
    ```

## Installation

1.  **Clone this repository (optional):** If you plan to share or modify the code, you can clone this GitHub repository to your local machine.
2.  **Create a virtual environment (recommended):** It's a good practice to create a virtual environment to isolate the project dependencies.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate  # On Windows
    ```
3.  **Install the dependencies:** Use `pip` to install the necessary libraries from the `requirements.txt` file (if you create one, see the Dependencies section). If you don't have a `requirements.txt`, you can install the dependencies individually:
    ```bash
    pip install langchain-community langchain
    ```
    On Windows, if Tab autocompletion isn't working, you might need to install `pyreadline3`:
    ```bash
    pip install pyreadline3
    ```

## Usage

1.  **Save the script:** Save the Python code in a file, for example, `extractor_etiquetas.py`.
2.  **Run the script from the terminal:** Navigate to the directory where you saved the file and run the script with the following command:
    ```bash
    python extractor_etiquetas.py
    ```
3.  **Enter the file path:** The script will ask you to input the path of the file you want to analyze. You can enter the full or relative path. In Unix-like systems, you can use the Tab key for autocompletion as you type.
4.  **View the tags:** Once the script processes the file, it will display the extracted tags in the terminal, prefixed with a dash (`-`).

## Dependencies

The following Python libraries are required to run this script:

* `langchain-community`: For integrating with Ollama and FAISS.
* `langchain`: The base framework of Langchain.
* `readline`: (Primarily for Unix-like systems) For terminal autocompletion functionality.
* `os`: For file system-related operations.
* `re`: For the use of regular expressions (for basic text extraction from XML).

You can create a file named `requirements.txt` in the same directory as your script and add the following lines:

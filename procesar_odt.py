import os
import zipfile
import tempfile
import subprocess

def extract_tags_and_create_obsidian_note(odt_filepath, output_dir):
    """
    Extrae los tags de un archivo .odt usando Fabric y crea un archivo Markdown para Obsidian.

    Args:
        odt_filepath (str): La ruta completa al archivo .odt.
        output_dir (str): La ruta al directorio donde se guardará el archivo Markdown.
    """
    try:
        # Crear un directorio temporal para extraer el contenido del .odt
        with tempfile.TemporaryDirectory() as tmpdir:
            # Abrir el archivo .odt (que es un archivo zip) y extraer el contenido XML
            with zipfile.ZipFile(odt_filepath, 'r') as zip_ref:
                zip_ref.extract('content.xml', tmpdir)
            xml_filepath = os.path.join(tmpdir, 'content.xml')

            # Construir el comando de Fabric
            fabric_command = f"echo '{os.path.basename(xml_filepath)}' | fabric --model deepseek-r1:14b -sp extract_wisdom"

            # Ejecutar el comando de Fabric
            process = subprocess.run(fabric_command, shell=True, capture_output=True, text=True)

            # Obtener los tags extraídos
            extracted_tags = process.stdout.strip()

            # Construir la ruta del archivo de salida para Obsidian
            base_name = os.path.splitext(os.path.basename(odt_filepath))[0]
            output_filename = f"{base_name}.md"
            output_filepath = os.path.join(output_dir, output_filename)

            # Crear el archivo Markdown y escribir los tags
            with open(output_filepath, 'w', encoding='utf-8') as outfile:
                if extracted_tags:
                    outfile.write(extracted_tags)
                else:
                    outfile.write("") # Si no hay tags, se crea un archivo vacío

            print(f"Tags extraídos de '{os.path.basename(odt_filepath)}' y guardados en '{output_filename}'")

    except FileNotFoundError:
        print(f"Error: No se encontró el archivo 'content.xml' dentro de '{odt_filepath}'.")
    except Exception as e:
        print(f"Ocurrió un error al procesar '{odt_filepath}': {e}")

def main():
    """
    Función principal para procesar todos los archivos .odt en la carpeta 'input_docs'.
    """
    input_directory = "input_docs"
    output_directory = "obsidian_vault"

    # Crear el directorio de salida si no existe
    os.makedirs(output_directory, exist_ok=True)

    # Buscar todos los archivos .odt en la carpeta de entrada
    odt_files = [f for f in os.listdir(input_directory) if f.endswith(".odt")]

    if not odt_files:
        print(f"No se encontraron archivos .odt en la carpeta '{input_directory}'.")
        return

    print(f"Se encontraron {len(odt_files)} archivos .odt para procesar.")

    # Procesar cada archivo .odt encontrado
    for odt_file in odt_files:
        odt_filepath = os.path.join(input_directory, odt_file)
        extract_tags_and_create_obsidian_note(odt_filepath, output_directory)

    print("Proceso completado.")

if __name__ == "__main__":
    main()

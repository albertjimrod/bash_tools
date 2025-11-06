<think>
Alright, I need to convert a technical note about installing NVIDIA CUDA Toolkit on Ubuntu-based systems into an engaging and educational article. First, I'll start by understanding the original content provided in the link. It includes terminal outputs showing environment variables like PATH and LD_LIBRARY_PATH after CUDA installation.

I should structure the article in a way that's easy for readers to follow. Maybe begin with an introduction explaining why someone would want to install CUDA on their Ubuntu system. Then, outline the prerequisites, such as having an NVIDIA GPU and the proprietary drivers installed.

Next, I'll need to detail each step clearly. Starting with downloading the CUDA toolkit from NVIDIA's website, choosing the correct version based on the system architecture (64-bit), and then installing it using a graphical installer or the command line. After installation, setting up environment variables is crucial for CUDA to work properly, so I should explain how to modify PATH and LD_LIBRARY_PATH.

I should also include verification steps to ensure everything works as expected. Running commands like nvcc --version or nvidia-smi can help confirm that CUDA is installed correctly and the GPU is recognized.

Additionally, it might be helpful to mention some common issues and solutions, such as driver installation problems or environment variable mistakes. Including a section about where to find additional resources for troubleshooting could also be beneficial.

Throughout the article, I'll keep the language clear and conversational, avoiding overly technical jargon unless necessary. Using headings and bullet points can make it more readable. Also, adding tips like backing up configuration files before making changes can help readers avoid potential issues.

Finally, I'll conclude by encouraging readers to explore CUDA programming with hands-on projects or examples, providing a sense of accomplishment and next steps.
</think>

# Instalación de NVIDIA CUDA Toolkit en Ubuntu y distribuciones similares: Guía paso a paso

¿Necesita instalar el **NVIDIA CUDA Toolkit** en su sistema Ubuntu o una distribución similar? ¡Está en el lugar correcto! En este tutorial, le guiaré a través del proceso de instalación de NVIDIA CUDA Toolkit, que incluye verificar y asegurarse de que su tarjeta gráfica es compatible con CUDA, descargar e instalar el toolkit, y configurar correctamente las variables de entorno.

---

## **¿Qué es NVIDIA CUDA?**

NVIDIA CUDA es un framework paralelo para programación basado en la arquitectura de GPU (gráficos por procesamiento masivo) de NVIDIA. Permite a los desarrolladores acelerar sus aplicaciones y rutas de aprendizaje máquina aprovechando el poder de cálculo de las tarjetas gráficas NVIDIA.

Si está interesado en **machine learning**, **deep learning** o cualquier otro campo que requiera cálculos intensivos, CUDA es una herramienta indispensable para usted.

---

## **Requisitos previos**

Antes de comenzar con la instalación, asegúrese de:

1. **Tener una tarjeta gráfica NVIDIA compatible con CUDA**:
   - Consulte la lista de GPUs compatibles en el [sitio web de NVIDIA](https://developer.nvidia.com/cuda-gpus).
2. **Haber instalado los drivers de NVIDIA propietarios**:
   - Si no tiene los drivers instalados, consulte [este tutorial](https://www.if-not-true-then-false.com/2021/install-nvidia-drivers-on-ubuntu-debian-linux-mint/) para instrucciones detalladas.

---

## **Paso 1: Descargar el CUDA Toolkit**

1. Vaya al sitio web oficial de NVIDIA [CUDA Toolkit Archive](https://developer.nvidia.com/cuda-toolkit-archive).
2. Elija la versión del toolkit que desea descargar. Asegúrese de seleccionar una versión compatible con su sistema operativo (64-bit o 32-bit).
3. Descargue el archivo `.deb` correspondiente.

---

## **Paso 2: Instalar el CUDA Toolkit**

Después de descargar el paquete `.deb`, instálelo utilizando la terminal:

```bash
sudo dpkg -i nombre_del_paquete.deb
```

Por ejemplo, si descargó `cuda-repo-ubuntu20.04_11.5.0-1_amd64.deb`:

```bash
sudo dpkg -i cuda-repo-ubuntu20.04_11.5.0-1_amd64.deb
```

Después de instalar el paquete, ejecute:

```bash
sudo apt-get update && sudo apt-get install nvidia-cuda-toolkit
```

Esto instalará el toolkit y cualquier dependencia necesaria.

---

## **Paso 3: Configurar las variables de entorno**

Para que CUDA funcione correctamente, necesitará configurar las variables de entorno `PATH` y `LD_LIBRARY_PATH`. Añada las siguientes líneas al final del archivo `.bashrc` en su directorio home:

```bash
echo 'export PATH=/usr/local/cuda-11.5/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-11.5/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
```

Después de editar el archivo `.bashrc`, cargue las nuevas configuraciones ejecutando:

```bash
source ~/.bashrc
```

Ahora, verá que sus variables de entorno incluyen los binarios y bibliotecas de CUDA.

---

## **Paso 4: Verificar la instalación**

Para asegurarse de que la instalación se realizó correctamente, ejecute el siguiente comando:

```bash
nvcc --version
```

Esto debería mostrar la versión de nvcc (el compilador CUDA) instalada.

También puede verificar que su tarjeta gráfica está funcionando correctamente con CUDA ejecutando:

```bash
nvidia-smi
```

Si ve una salida similar a la siguiente, significa que CUDA detectó correctamente su GPU:

```
+----------------------------------------------------------------+
| NVIDIA-SMI 450.80.01             Driver Version: 450.80.01    |
|-----------------------------------+--------------------------+
| GPU  Name        TCCS Memory     | 0   Tesla V100            |
| ...                              +--------------------------+
```

---

## **¿Dónde puedo encontrar más información?**

- [Sitio web oficial de NVIDIA CUDA](https://developer.nvidia.com/cuda)
- [Documentación del CUDA Toolkit](https://docs.nvidia.com/cuda/index.html)
- [Foro de soporte de NVIDIA](https://forums.developer.nvidia.com/)

---

Espero que esta guía le haya sido útil. Si tiene alguna pregunta o necesita ayuda adicional, no dude en dejarme un comentario. ¡Buenos días! 😊
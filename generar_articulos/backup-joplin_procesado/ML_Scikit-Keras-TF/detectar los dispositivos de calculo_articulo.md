<think>
Okay, so I'm trying to figure out how to check if my computer has access to GPUs when using TensorFlow. I remember that sometimes programs can run on the CPU or GPU, and GPUs are usually faster for machine learning tasks. But I'm not exactly sure how to see if TensorFlow is recognizing my GPU.

I saw some code snippets online that people use to check available devices in TensorFlow. They import device_lib from tensorflow.python.client and then call list_local_devices(). Maybe I can try that. Let me write it down:

from tensorflow.python.client import device_lib
print(device_lib.list_local_devices())

When I run this, what should happen? It should print out the local devices, like CPUs and GPUs available.

I also saw another snippet where someone prints the number of GPUs by using len(tf.config.list_physical_devices('GPU')). Maybe that's another way to check. So I'll need to make sure TensorFlow is imported properly, maybe using 'import tensorflow as tf' first.

Wait, in the code examples provided, some parts are repeated. Like, importing device_lib multiple times and calling list_local_devices() more than once. I think it's better to streamline this so each step is clear without repetition.

So here's what I'm thinking: I'll write a script that first checks all available devices, then counts the GPUs, and finally gets their names. This way, I can see if TensorFlow detects my GPU(s).

I should also make sure that I have the latest version of TensorFlow installed because older versions might behave differently or not support certain functions anymore.

Another thing to consider is whether CUDA is properly installed on my system because TensorFlow can use CUDA for GPU acceleration. If CUDA isn't set up correctly, TensorFlow might not detect the GPUs even if they exist.

I'll run each part step by step and see what outputs I get. If it says "GPU" in the device names, that means it's detected them. If not, maybe there's an issue with my setup.

So putting it all together, I can create a Python script that does the following:
1. Imports TensorFlow and the necessary modules.
2. Prints all local devices.
3. Counts and prints the number of GPUs.
4. Lists the names of available GPUs.

This should give me a clear idea of whether TensorFlow recognizes my GPU for machine learning tasks.
</think>

Para verificar si TensorFlow detecta tu tarjeta gráfica (GPU) y cuales están disponibles para su uso, puedes ejecutar el siguiente código. Este script te mostrará los dispositivos locales disponibles, el número de GPUs detectadas y sus nombres.

```python
# Primero, importa la biblioteca necesaria
from tensorflow.python.client import device_lib

# Función para obtener todos los dispositivos locales
def get_available_devices():
    local_device_protos = device_lib.list_local_devices()
    return local_device_protos

# Función para obtener el nombre de los dispositivos
def get_device_names():
    return [x.name for x in device_lib.list_local_devices()]

# Obtén y muestra todos los dispositivos disponibles
devices = get_available_devices()
print("Dispositivos disponibles:")
for device in devices:
    print(f"{device.device_type} - {device.name}")

# Cuenta el número de GPUs detectadas
import tensorflow as tf
gpus = tf.config.list_physical_devices('GPU')
print("\nNúmero de GPUs disponibles:", len(gpus))

# Muestra los nombres de las GPUs disponibles
print("\nNombres de las GPUs:")
print(get_device_names())
```

**Explicación paso a paso:**

1. **Importar bibliotecas:** Se importa `device_lib` de TensorFlow para interactuar con los dispositivos.

2. **Función `get_available_devices()`:** Lista todos los dispositivos locales disponibles, sean CPUs o GPUs.

3. **Función `get_device_names()`:** Extrae y devuelve los nombres de los dispositivos detectados.

4. **Mostrar dispositivos:** Se imprime una lista detallada de los dispositivos disponibles con su tipo y nombre.

5. **Contar GPUs:** Se utiliza `tf.config.list_physical_devices('GPU')` para obtener las GPU físicas detectadas y se imprime el conteo.

6. **Mostrar nombres de GPUs:** Se llama a la función que extrae los nombres de los dispositivos y se imprimen.

**Resultado esperado:**

- Verás una lista de dispositivos, incluyendo CPUs y GPUs.
- Si tienes una o más GPUs instaladas y configuradas correctamente, aparecerán en la salida con su nombre (p.ej., `/device:GPU:0`).
- El número de GPUs detectadas coincide con las que has instalado.

**Consideraciones:**

- Asegúrate de tener TensorFlow instalado correctamente.
- Verifica que CUDA esté instalado y configurado si planeas usar GPU acceleration en TensorFlow.
- Si no ves GPUs en la salida, revisa tu instalación de CUDA o Drivers de NVIDIA.
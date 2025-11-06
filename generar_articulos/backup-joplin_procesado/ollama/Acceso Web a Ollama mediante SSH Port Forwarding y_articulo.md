<think>
Okay, so I need to convert this technical content into a clear, educational, and enjoyable article. Let me read through the provided content first to understand what it's about.

The original text is in Spanish, and it seems to be instructions on setting up Open WebUI and using Ollama API via SSH tunnels. There are two main parts: a solution using port 8080 and a future template with steps, objectives, and additional commands.

My goal is to make this information more accessible. I'll need to break down the technical jargon, explain each step clearly, and present it in an engaging way. Maybe start with an introduction that explains why someone would want to do this setup—perhaps they're a data scientist or developer looking to access remote AI models.

I should also think about the audience. They might be familiar with basic command-line operations but could need guidance on setting up SSH tunnels and Docker containers. Including some background on what Open WebUI and Ollama are would help, maybe in a "What is..." section.

The step-by-step guide needs to be easy to follow. I'll number the steps, use clear headings, and perhaps include explanations for each command. For example, when explaining SSH tunnels, it's important to note that they forward ports from the local machine to the remote server, allowing access through localhost.

I should also consider visual elements. Maybe a diagram showing the flow of data or where to enter each command. But since I can't add images here, I'll focus on clear headings and descriptions instead.

In the future template section, it's presented as a checklist, which is good for quick reference. I'll keep that structure but make sure it's easy to understand at a glance.

I should also include some tips or troubleshooting advice. For example, what if the SSH connection fails? Or how to verify that the containers are running correctly using `docker ps`.

Finally, wrapping up with a conclusion that summarizes the benefits and encourages the reader to experiment further would be nice. Maybe suggest exploring different models or optimizing their setup.

I think I've covered all the key points. Now, I'll structure the article accordingly, making sure each section flows logically from one to the next, and that the language is friendly and approachable.
</think>

# Acceso Remoto a Ollama y Open WebUI: Guía Completa

¡Hola! Si estás aquí, probablemente te interesa acceder a los potentes modelos de lenguaje desde tu equipo local utilizando herramientas como Ollama y Open WebUI. En este artículo, te guiaré paso a paso para que puedas conectar con un servidor remoto, configurar los túneles necesarios y acceder a las interfaces deseadas.

## ¿Qué es lo que haremos?

En este tutorial, aprenderemos a:

1. Configurar una conexión segura desde tu equipo de trabajo hasta un servidor remoto.
2. Instalar y ejecutar Open WebUI en el servidor.
3. Crear túneles SSH para acceder a las interfaces de Ollama y Open WebUI.
4. Verificar que todo funciona correctamente.

## Requisitos previos

- Acceso SSH al servidor remoto con usuario y contraseña/certificado.
- Docker instalado en el servidor remoto.
- Ollama ya instalado y configurado en el servidor (ya sea a través de Docker o directamente).

## Paso 1: Configuración inicial

### Conexión SSH al servidor remoto

Primero, necesitamos acceso al servidor remoto. Ejecuta el siguiente comando en tu terminal:

```bash
ssh ion@192.168.91.236
```

Si la conexión falla, revisa si el usuario y la IP son correctos y que el puerto 22 (puerto predeterminado para SSH) esté abierto.

## Paso 2: Creación de túneles SSH

Los túneles SSH nos permiten redirigir tráfico desde tu equipo local al servidor remoto, esenciales para acceder a las interfaces web y APIs que están detrás del firewall.

### Túnel para Ollama API (puerto 11434)

```bash
ssh -L 11434:localhost:11434 ion@192.168.91.236
```

Este comando crea un túnel que redirige el puerto 11434 de tu ordenador local al puerto 11434 del servidor remoto.

### Túnel para Open WebUI (puerto 8080)

```bash
ssh -L 8080:localhost:8080 ion@192.168.91.236
```

Similarmente, este comando redirige el puerto 8080 de tu ordenador al puerto 8080 del servidor remoto.

Nota: Asegúrate de ejecutar estos comandos en terminales diferentes para mantener ambas conexiones activas.

## Paso 3: Instalación de Open WebUI en el servidor remoto

Open WebUI es una interfaz web que nos permite interactuar con los modelos de lenguaje de manera más cómoda. Para instalarlo, ejecuta en el servidor remoto:

```bash
docker run -d -p 8080:8080 --add-host=host.docker.internal:host-gateway --name open-webui ghcr.io/open-webui/open-webui:main
```

Este comando inicia un contenedor Docker con la imagen de Open WebUI, mapeando el puerto 8080 y configurando correctamente las redes.

## Paso 4: Verificación y acceso

### Verificar el estado de los contenedores

En el servidor remoto, ejecuta:

```bash
docker ps -a
```

Buscarás una línea que incluya `open-webui` para asegurarte de que el contenedor esté corriendo.

### Acceso a las interfaces

- **Open WebUI**: Abre tu navegador y ve a [http://localhost:8080](http://localhost:8080). Deberías ver la interfaz de Open WebUI lista para usar.
  
- **Ollama**: Puedes acceder a su interfaz web en [http://localhost:11434](http://localhost:11434) o usar la CLI directamente.

## Paso 5: Configuración futura

Ahora que tienes todo configurado, puedes explorar diferentes modelos y ajustes. Aquí están algunos consejos:

- **Optimización**: Considera la memoria y el procesamiento disponibles en el servidor remoto para elegir los modelos más adecuados.
- **Seguridad**: Si vas a mantener estas conexiones activas, especialmente en entornos públicos, considera usar VPN o servicios de proxy seguros.
- **Automatización**: Puedes scripted las conexiones SSH y túneles para una experiencia más fluida.

## Conclusión

¡Felicidades! Has configurado con éxito tu acceso remoto a Ollama y Open WebUI. Ahora tienes el poder de acceder a los últimos avances en procesamiento de lenguaje natural desde tu escritorio. No dudes en experimentar y llevártelo más allá.
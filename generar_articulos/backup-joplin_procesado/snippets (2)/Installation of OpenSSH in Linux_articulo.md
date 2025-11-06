<think>
Okay, I need to convert this technical note about installing OpenSSH on Linux into an engaging article. Let me start by understanding what the original content is covering.

First, there's a command to install both openssh-server and openssh-client using apt-get. That’s straightforward. Then, it talks about backing up the configuration file before making changes. I should explain why backup is important because readers might not be familiar with best practices.

Next, the article needs to guide the user through verifying if OpenSSH is running by using netcat. I should make sure to explain what netcat is for those who aren't familiar and how it helps in testing connections.

There's a part about changing the default port from 22 to 13. I need to clarify why someone might want to change the port, maybe for security reasons or avoiding conflicts. Also, explaining where to make the change in the config file is essential.

After modifying the port, the user needs to restart the SSH service. I should include that command and perhaps mention how services can be managed with init.d versus systemctl if the distribution varies.

Another section mentions adding a login banner by editing /etc/issue.net. I need to explain what a banner does and why it's useful for system administrators. Maybe also suggest creating an example banner to make it concrete.

I should structure the article in clear sections, maybe numbered steps or headings that make each part easy to follow. Using friendly language will help keep it engaging rather than too technical. Also, adding tips on security and best practices could add value beyond just installation instructions.

I’ll need to make sure each step is clearly explained, with commands highlighted so they stand out. Maybe include some notes on permissions or what to do if something goes wrong, like the backup mentioned earlier.

Overall, I want readers to feel confident in setting up OpenSSH after following this guide, so clarity and thoroughness are key. I'll avoid jargon where possible and explain any necessary technical terms.
</think>

# Cómo Configurar y Usar el Servidor de SSH en Linux: Guía Detallada

La capacidad de acceder remotamente a un sistema operativo es una herramienta invaluable para los administradores de sistemas y desarrolladores. En este tutorial, aprenderás cómo instalar, configurar y probar el servidor de OpenSSH en tu sistema Linux.

---

## Instalación de OpenSSH Server y Cliente

Primero, necesitamos instalar tanto el servidor como el cliente de OpenSSH. Esto se hace fácilmente mediante la terminal con el siguiente comando:

```bash
$ sudo apt-get install openssh-server openssh-client
```

Este comando instala el paquete del servidor de SSH (para permitir conexiones remotas) y el paquete del cliente de SSH (para conectarte a otros servidores).

---

## Configuración Básica de OpenSSH

El comportamiento del servidor de SSH se configura mediante el archivo `/etc/ssh/sshd_config`. Antes de modificar este archivo, es una buena práctica crear una copia de seguridad:

```bash
$ sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.original_copy
```

Esto te permitirá恢复 la configuración original si algo sale mal.

---

## Verificar Si el Servidor está Funcionando

Después de instalar OpenSSH, es importante verificar que esté funcionando correctamente. Puedes hacerlo conectándote al servidor desde tu misma máquina (localhost) o usando herramientas como `netcat`, una herramienta popular para probar conexiones TCP/IP.

Ejecuta el siguiente comando en la terminal:

```bash
# nc -v -z 127.0.0.1 22
```

Si ves algo similar a esto, significa que el servidor de SSH está escuchando en el puerto 22:

```
Connecting to 127.0.0.1:22
nc: connect to 127.0.0.1 port 22 (tcp) failed: Connection refused
```

Si obtienes un mensaje de "Connection refused", no te preocupes; simplemente significa que el servidor no está escuchando en ese puerto correctamente.

---

## Cambiar el Puerto por Defecto de SSH

El puerto por defecto para SSH es 22. Si deseas cambiarlo a otro puerto (como 13), modifica el archivo de configuración:

```bash
$ sudo nano /etc/ssh/sshd_config
```

Busca la línea que dice `Port 22` y cámbiala por:

```bash
Port 13
```

Guarda los cambios y reinicia el servidor SSH para aplicarlos:

```bash
$ sudo /etc/init.d/ssh restart
```

Verifica que el puerto nuevo esté abierto:

```bash
# nc -v -z 127.0.0.1 13
```

---

## Configurar un-banner de Login

Si deseas mostrar un mensaje de bienvenida cuando alguien se conecte al servidor, puedes crear un archivo `/etc/issue.net` con tu mensaje y modificar el archivo de configuración de SSH para incluirlo:

```bash
$ sudo nano /etc/ssh/sshd_config
```

Busca la línea que dice `#Banner /etc/ssh_banner` y descomenta o agrega:

```bash
Banner /etc/issue.net
```

Luego crea el archivo `/etc/issue.net` con tu mensaje:

```bash
$ sudo nano /etc/issue.net
```

Escribe tu banner, por ejemplo:

```
¡Bienvenido al servidor SSH!
Fecha: `date`
Usuario actual: `whoami`
```

Guarda los cambios y reinicia el servidor SSH para ver el banner en acción.

---

## Conclusión

Con estos pasos, has instalado, configurado y personalizado tu servidor de SSH. Ahora puedes acceder remotamente a tu sistema Linux usando cualquier cliente de SSH, como `ssh` en la terminal o herramientas como PuTTY en Windows.

No olvides siempre cerrar las conexiones cuando no las necesites y mantener actualizada tu contraseña para garantizar la seguridad de tu sistema.
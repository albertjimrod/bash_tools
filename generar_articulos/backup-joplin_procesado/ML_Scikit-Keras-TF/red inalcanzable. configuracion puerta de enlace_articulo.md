<think>
Alright, I need to help the user convert a technical note into an engaging article. The content is about fixing network connectivity issues on Linux by setting up the default gateway and configuring DNS settings. 

First, I'll start by understanding the original instructions provided in the query. They outline steps like opening terminal, using sudo su, adding a route with 'route add', checking ping, editing resolv.conf, adding DNS servers, and restarting networking.

I notice that the user wants clarity and education, so I should break down each step simply. Maybe start with an introduction explaining the common issue of no internet after connecting to Wi-Fi. Then guide them through each step methodically, using simple language and maybe some examples.

I'll structure the article into sections for better readability: Checking Network Settings, Setting Up the Default Gateway, Configuring DNS Servers, Restarting the Network Service, Verifying Connectivity, Common Mistakes, and Additional Tips.

Using headings and bullet points can make it more digestible. I should also include explanations for why each step is necessary to educate the reader beyond just following instructions.

I need to ensure that the tone is friendly and encouraging, making readers feel comfortable even if they're new to Linux commands. Including examples like replacing '192.168.136.1' with their actual gateway IP will help them apply it correctly.

Finally, I'll conclude by summarizing the steps and offering additional resources for further troubleshooting. This should make the article not only informative but also supportive for users facing similar issues.
</think>

**Cómo solucionar el problema de conexión a la red: Configuración del.gateway por defecto y DNS**

¿Te has enfrentado alguna vez al frustrante problema donde el ping muestra que estás conectado, pero no puedes navegar por internet? ¡No te preocupes! En este artículo te guiaré paso a paso para solucionar este problema común en sistemas Linux.

### Problema: Conexión de red inalcanzable (ping funciona, pero no hay acceso a internet)

Si estás viendo este mensaje en tu terminal:

```
connect: Network is unreachable
```

o si el ping falla con un código de error como "Network unreachable",很可能 tienes un problema con tu configuración de red. A menudo, esto ocurre porque **no has configurado correctamente la puerta de enlace por defecto (default gateway)** que permite a tu sistema comunicarse con redes externas.

### Solución paso a paso

#### 1. Abrir el terminal
El primer paso es abrir un terminal para ejecutar comandos de línea.

#### 2. Obtener privilegios de administrador
Para realizar cambios en la configuración del sistema, necesitarás privilegios de administrador. Ejecuta:

```bash
sudo su
```

Esto te pedirá tu contraseña de usuario root o administrador.

#### 3. Configurar el gateway por defecto
La mayoría de las veces, tu router (puerta de enlace) tiene una dirección IP como `192.168.x.x` o `172.16.x.x`. Necesitamos añadir esta dirección a tu sistema.

Ejecuta el siguiente comando, reemplazando `(ej: 192.168.136.1)` con la dirección real de tu puerta de enlace:

```bash
route add default gw 192.168.136.1 eth0
```

**¿Qué hace este comando?**
- `route`: Manejador de rutas de Linux.
- `add default`: Añade una ruta por defecto para salir de tu red local.
- `gw [dirección]`: Especifica la dirección de la puerta de enlace.
- `eth0`: Interface Ethernet o Wi-Fi (depende de tu adaptador).

**Verificación:**
Ejecuta:

```bash
ping 8.8.8.8
```

Si el ping funciona, significa que has establecido correctamente la conexión con Google's DNS.

#### 4. Configurar los servidores DNS
A veces, aunque estás conectado a la red, tu navegador no puede resolver nombres de dominio (como google.com) porque no tienes servidor DNS configurado.

**Pasos:**

1. Abre el archivo de configuración de resolución:

   ```bash
   nano /etc/resolv.conf
   ```

2. Añade las siguientes líneas al final del archivo, reemplazando los ejemplos con tus propias direcciones:

   ```
   nameserver 8.8.8.8  # DNS público de Google
   nameserver 192.168.136.0  # Si tu router actúa como servidor DNS
   ```

   **Opción alternativa:**
   Si prefieres usar el servidor local:

   ```
   nameserver 127.0.1.1
   ```

#### 5. Reiniciar el servicio de red
Para aplicar los cambios, reinicia el servicio de red:

```bash
sudo /etc/init.d/networking restart
```

o

```bash
sudo service networking restart
```

**Verificación final:**
Abre tu navegador y visita cualquier sitio web para asegurarte de que la conexión funcione correctamente.

---

### Consejos adicionales

- **Revisa tu dirección MAC:** Si el comando `eth0` no funciona, prueba con `wlan0` si estás usando Wi-Fi.
- **Configuración automática:** Algunas distribuciones de Linux (como Ubuntu) configuran automáticamente la puerta de enlace y DNS si usas NetworkManager.
- **Usa DHCP:** Si tu red usa DHCP, puedes omitir manualmente la configuración de la dirección IP y dejar que el servidor DHCP te asigne una dirección.

Espero que estos pasos te hayan ayudado a solucionar el problema de conexión a internet en tu sistema Linux. Si sigues teniendo problemas, no dudes en consultar con tu administrador de red o revisar los logs de syslog para más detalles.
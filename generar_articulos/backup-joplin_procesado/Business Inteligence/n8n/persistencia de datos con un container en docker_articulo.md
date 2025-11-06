<think>
Bueno, el usuario está teniendo problemas con n8n en Docker. Cada vez que inicia la imagen, tiene que crear una nueva cuenta de usuario. Eso es molesto porque quieres que todo quede configurado ya.

Primero, entiendo que los datos no se están guardando correctamente. Probablemente, el contenedor no está montando un volumen, así que los archivos se pierden al cerrar o actualizar.

Voy a buscar cómo añadir persistencia en Docker. Veo que hay que usar la opción -v para montar una ruta del host en /home/node/.n8n dentro del contenedor. Eso debería hacer que todo guarde correctamente.

También debo asegurarme de los permisos, porque el usuario interno es node con UID 1000. La carpeta en el host debe tener estos permisos para que no haya problemas de acceso.

Voy a modificar el comando del usuario, añadiendo el volumen y explicando cada paso. Además, recomendaré crear la ruta si no existe y cambiar los permisos.

Finalmente, le diré que después de esto, n8n debería conservar toda su configuración y workflows sin problema.
</think>

# Solución para Añadir Persistencia a tu Instancia de n8n en Docker

Para asegurar que tu instancia de n8n en Docker conserve la configuración y los flujos (workflows) incluso después de reiniciar o detener el contenedor, necesitas añadir un volumen al montar una carpeta en tu sistema anfitrión. Esto permitirá que todos los datos importantes se guarden en tu disco duro local en lugar de dentro del contenedor.

---

## Pasos a Seguir

### 1. Crear la Ruta para el Volumen
Primero, crea una ruta en tu sistema anfitrión donde se almacenarán los datos de n8n. Puedes elegir cualquier ubicación que prefieras, pero es recomendable usar algo como `/home/tuusuario/n8n_data` (sustituye `tuusuario` por tu nombre de usuario).

Abre una terminal y ejecuta:
```bash
mkdir -p /home/tuusuario/n8n_data
```

### 2. Añadir la Opción `-v` al Comando de Docker
Modifica tu comando actual para incluir la opción `-v` que montará tu carpeta en `/home/node/.n8n` dentro del contenedor.

Ejemplo:
```bash
sudo docker run -it --network host \
  --name n8n \
  -e GENERIC_TIMEZONE="Europe/Madrid" \
  -e N8N_HOST="localhost" \
  -e N8N_PORT=5678 \
  -v /home/tuusuario/n8n_data:/home/node/.n8n \
  --restart unless-stopped \
  n8nio/n8n
```

- **Explicación de la Opción `-v`**:
  - `/home/tuusuario/n8n_data`: Ruta en tu sistema anfitrión.
  - `:/home/node/.n8n`: Ubicación dentro del contenedor donde se montará el volumen.

### 3. Cambiar los Permisos de la Carpeta
Asegúrate de que la carpeta `/home/tuusuario/n8n_data` tenga permisos adecuados para el usuario `node` (que corre n8n en el contenedor). El UID y GID del usuario dentro del contenedor son 1000.

Ejecuta:
```bash
sudo chown -R 1000:1000 /home/tuusuario/n8n_data
```

### 4. Verificar que los Datos se Están Guardando
Después de iniciar el contenedor por primera vez, verás archivos como `database.sqlite` y `config` en `/home/tuusuario/n8n_data`. Esto significa que la persistencia está funcionando correctamente.

---

## Resumen del Comando Final

```bash
sudo docker run -it --network host \
  --name n8n \
  -e GENERIC_TIMEZONE="Europe/Madrid" \
  -e N8N_HOST="localhost" \
  -e N8N_PORT=5678 \
  -v /home/tuusuario/n8n_data:/home/node/.n8n \
  --restart unless-stopped \
  n8nio/n8n
```

---

## Consejos Adicionales

- **Actualizar la Imagen**: Si decides actualizar la imagen de Docker, solo necesitarás eliminar el contenedor y volverlo a crear con los mismos parámetros. Los datos en tu carpeta `/home/tuusuario/n8n_data` permanecerán intactos.
  
  ```bash
  sudo docker stop n8n && sudo docker rm n8n
  ```

- **Gestionar el Volumen**: Si necesitas mover la ubicación de los datos, simplemente desmonta el volumen actual y monta una nueva ruta.

---

Con estos pasos, tu instancia de n8n en Docker será completamente persistente y no perderá ningún dato incluso después de reiniciar tu sistema.
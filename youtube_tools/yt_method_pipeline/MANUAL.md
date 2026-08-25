# Manual de puesta en marcha — yt_method_pipeline

Esta guía explica, paso a paso y desde cero, cómo poner en marcha el pipeline
y **por qué** cada paso existe y va en ese orden. El `README.md` es la
referencia rápida de comandos; este documento es la explicación larga para
la primera vez (o para cuando vuelvas dentro de unos meses y no te acuerdes
de nada).

## Qué hace esto, en una frase

A partir de una o varias fuentes de YouTube (uno o varios canales, playlists,
vídeos sueltos o búsquedas por título), descarga las transcripciones, se
queda solo con los vídeos que explican un método de generar ingresos
(descarta entrevistas y demás), extrae esa información en un formato
estructurado, la limpia/normaliza, y te da un dashboard interactivo para
explorar los métodos, ver huecos de mercado y combinar ideas — todo
corriendo en tu máquina, sin mandar nada a ningún servicio de pago.

## 0. Requisitos previos

- **Python 3.10+** con `venv`. El proyecto usa sintaxis de tipos moderna
  (`str | None`), no funciona en versiones más antiguas.
- **[Ollama](https://ollama.com) instalado y corriendo** (`ollama serve`, o
  como servicio del sistema). Es lo que hace posible que todo el análisis
  (extracción, embeddings, informe) corra localmente y gratis, en vez de
  depender de una API de pago con límites de cuota. Es la pieza más
  importante de todo el sistema: sin Ollama corriendo, nada funciona salvo
  que cambies a `LLM_PROVIDER=anthropic`.
- **Los modelos de Ollama descargados** (ver paso 2).
- **Un navegador** con sesión iniciada en YouTube (Brave, Chrome...) — se
  usa opcionalmente para leer cookies y poder descargar transcripciones de
  vídeos con restricción de edad.
- **git**, para tener el repo.

¿Por qué Ollama y no directamente Claude API? Porque el volumen de llamadas
que hace este pipeline (una por cada vídeo, con transcripciones que pueden
ser muy largas) sale gratis en local y no depende de una cuota externa que
se puede agotar a mitad de una tanda de 100 vídeos (nos pasó — ver la
sección de problemas conocidos). Claude API sigue disponible como
alternativa (`LLM_PROVIDER=anthropic`) si algún día prefieres esa vía.

## 1. Instalación

```bash
cd yt_method_pipeline
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

**Por qué un entorno virtual (`venv`)**: aísla las dependencias de este
proyecto del resto de tu sistema. Importante en particular porque el propio
sistema puede tener otra versión de `yt-dlp` instalada (p.ej. vía snap) que
está sandboxed y no puede leer las cookies reales de tu navegador — nos
pasó, y por eso el código llama siempre a `python -m yt_dlp` usando
explícitamente el intérprete del venv, nunca al `yt-dlp` que haya en el
`PATH` del sistema.

**Por qué todos los comandos de este manual usan `.venv/bin/python cli.py`
en vez de solo `python cli.py`**: si usas conda además de `venv` (habitual
si trabajas con varios proyectos de Python/ML), es fácil acabar con un
entorno conda que se llama igual que la carpeta del proyecto
(`yt_method_pipeline`) sin darte cuenta — algún IDE o herramienta lo crea
automáticamente. Cuando ese entorno conda está activo, tu prompt muestra
`(yt_method_pipeline)` igual que si fuera el `venv` del proyecto, pero es
un intérprete de Python completamente distinto, sin las dependencias
instaladas aquí (`pip install -r requirements.txt` las puso en `.venv/`,
no en ese entorno conda) — nos pasó justo así. Usar la ruta explícita
`.venv/bin/python` evita ese lío por completo, sea cual sea el entorno que
tengas activo en el shell. Compruébalo con `conda env list` si quieres ver
si tienes ese mismo problema.

**Por qué `.env` en vez de meter las claves en el código**: `.env` está en
`.gitignore`, así que tus claves (si usas Claude API) o configuración local
nunca se suben al repositorio por accidente.

## 2. Preparar Ollama

```bash
ollama serve                       # si no corre ya como servicio
ollama pull qwen3:14b              # modelo de extracción/razonamiento
ollama pull qwen3-embedding:8b     # modelo de embeddings para búsqueda semántica
```

**Por qué `qwen3:14b`**: de los modelos probados en esta máquina es el que
mejor sigue instrucciones complejas en español y soporta modo de salida
estructurada nativo de Ollama (`format` con JSON Schema), que es lo que
usamos para forzar que la respuesta encaje siempre con el schema de 22
campos sin tener que parsear texto libre.

**Por qué un modelo de embeddings aparte (`qwen3-embedding:8b`)**: los
modelos de chat no están entrenados para generar vectores de similitud
semántica útiles; un modelo dedicado a embeddings da resultados mucho más
fiables para "busca vídeos parecidos a X" o para la vista de Similitud del
dashboard.

Comprueba que está todo bien:
```bash
ollama list      # deben aparecer los dos modelos
ollama ps         # modelos cargados en memoria (vacío hasta la primera llamada)
```

## 3. Los pasos del pipeline, en orden, y por qué van así

El pipeline está partido en pasos pequeños e **idempotentes** (relanzar un
paso no repite lo que ya estaba hecho, ni te machaca datos) a propósito:
cada paso puede tardar minutos u horas, así que si algo falla a mitad
(bloqueo de red, timeout, apagón) puedes cortar y retomar sin perder el
trabajo ya hecho.

### Paso 1 — `fetch`: descargar transcripciones

```bash
.venv/bin/python cli.py fetch @NombreCanal --limit 20
```

**Qué hace**: resuelve una o varias entradas (vía `yt-dlp`, sin descargar
nada todavía) a una lista de vídeos, y descarga la transcripción de cada uno
(primero con `youtube_transcript_api`, y si falla, con los subtítulos de
`yt-dlp` como alternativa).

**Entradas mixtas**: `fetch` acepta varias entradas a la vez, mezclables
libremente, autodetectadas por su forma:

```bash
# canal (comportamiento clásico)
.venv/bin/python cli.py fetch @AdrianSaenz --limit 50

# canal + playlist + un par de vídeos sueltos + un fichero de lista, todo junto
.venv/bin/python cli.py fetch @AdrianSaenz \
  "https://www.youtube.com/playlist?list=XXXX" \
  "https://youtu.be/XXXXXXXXXXX" \
  --list mis_videos.txt

# búsqueda por título (marca resuelto_por_titulo=true para que lo revises)
.venv/bin/python cli.py fetch "titulo:Cómo Ganar Dinero Con TikTok Sin Enseñar La Cara" \
  --title-channel @AdrianSaenz
```

- `@canal` o URL de canal → todos sus vídeos (usa `--limit` para acotar).
- URL de playlist → yt-dlp la expande sola; el canal real de cada vídeo se
  guarda por-vídeo, porque una playlist puede mezclar canales.
- URL o ID de vídeo suelto.
- `--list fichero.txt` (repetible) — una URL/ID por línea; usa el soporte
  nativo de `-a` de `yt-dlp`, así que las líneas vacías y las que empiezan
  por `#` se ignoran solas.
- `"titulo:texto a buscar"` — se resuelve con `ytsearch` (top 5, no solo el
  primero). Con `--title-channel @canal` prefiere, de esos 5, el resultado
  de ese canal exacto en vez de quedarse a ciegas con el primero. Si una
  búsqueda no encuentra nada, se registra un aviso y el resto de entradas de
  la misma llamada se sigue procesando — no aborta la ejecución.

Todas las entradas se deduplican por `video_id`: si el mismo vídeo llega por
dos fuentes distintas en la misma llamada, se procesa una sola vez.

**Por qué es el primer paso**: todo lo demás analiza *texto*, no vídeo —
necesitas el texto en disco antes de poder hacer nada con IA.

**Por qué es idempotente**: si `transcript.txt` ya existe para un
`video_id`, se salta. Puedes ir subiendo el `--limit` poco a poco (10, luego
50, luego 100), o añadir fuentes nuevas en llamadas sucesivas, y nunca vuelve
a descargar lo que ya tenías. El nombre de la carpeta de cada vídeo lleva el
`video_id` como sufijo (no solo el título) para que, si el canal le cambia
el título a un vídeo más adelante, el pipeline lo siga reconociendo como "ya
descargado" en vez de intentar bajarlo de nuevo.

**Procedencia en `meta.json`**: cada vídeo descargado guarda de dónde vino,
en campos separados del canal real al que pertenece:
```json
{
  "canal_nombre": "Adrián Sáenz",
  "canal_id": "UCVt4ugq2txl_szlXAO7B3-g",
  "fuente_origen": "canal",
  "fuente_detalle": "@AdrianSaenz",
  "resuelto_por_titulo": false
}
```
`fuente_origen` es uno de `canal` / `playlist` / `video` / `lista_fichero` /
`busqueda_titulo`. `canal_nombre`/`canal_id` son el canal real del vídeo,
no la fuente por la que entró (relevante en playlists mixtas). Estos campos
llegan hasta el dashboard vía `normalize` (ver más abajo el filtro por
fuente).

**`reannotate` — rellenar la procedencia en vídeos ya descargados**:
```bash
.venv/bin/python cli.py reannotate --channel-hint @AdrianSaenz
```
Si ya tenías vídeos descargados antes de que existiera este campo, sus
`meta.json` no tienen `canal_nombre`/`fuente_origen`/etc. `reannotate` los
recorre, resuelve el canal real de cada uno contra YouTube (sin descargar
ninguna transcripción) y rellena solo lo que falte. Como esos vídeos solo
pudieron llegar por el flujo antiguo de "un canal a la vez", se les asigna
`fuente_origen="canal"` y `fuente_detalle` = el valor que le pases en
`--channel-hint` (indícalo tú explícitamente; no se adivina de
`data/channel.json`, que se sobrescribe en cada `fetch` y puede llevar a
etiquetar mal vídeos antiguos si mientras tanto ya usaste otra fuente).

**Variables relevantes** (en `.env`):
- `YT_COOKIES_FROM_BROWSER=brave` — de qué navegador coger cookies, para
  poder acceder a vídeos con restricción de edad. *Ojo*: se usa como último
  recurso, no siempre — probamos primero sin cookies porque en este entorno
  las cookies de Brave hacían que YouTube devolviera errores en casi todas
  las peticiones (ver problemas conocidos).
- `FETCH_DELAY=1.5` — segundos de pausa entre vídeos, para no disparar el
  límite de peticiones de YouTube en tandas grandes.

### Paso 2 — `classify`: filtrar solo métodos de negocio reales

```bash
.venv/bin/python cli.py classify
```

**Qué hace**: para cada transcripción descargada, un LLM lee el título + el
principio del texto y decide si el vídeo explica un método de ingresos
replicable, o si es otra cosa (entrevista, noticia, documental...).

**Por qué existe como paso separado, antes de `extract`**: `extract` es la
parte cara del pipeline (minutos por vídeo). Sin este filtro, gastarías ese
tiempo analizando vídeos irrelevantes con el schema de "método de negocio" —
y además contaminarías el dashboard con datos sin sentido (nos pasó con una
entrevista a un narcotraficante que salió clasificada con `red_flags` y
`categoria` como si fuera un tutorial de dropshipping). Filtrar por título
solo no basta: un vídeo puede llamarse "El rentable negocio de..." y ser una
entrevista, no un tutorial — por eso este paso lee también el principio de
la transcripción.

**Qué hace con lo ya extraído**: si relanzas `classify` después de haber
corrido `extract`, y algún vídeo cambia de "sí es método" a "no lo es", se
borran su `method.json`/`embedding.json` (quedan obsoletos) pero **nunca**
se borra `transcript.txt` — puedes revertir la clasificación a mano sin
tener que volver a descargar nada.

**Si no estás de acuerdo con una clasificación**: edita a mano el
`classification.json` de ese vídeo (dentro de
`data/transcripts/<vídeo>/`) y cambia `es_metodo_negocio`.

### Paso 3 — `extract`: la extracción estructurada (el paso lento)

```bash
.venv/bin/python cli.py extract
```

**Qué hace**: por cada vídeo que pasó el filtro, le pide al LLM que rellene
un JSON con 22 campos organizados en 6 bloques — identificación, economía,
requisitos y barreras de entrada, ejecución, credibilidad/riesgo, y
meta/fuente (`schemas/method_extraction.json`) — y lo valida contra ese
schema antes de guardarlo.

**Por qué un schema tan detallado**: la gracia de tener datos estructurados
en vez de "resúmenes en prosa" es poder comparar y cruzar vídeos entre sí
después (rejilla de huecos, combinador...). Con texto libre eso no es
posible; con campos cerrados (`escalabilidad: alta/media/baja`, etc.) sí.

**Por qué tarda lo que tarda**: cada llamada al modelo tiene que leer toda
la transcripción (hasta ~130.000 caracteres en los vídeos más largos) y
generar una respuesta de cientos de líneas de JSON. El pipeline ajusta el
contexto de Ollama al tamaño real de cada transcripción (en vez de usar
siempre el máximo) y procesa de más corta a más larga para minimizar
recargas del modelo — así que, en general, los vídeos cortos van rápido
(~1 min) y solo los más largos se acercan a varios minutos.

### Paso 4 — `index`: embeddings para búsqueda semántica

```bash
.venv/bin/python cli.py index
.venv/bin/python cli.py search "dropshipping con poca inversión inicial"
```

**Qué hace**: construye, para cada vídeo, un resumen normalizado en texto
plano a partir de su `method.json` ya validado (no de la transcripción
cruda) y calcula su embedding con `qwen3-embedding:8b`.

**Por qué sobre el resumen normalizado y no sobre la transcripción**: la
transcripción cruda tiene muletillas, ruido, repeticiones — el embedding
saldría dominado por el "cómo habla" en vez de "qué dice el método". El
resumen normalizado es una traducción determinista (sin LLM, sin
variabilidad) de los campos ya extraídos a una frase larga en español,
pensada para que el embedding capture el *contenido* del método.

**Para qué sirve luego**: para `search` (búsqueda por significado, no por
palabra exacta) y para la vista de Similitud del dashboard.

### Paso 5 — `normalize`: limpiar y homogeneizar (el único paso manual/iterativo)

```bash
.venv/bin/python cli.py normalize
```

**Qué hace**: el LLM, al extraer `mecanismo_valor`, `canal_apalancamiento` y
`audiencia` en el paso 3, escribe frases libres — el mismo concepto sale
escrito de mil formas distintas entre vídeos ("redes_sociales" vs "redes
sociales" vs "instagram"). Este paso colapsa esas frases libres a un
vocabulario canónico corto (6-8 valores por campo), definido por ti en
`configs/normalization.json`, y calcula un `potencial` transparente (pesos
declarados en ese mismo archivo, no escondidos en el código).

**Por qué es el único paso que NO se puede automatizar del todo**: decidir
que "trading y creación de contenido" y "creacion_de_contenido_profesional"
son "lo mismo" (o no) requiere criterio humano sobre el dominio — un
algoritmo no puede juzgar eso de forma fiable. Por eso el diseño es: el
sistema te dice qué valores no sabe clasificar (`_pendientes` en el
config), tú decides, y relanzas cuantas veces quieras. No pasa nada si al
principio la cobertura sale baja (16% en nuestra primera pasada con 43
vídeos) — es el punto de partida esperado, no un fallo.

**Cómo se usa, en la práctica**:
1. Corre `normalize` la primera vez.
2. Abre `data/normalization_report.html` en el navegador — te dice la
   cobertura (semáforo verde/ámbar/rojo) y lista, por campo, qué valores
   están sin mapear.
3. Abre `configs/normalization.json`, añade entradas al `map` de cada
   campo (mapeando el valor crudo a uno de los valores de `canonico`).
4. Vuelve a correr `normalize`. Repite hasta que la cobertura te convenza
   (no hace falta el 100%; con 40-75% el semáforo ya pasa a ámbar y la
   rejilla de huecos empieza a ser razonablemente fiable).

**Por qué esto no está en el `run` automático**: precisamente porque quiere
tu revisión activa. Meterlo en la cadena automática animaría a confiar en
huecos calculados sobre datos sin normalizar.

**La categoría también se re-etiqueta, y no por su propio valor**: la
`categoria` que pone el LLM en `extract` resultó poco fiable — en nuestros
43 vídeos, 13 estaban etiquetados `inversion_trading` pero solo 5 eran
negocios financieros de verdad (los otros 8 eran Skool, servicios con IA,
ecommerce...). En vez de fiarnos de esa etiqueta, `categoria_norm` se
reasigna a partir de `mecanismo_norm` (una señal más fiable: es un campo
más concreto y con menos margen de ambigüedad para el LLM), usando el mapa
`categoria_por_mecanismo` del config — editable igual que el resto.

### Paso 6 — `dashboard`: la vista interactiva

```bash
.venv/bin/python cli.py dashboard
```
Ábrelo con `file:///.../data/dashboard.html` directamente en el navegador.

**Qué hace**: genera un único HTML autónomo (tipografías y datos
incrustados, cero peticiones de red salvo el botón de generar idea) con
seis vistas:
- **Expediente** — las respuestas de los 6 bloques de cada vídeo, en
  formato legible, más su `potencial`.
- **Rejilla de huecos** — combinaciones normalizadas (mecanismo × canal,
  canal × audiencia, categoría × inversión) que ningún vídeo del canal
  cubre todavía. Cada celda vacía muestra un **score estimado** (media del
  `potencial` de los vídeos que sostienen cada faceta por separado, no de
  vídeos que ya combinen ambas — por definición no existen) y su **n**
  (cuántos vídeos apoyan ese score); con n bajo se marca ⚠ "baja
  evidencia", porque un score alto sostenido por 1 solo vídeo es frágil.
  Las combinaciones que declares incompatibles en el config (p.ej.
  invertir en bolsa vía un marketplace no tiene sentido) se pintan como
  descartadas y no entran en el ranking; si el propio generador de ideas
  (ver más abajo) descarta una celda por inviable, también se pinta como
  descartada aunque no esté en el config. El toggle "solo huecos
  adyacentes" (activado por defecto) oculta huecos "de dos saltos" —
  combinaciones que no comparten fila ni columna con nada que el canal ya
  haga, y que por tanto son más especulativas. El panel "Top 50 huecos"
  ordena los mejores candidatos. Depende directamente de `normalize`: si
  la cobertura es baja, avisa de que los huecos pueden ser artefactos de
  datos sin mapear, no huecos reales.
- **Similitud** — parecido temático (embeddings) o ponderado (tú eliges
  con sliders qué facetas pesan).
- **Combinador** — mezcla primitivos de vídeos distintos y comprueba si la
  combinación ya existe o es nueva, con sugerencias automáticas.
- **Constructor de proyecto** — en vez de partir de una celda vacía de la
  rejilla, fijas tú mismo, faceta a faceta (mecanismo, canal, audiencia,
  categoría, inversión inicial, evidencia), la composición de un proyecto,
  y ves en vivo cuántos vídeos y qué potencial medio la sostienen. Para
  cada faceta que dejes en "(cualquiera)" te enseña qué valores siguen
  teniendo respaldo (con su n y potencial) dada la selección actual, y
  atenúa tanto los que se quedarían sin vídeos como los que serían
  incompatibles mecanismo×canal. El botón "Completar composición" rellena
  las facetas que dejes libres a partir de una o dos anclas, maximizando
  potencial×respaldo sin colar una incompatibilidad ni un hueco vacío —
  el resultado sigue siendo editable, no es una respuesta cerrada. El
  mismo botón "Generar idea" de la rejilla está aquí también, en cuanto
  fijas exactamente dos facetas compatibles.
- **Panorama** — vista de solo diagnóstico (no genera ideas) con seis
  gráficos para leer el terreno antes de decidir: mapas de calor
  mecanismo×canal y categoría×inversión (color = potencial medio, número =
  n, gris = hueco real, borde discontinuo = n=1 frágil, rayado = pareja
  marcada incompatible), una dispersión de potencial contra saturación de
  competencia coloreada por evidencia (con la zona "potencial alto +
  saturación baja/media" sombreada), barras de potencial medio y cuota por
  cada valor de mecanismo/canal/audiencia, el reparto de vídeos por
  categoría para ver de un vistazo en cuántos modelos distintos se
  concentra realmente el canal, y "En qué se diferencia cada fuente"
  (n, potencial medio, categorías y evidencia por canal — esta última
  siempre sobre todas las fuentes, sin aplicar el filtro de abajo, porque
  su objetivo es precisamente compararlas).

**Filtro por fuente**: si el corpus mezcla vídeos de más de un canal (ver
`fetch` con entradas mixtas, arriba), aparece un control de checkboxes
("Fuente") justo encima de las pestañas, visible en todas ellas. Huecos,
Similitud, Combinador, Constructor y Panorama (salvo la comparación por
fuente) recalculan solo con los vídeos de las fuentes marcadas; el
Expediente muestra de qué canal es cada vídeo y la exportación a
Markdown/PDF refleja el filtro activo. Con una sola fuente en el corpus el
control ni siquiera se muestra, y todo se comporta exactamente igual que
si esta función no existiera. En Similitud, si filtras a exactamente dos
fuentes, los pares muy parecidos entre canales distintos se resaltan con
un borde de acento — es la señal de que dos canales están enseñando casi
lo mismo.

En el Expediente, además, dos botones — **"⬇ Descargar Markdown"** y
**"🖨 Exportar a PDF"** — vuelcan a un único informe el estado actual de
las cuatro primeras vistas: la ficha completa de todos los vídeos, la
rejilla de huecos con el par de ejes que tengas seleccionado (más las
ideas ya generadas para esa combinación), la matriz de similitud en el
modo/orden que tengas activo, y tu selección vigente del combinador. El
PDF usa el diálogo de impresión nativo del navegador — sin librerías ni
conexión.

**Por qué depende de `methods_norm.json` y no del `method.json` crudo**:
porque la rejilla de huecos, el combinador, el constructor y el panorama
solo tienen sentido con vocabulario homogéneo — comparar "redes_sociales"
con "instagram" como si fueran cosas distintas rompería el propósito de
la herramienta.

### Paso 6b — `idea-server`: el botón "Generar idea"

```bash
.venv/bin/python cli.py idea-server    # en una terminal aparte, la dejas corriendo
```

**Qué hace**: en la Rejilla de huecos (o en el Constructor de proyecto,
fijando exactamente dos facetas) cada celda vacía o entrada del Top 50
tiene un botón "Generar idea" que le pide al LLM configurado una
propuesta de negocio concreta para esa combinación. El prompt
(`prompts/generate_idea.md`, editable a mano) trabaja en dos fases:
primero verifica si las dos facetas son económicamente compatibles
(p.ej. un mecanismo de renta pasiva sobre un activo propio no encaja con
un canal de venta consultiva salvo que haya un puente de negocio
explícito) — si no lo son, devuelve solo un motivo y una alternativa, sin
inventar una idea que no se sostiene; si sí lo son, redacta la
propuesta —nombre, cliente objetivo, propuesta de valor, primeros 3
pasos, herramientas sugeridas, por qué encaja (referenciando los vídeos
reales) y riesgos a vigilar— y marca `confianza: "baja"` si alguna de las
dos facetas se apoya en un solo vídeo del canal. La rejilla y el
constructor reflejan ambas señales: celdas descartadas por inviables se
pintan igual que las incompatibles por config, y las de confianza baja
llevan su propio indicador.

**Por qué hace falta un servidor aparte**: `data/dashboard.html` es un
fichero que abres con doble clic (`file://`) — si el botón llamara
directamente a un LLM desde el JavaScript de la página, o bien tu clave de
API tendría que estar escrita en el propio HTML (visible para cualquiera
que abra el archivo), o bien el navegador tendría que hablar directamente
con Ollama en tu máquina desde una página sin ningún control. En vez de
eso, el botón le hace una petición al servidor local (`http://localhost:8765`,
permitido desde una página `file://`, a diferencia de leer otro fichero
local), y es el servidor — un proceso Python en tu máquina — quien llama
al LLM.

**Qué proveedor usa**: el mismo `LLM_PROVIDER` que el resto del pipeline
(Ollama por defecto, gratis y local; Claude API si pones
`LLM_PROVIDER=anthropic` y `ANTHROPIC_API_KEY` en `.env` — útil si algún
día quieres la calidad de Claude para esta tarea puntual en concreto, ya
que es solo una llamada por idea que pidas, no una por vídeo).

**Caché**: cada idea se guarda en
`data/ideas/<eje_a>=<valor_a>__<eje_b>=<valor_b>.json` (los ejes pueden
ser cualquier pareja de mecanismo/canal/audiencia/categoría/inversión, no
solo mecanismo×canal). Si vuelves a pedir la misma combinación, el
servidor —o el propio dashboard, si ya está en `cached_ideas`— devuelve
la versión cacheada sin volver a llamar al LLM.

### Paso 6c — `scripts/generate_post.py`: borradores de post para LinkedIn

```bash
# la primera vez, instala Playwright y descarga su navegador:
.venv/bin/pip install playwright
.venv/bin/playwright install chromium

.venv/bin/python scripts/generate_post.py --pestana huecos
```

**Qué hace**: coge una pestaña del dashboard, calcula en Python (sobre
`methods_norm.json` y los `embedding.json`, nunca inventadas) el hallazgo
más relevante de esa vista, le pide a un LLM que redacte un post de
LinkedIn con esas cifras exactas, y genera con Playwright/Chromium una
captura de página completa de esa pestaña (cabecera, KPIs, barra de
pestañas y todo el contenido) más una tarjeta social 1200×627 con el
hallazgo resumido. Deja todo en
`data/linkedin_posts/<fecha>-<pestana>/post.txt` + imágenes + `meta.json`
(con las cifras exactas citadas, para trazabilidad).

**No publica nada.** No hay integración con la API de LinkedIn ni scraping
— el flujo termina en el borrador; tú lo revisas y lo subes a mano cuando
quieras.

**Cómo elige el hallazgo**: cada pestaña tiene su propia regla (huecos:
una celda vacía cuyos dos primitivos, por separado, tienen n≥2 y potencial
medio alto, nunca destacando un n=1 sin avisarlo; combinador: una terna
que no exista ya en el corpus, buscada entre las mejores candidatas por
potencial; similitud: el par más parecido y cuántos otros pares superan un
umbral alto; panorama: el primitivo con mejor combinación de potencial
alto y cuota baja, o la concentración por categoría). Puedes fijar tú la
idea con `--destacado "texto libre"` en vez de dejar que el script elija.

**Anonimizado por defecto**: `--enfoque metodologia` (por defecto) quita
el nombre del canal tanto del texto como de la captura (se reemplaza el
subtítulo del dashboard y cualquier etiqueta de canal, vía JavaScript
inyectado en la página ya cargada — no toca `pipeline/dashboard_template.html`
para nada); `--enfoque nombres_reales` permite citarlo.

**Proveedor del LLM**: por defecto llama a la API de Anthropic (necesita
`ANTHROPIC_API_KEY` en `.env`, igual que el resto del proyecto cuando usas
Claude). Si la API no está disponible (cuota, sin conexión...), usa
`--provider ollama` para redactar el mismo prompt 100% en local con
`qwen3:14b` (o el modelo que pases con `--ollama-model`) — `meta.json`
registra siempre qué proveedor y modelo escribió cada borrador.

**El prompt de redacción** vive en `prompts/linkedin_post.md`, editable a
mano — ahí están el tono, las reglas de longitud/hashtags, y la instrucción
de que el texto haga referencia explícita a lo que se ve en la captura
adjunta.

### Paso 6d — `scripts/annotate_screenshots.py`: capturas explicadas de cada pestaña

```bash
.venv/bin/python scripts/annotate_screenshots.py                  # las 6 pestañas
.venv/bin/python scripts/annotate_screenshots.py --pestana huecos  # solo una
```

**Qué hace**: para cada pestaña del dashboard, abre `data/dashboard.html`
con Playwright, activa esa vista, e inyecta —vía JavaScript, en el DOM ya
cargado, sin tocar `pipeline/dashboard_template.html`— una franja arriba
del todo con el título de la pestaña y una explicación de qué hace, en el
mismo estilo visual del dashboard (misma paleta, misma tipografía). Luego
hace una captura de página completa, igual que `generate_post.py`.

**Diferencia con `generate_post.py`**: este script no llama a ningún LLM ni
calcula ningún hallazgo — el texto de cada franja es fijo y descriptivo
(qué hace la pestaña, no qué dice de tus datos concretos), pensado para
documentación o para acompañar una explicación del proyecto sin depender
de una cifra que pueda quedar desactualizada. Si lo que quieres es un post
con un hallazgo real y sus cifras, usa `generate_post.py`; si quieres una
imagen que simplemente explique "esto es lo que hace esta pestaña", usa
`annotate_screenshots.py`.

**Salida**: `data/capturas_explicadas/<pestana>.png` — una imagen por
pestaña, sin `post.txt` ni `meta.json` (no hay cifras que trazar). Acepta
`--enfoque metodologia|nombres_reales` (anonimizado igual que en
`generate_post.py`) y `--salida` para cambiar la carpeta de destino.

### Paso 7 — `report`: informe agregado en Markdown

```bash
.venv/bin/python cli.py report
```

**Qué hace**: agrega todos los `method.json`, genera tablas de
distribuciones/contraste y le pide al LLM (con razonamiento activado, ya
que es solo una llamada) que proponga combinaciones de primitivos nuevas.

**Diferencia con el dashboard**: el `report` es un resumen estático para
leer de un tirón; el dashboard es para explorar de forma interactiva. Se
complementan, no se sustituyen.

## 4. El atajo `run`

```bash
.venv/bin/python cli.py run @NombreCanal --limit 100
```

Encadena `fetch → classify → extract → index → report`. **A propósito deja
fuera `normalize` y `dashboard`** — el primero porque necesita tu revisión,
el segundo porque depende del primero. Después de `run`, el ciclo normal es:

```bash
.venv/bin/python cli.py normalize     # revisar data/normalization_report.html, iterar
.venv/bin/python cli.py dashboard
```

## 5. Problemas conocidos (y por qué pasan)

- **`RequestBlocked` / `IpBlocked` de `youtube_transcript_api`, o `429` en
  `yt-dlp`**: YouTube limita peticiones por IP cuando detecta un patrón de
  scraping (tandas grandes y rápidas — nos pasó relanzando `fetch` con
  `--limit 150`: los 70 vídeos nuevos fallaron todos con `429`). El pipeline
  detecta ambos casos por separado y no malgasta reintentos en ninguno de
  los dos: en cuanto detecta el bloqueo de `youtube_transcript_api` pasa
  directo al fallback de `yt-dlp` el resto de la ejecución, y si ese
  fallback también empieza a devolver `429`/`"the page needs to be
  reloaded"`, deja de intentarlo también — así los vídeos restantes fallan
  al instante en vez de perder ~30s cada uno. No hay nada que hacer salvo
  esperar un rato y reintentar (relanzar `fetch` es idempotente y seguro,
  solo reintenta lo que falló). Para tandas grandes, considera subir
  `FETCH_DELAY` en `.env` para reducir la probabilidad de que pase.
- **Vídeos con restricción de edad**: `youtube_transcript_api` no soporta
  ahora mismo autenticación por cookies (rotura reciente de la propia
  librería); el fallback de `yt-dlp` con `--cookies-from-browser` puede
  rescatar algunos si tu cuenta de YouTube tiene la edad verificada — si
  no, simplemente ese vídeo se queda sin transcripción y aparece en
  `data/logs/no_transcript.log`.
- **Timeouts en `extract` con transcripciones muy largas**: si un vídeo
  concreto se queda atascado agotando reintentos sin avanzar (lo vimos con
  una transcripción de 133.000 caracteres), es más rápido excluirlo a mano
  que esperar: pon `"es_metodo_negocio": false` en su
  `classification.json` con un motivo, y relanza `extract` — se salta
  automáticamente.
- **`OLLAMA_NUM_CTX` y VRAM**: con poca VRAM, Ollama reparte el modelo
  entre GPU y CPU en vídeos largos, mucho más lento. Si tu GPU es más
  pequeña que la usada aquí (RTX 3060, 12GB), puedes bajar
  `OLLAMA_NUM_CTX` en `.env`, a costa de arriesgarte a truncar
  transcripciones muy largas.
- **`python cli.py ...` falla o usa las dependencias equivocadas**: casi
  siempre es que el `python` de tu shell no es el del `.venv` del proyecto
  — sobre todo si usas conda y tienes (o algo te creó) un entorno con el
  mismo nombre que la carpeta del proyecto, que activa un intérprete
  distinto mostrando el mismo `(yt_method_pipeline)` en el prompt. La
  solución es usar siempre la ruta explícita: `.venv/bin/python cli.py ...`
  (así están escritos todos los comandos de este manual). Compruébalo con
  `conda env list`.
- **`OSError: [Errno 98] Address already in use` al lanzar `idea-server`**:
  ya tienes un `idea-server` corriendo en otra terminal (o quedó huérfano
  de una sesión anterior). Compruébalo con `ss -ltnp | grep 8765` y mata el
  proceso que aparezca (`kill <pid>`) antes de relanzar. Si acabas de
  cambiar código de `idea_server.py`, también tienes que reiniciarlo — un
  proceso Python ya arrancado no recoge cambios de fichero solo.

## 6. De cero a dashboard: resumen de comandos

```bash
# 0-2: preparación (una sola vez)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
ollama pull qwen3:14b
ollama pull qwen3-embedding:8b

# 3: el pipeline (run acepta las mismas entradas mezclables que fetch:
# canal, playlist, vídeo suelto, --list, "titulo:...")
.venv/bin/python cli.py run @NombreCanal --limit 100
.venv/bin/python cli.py normalize
# -> abrir data/normalization_report.html, completar configs/normalization.json, repetir
.venv/bin/python cli.py dashboard
# -> abrir data/dashboard.html

# 4 (opcional, para el botón "Generar idea" de la rejilla de huecos y del
# constructor de proyecto): en otra terminal, la dejas corriendo
.venv/bin/python cli.py idea-server
```

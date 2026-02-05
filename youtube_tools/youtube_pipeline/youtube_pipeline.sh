#!/usr/bin/env bash
set -euo pipefail

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                     YOUTUBE CORPUS PIPELINE                                ║
# ║  Script unificado para descargar transcripciones y crear corpus           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
# Uso:
#   ./youtube_pipeline.sh [URL_CANAL]
#   ./youtube_pipeline.sh                    # Modo interactivo completo
#   ./youtube_pipeline.sh "https://..."      # Con URL predefinida
#
# Requisitos:
#   - yt-dlp (pip install -U yt-dlp)
#   - python3
#
# Variables de entorno opcionales:
#   YT_COOKIES_FROM_BROWSER=chrome
#   YT_COOKIES_FILE=/ruta/a/cookies.txt

VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE=""
BASE_OUTPUT_DIR="./canales"
LAST_VIDEO_COUNT=0
LAST_OK_COUNT=0
LAST_CORPUS_FILE=""

# ═══════════════════════════════════════════════════════════════════════════
# COLORES Y FORMATO
# ═══════════════════════════════════════════════════════════════════════════
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ═══════════════════════════════════════════════════════════════════════════

print_header() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════════════════╗"
    echo "║                     YOUTUBE CORPUS PIPELINE v${VERSION}                      ║"
    echo "╚═══════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${CYAN}  PASO $1: $2${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "$msg"
    if [[ -n "$LOG_FILE" ]]; then
        mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true
        echo "$msg" >> "$LOG_FILE" 2>/dev/null || true
    fi
}

log_success() { log "${GREEN}✔ $1${NC}"; }
log_warning() { log "${YELLOW}⚠ $1${NC}"; }
log_error() { log "${RED}✖ $1${NC}"; }
log_info() { log "${BLUE}ℹ $1${NC}"; }

confirm() {
    local prompt="$1"
    local default="${2:-n}"
    local response
    
    if [[ "$default" == "y" ]]; then
        prompt="$prompt [Y/n]: "
    else
        prompt="$prompt [y/N]: "
    fi
    
    # Usar printf y leer de /dev/tty para asegurar interactividad
    printf "${YELLOW}%s${NC}" "$prompt" >/dev/tty
    read -r response </dev/tty || response="$default"
    response="${response:-$default}"
    [[ "$response" =~ ^[Yy] ]]
}

prompt_input() {
    local prompt="$1"
    local default="${2:-}"
    local response
    
    if [[ -n "$default" ]]; then
        printf "${CYAN}%s ${NC}[%s]: " "$prompt" "$default" >/dev/tty
    else
        printf "${CYAN}%s: ${NC}" "$prompt" >/dev/tty
    fi
    
    # Leer respuesta del usuario
    if read -r response </dev/tty; then
        : # OK
    else
        response="$default"
    fi
    
    # Devolver respuesta o default
    echo "${response:-$default}"
}

check_dependencies() {
    echo ""
    echo -e "${BOLD}Verificando dependencias...${NC}"
    
    local missing=()
    
    if command -v yt-dlp >/dev/null 2>&1; then
        echo -e "  ${GREEN}✔${NC} yt-dlp: $(yt-dlp --version 2>/dev/null || echo 'instalado')"
    else
        echo -e "  ${RED}✖${NC} yt-dlp: NO INSTALADO"
        missing+=("yt-dlp")
    fi
    
    if command -v python3 >/dev/null 2>&1; then
        echo -e "  ${GREEN}✔${NC} python3: $(python3 --version 2>/dev/null | cut -d' ' -f2)"
    else
        echo -e "  ${RED}✖${NC} python3: NO INSTALADO"
        missing+=("python3")
    fi
    
    echo ""
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${RED}  ERROR: Faltan dependencias necesarias${NC}"
        echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
        echo ""
        echo "Instala las dependencias faltantes:"
        echo ""
        for dep in "${missing[@]}"; do
            case "$dep" in
                yt-dlp) 
                    echo "  yt-dlp:"
                    echo "    pip install -U yt-dlp"
                    echo "    # o con pipx:"
                    echo "    pipx install yt-dlp"
                    ;;
                python3) 
                    echo "  python3:"
                    echo "    sudo apt install python3"
                    ;;
            esac
            echo ""
        done
        exit 1
    fi
    
    echo -e "${GREEN}✔ Todas las dependencias están instaladas${NC}"
}

# Extraer nombre del canal de la URL
extract_channel_name() {
    local url="$1"
    local name=""
    
    # Intentar extraer @nombre
    if [[ "$url" =~ @([^/]+) ]]; then
        name="${BASH_REMATCH[1]}"
    # Intentar extraer /channel/nombre o /c/nombre
    elif [[ "$url" =~ /c(hannel)?/([^/]+) ]]; then
        name="${BASH_REMATCH[2]}"
    # Intentar extraer /user/nombre
    elif [[ "$url" =~ /user/([^/]+) ]]; then
        name="${BASH_REMATCH[1]}"
    fi
    
    # Limpiar nombre
    name=$(echo "$name" | tr -d '\r\n' | sed 's/[^a-zA-Z0-9_-]/_/g')
    echo "$name"
}

# Sanitizar nombre de archivo
sanitize() {
    local s="$1"
    s=$(printf "%s" "$s" | tr -d '\r')
    s=$(printf "%s" "$s" | sed 's/[\/\\]/-/g; s/:/ - /g; s/"/'\''/g; s/?//g; s/*//g; s/</(/g; s/>/)/g; s/|/-/g')
    s=$(printf "%s" "$s" | tr -d '\000-\037' | tr -s ' ' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    printf "%.180s" "$s"
}

# Convertir subtítulos a texto limpio
subs_to_text() {
    local f="$1"
    awk '
        /^WEBVTT/ { next }
        /^Kind:/ { next }
        /^Language:/ { next }
        /^NOTE/ { next }
        /^[0-9]{2}:[0-9]{2}:[0-9]{2}[\.,][0-9]{3} --> / { next }
        /^[0-9]+$/ { next }
        /align:/ { next }
        /position:/ { next }
        /^[[:space:]]*$/ { next }
        {
            gsub(/<[^>]*>/, " ")
            gsub(/&nbsp;/, " ")
            gsub(/&amp;/, "\\&")
            gsub(/&lt;/, "<")
            gsub(/&gt;/, ">")
            gsub(/\xef\xbb\xbf/, "")
            gsub(/[[:space:]]+/, " ")
            gsub(/^[[:space:]]+|[[:space:]]+$/, "")
            if (length($0) > 0 && $0 != prev) {
                print
                prev = $0
            }
        }
    ' "$f" | \
    awk '
        BEGIN { buf = "" }
        {
            if (buf != "") buf = buf " " $0
            else buf = $0
        }
        END {
            gsub(/([.!?]) +/, "\\1\n", buf)
            print buf
        }
    ' | sed '/^$/d; s/^[[:space:]]*//; s/[[:space:]]*$//'
}

# Slugify para anchors Markdown
slugify() {
    local input="$1"
    printf '%s' "$input" \
        | tr '[:upper:]' '[:lower:]' \
        | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g; s/-+/-/g' \
        || printf 'unknown'
}

# Convertir tamaño a bytes
to_bytes() {
    case "${1^^}" in
        *K) echo $((${1%[Kk]} * 1024)) ;;
        *M) echo $((${1%[Mm]} * 1048576)) ;;
        *G) echo $((${1%[Gg]} * 1073741824)) ;;
        *)  echo "$1" ;;
    esac
}

# ═══════════════════════════════════════════════════════════════════════════
# PASO 1: OBTENER URLs DEL CANAL
# ═══════════════════════════════════════════════════════════════════════════

step1_get_urls() {
    print_step "1" "OBTENER URLs DEL CANAL"
    
    local channel_url="$1"
    local channel_name="$2"
    local output_dir="$3"
    local limit="$4"
    local urls_file="$output_dir/urls.txt"
    
    mkdir -p "$output_dir"
    
    log_info "Canal: $channel_name"
    log_info "URL: $channel_url"
    log_info "Destino: $urls_file"
    [[ "$limit" -gt 0 ]] && log_info "Límite: $limit vídeos"
    
    echo ""
    
    # Construir comando
    local cmd="yt-dlp --flat-playlist --print \"%(webpage_url)s\" $COOKIES_ARGS"
    
    if [[ "$limit" -gt 0 ]]; then
        cmd="$cmd -I 1:$limit"
    fi
    
    cmd="$cmd \"$channel_url\""
    
    log_info "Obteniendo lista de vídeos..."
    
    # Ejecutar y guardar
    if eval "$cmd" > "$urls_file" 2>/dev/null; then
        LAST_VIDEO_COUNT=$(wc -l < "$urls_file")
        log_success "Se encontraron $LAST_VIDEO_COUNT vídeos"
    else
        log_error "Error al obtener URLs del canal"
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# PASO 2: ANALIZAR IDIOMAS DISPONIBLES
# ═══════════════════════════════════════════════════════════════════════════

step2_analyze_languages() {
    print_step "2" "ANALIZAR IDIOMAS DISPONIBLES"
    
    local urls_file="$1"
    local first_url=""
    
    # Obtener primera URL
    while IFS= read -r line || [[ -n "$line" ]]; do
        line=$(printf "%s" "$line" | tr -d '\r')
        [[ -z "$line" ]] && continue
        [[ "$line" == \#* ]] && continue
        first_url="$line"
        break
    done < "$urls_file"
    
    if [[ -z "$first_url" ]]; then
        log_error "No se encontraron URLs válidas"
        return 1
    fi
    
    log_info "Analizando: $first_url"
    echo ""
    
    local sub_info
    sub_info=$(yt-dlp $COOKIES_ARGS --list-subs "$first_url" 2>&1)
    
    local has_manual=$(echo "$sub_info" | grep -c "Available subtitles" || true)
    local has_auto=$(echo "$sub_info" | grep -c "Available automatic captions" || true)
    
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║              IDIOMAS DISPONIBLES                              ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    
    if [[ "$has_manual" -gt 0 ]]; then
        echo ""
        echo -e "${GREEN}📝 SUBTÍTULOS MANUALES:${NC}"
        echo "$sub_info" | awk '
            /Available subtitles/ { printing=1; next }
            /Available automatic/ { printing=0 }
            printing && /^[a-z]{2,}(-[a-zA-Z]+)?[[:space:]]/ {
                code=$1
                $1=""
                name=$0
                gsub(/vtt.*$/, "", name)
                gsub(/^[[:space:]]+|[[:space:]]+$/, "", name)
                printf "   %-12s %s\n", code, name
            }
        '
    fi
    
    if [[ "$has_auto" -gt 0 ]]; then
        echo ""
        echo -e "${YELLOW}🤖 SUBTÍTULOS AUTOMÁTICOS:${NC}"
        echo "$sub_info" | awk '
            /Available automatic captions/ { printing=1; next }
            printing && /^[a-z]{2,}(-[a-zA-Z]+)?[[:space:]]/ {
                code=$1
                if (code ~ /^(es|es-orig|en|en-orig|fr|de|it|pt|pt-PT|ca|eu|gl|zh-Hans|zh-Hant|ja|ko|ru|ar)$/) {
                    $1=""
                    name=$0
                    gsub(/vtt.*$/, "", name)
                    gsub(/^[[:space:]]+|[[:space:]]+$/, "", name)
                    printf "   %-12s %s\n", code, name
                }
            }
        '
        echo ""
        echo -e "   ${YELLOW}(Hay más idiomas. Escribe el código exacto si necesitas otro)${NC}"
    fi
    
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    
    # Guardar info para detección de default
    echo "$sub_info"
}

# ═══════════════════════════════════════════════════════════════════════════
# PASO 3: DESCARGAR TRANSCRIPCIONES
# ═══════════════════════════════════════════════════════════════════════════

step3_download_transcriptions() {
    print_step "3" "DESCARGAR TRANSCRIPCIONES"
    
    local urls_file="$1"
    local trans_dir="$2"
    local lang_code="$3"
    local resume_mode="$4"
    
    mkdir -p "$trans_dir"
    
    local tmp_dir
    tmp_dir="$(mktemp -d)"
    trap 'rm -rf "$tmp_dir"' RETURN
    
    # Contar total de vídeos a procesar
    local total_urls
    total_urls=$(grep -v '^#' "$urls_file" | grep -v '^$' | wc -l)
    
    log_info "Idioma: $lang_code"
    log_info "Destino: $trans_dir"
    log_info "Vídeos a procesar: $total_urls"
    [[ "$resume_mode" == "true" ]] && log_info "Modo resume: activado"
    echo ""
    
    local current=0 ok=0 no_sub=0 err=0 skipped=0
    
    while IFS= read -r url || [[ -n "$url" ]]; do
        url=$(printf "%s" "$url" | tr -d '\r')
        [[ -z "$url" ]] && continue
        [[ "$url" == \#* ]] && continue
        
        current=$((current + 1))
        echo -e "${BLUE}▶ [$current/$total_urls]${NC} $url"
        
        # Obtener ID y título
        local vid_id title_raw title out_txt
        vid_id=$(yt-dlp $COOKIES_ARGS --skip-download --get-id "$url" 2>/dev/null) || {
            log_error "  Error obteniendo ID"
            err=$((err + 1))
            continue
        }
        
        title_raw=$(yt-dlp $COOKIES_ARGS --skip-download -e "$url" 2>/dev/null) || {
            log_error "  Error obteniendo título"
            err=$((err + 1))
            continue
        }
        
        # Obtener fecha de subida
        local upload_date=""
        upload_date=$(yt-dlp $COOKIES_ARGS --skip-download --print "%(upload_date)s" "$url" 2>/dev/null) || true
        # Formatear fecha de YYYYMMDD a YYYY-MM-DD
        if [[ -n "$upload_date" ]] && [[ ${#upload_date} -eq 8 ]]; then
            upload_date="${upload_date:0:4}-${upload_date:4:2}-${upload_date:6:2}"
        fi
        
        title=$(sanitize "$title_raw")
        [[ -z "$title" ]] && title="video_${vid_id}"
        out_txt="$trans_dir/${title}.txt"
        
        # Modo resume: saltar si ya existe
        if [[ "$resume_mode" == "true" ]] && [[ -f "$out_txt" ]]; then
            echo -e "  ${YELLOW}⏭ Ya existe, saltando${NC}"
            skipped=$((skipped + 1))
            continue
        fi
        
        rm -f "$tmp_dir"/* 2>/dev/null || true
        
        local found_file="" sub_type=""
        
        # Intentar subtítulos MANUALES primero
        yt-dlp $COOKIES_ARGS \
            --skip-download \
            --write-sub \
            --sub-langs "$lang_code" \
            --sub-format "vtt/srt/best" \
            -o "$tmp_dir/%(id)s.%(ext)s" \
            "$url" >/dev/null 2>&1 || true
        
        for f in "$tmp_dir"/*.vtt "$tmp_dir"/*.srt; do
            if [[ -f "$f" ]]; then
                found_file="$f"
                sub_type="manual"
                break
            fi
        done
        
        # Si no hay manuales, intentar AUTOMÁTICOS
        if [[ -z "$found_file" ]]; then
            yt-dlp $COOKIES_ARGS \
                --skip-download \
                --write-auto-sub \
                --sub-langs "$lang_code" \
                --sub-format "vtt/srt/best" \
                -o "$tmp_dir/%(id)s.%(ext)s" \
                "$url" >/dev/null 2>&1 || true
            
            for f in "$tmp_dir"/*.vtt "$tmp_dir"/*.srt; do
                if [[ -f "$f" ]]; then
                    found_file="$f"
                    sub_type="auto"
                    break
                fi
            done
        fi
        
        if [[ -n "$found_file" ]] && [[ -f "$found_file" ]]; then
            local base found_lang
            base=$(basename "$found_file")
            found_lang=$(echo "$base" | sed -E 's/^[^.]+\.(.+)\.(vtt|srt)$/\1/')
            [[ -z "$found_lang" ]] && found_lang="$lang_code"
            
            {
                echo "# Título: $title_raw"
                echo "# URL: https://www.youtube.com/watch?v=${vid_id}"
                echo "# Fecha: $upload_date"
                echo "# Idioma: $found_lang ($sub_type)"
                echo "#"
                subs_to_text "$found_file"
            } > "$out_txt"
            
            echo -e "  ${GREEN}✔ OK ($sub_type)${NC}"
            ok=$((ok + 1))
        else
            echo -e "  ${YELLOW}⚠ Sin subtítulos en '$lang_code'${NC}"
            no_sub=$((no_sub + 1))
        fi
        
        rm -f "$tmp_dir"/* 2>/dev/null || true
        
    done < "$urls_file"
    
    echo ""
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                    RESUMEN TRANSCRIPCIONES                    ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo -e "  Total procesados:    $current"
    echo -e "  ${GREEN}✔ Exitosos:          $ok${NC}"
    [[ "$skipped" -gt 0 ]] && echo -e "  ${YELLOW}⏭ Saltados (resume): $skipped${NC}"
    echo -e "  ${YELLOW}⚠ Sin subtítulos:    $no_sub${NC}"
    echo -e "  ${RED}✖ Errores:           $err${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    
    # Guardar número de exitosos en variable global
    LAST_OK_COUNT="$ok"
}

# ═══════════════════════════════════════════════════════════════════════════
# PASO 4: CREAR CORPUS
# ═══════════════════════════════════════════════════════════════════════════

step4_create_corpus() {
    print_step "4" "CREAR CORPUS MARKDOWN"
    
    local trans_dir="$1"
    local corpus_dir="$2"
    local channel_name="$3"
    
    # Convertir a rutas absolutas
    trans_dir="$(cd "$trans_dir" && pwd)"
    mkdir -p "$corpus_dir"
    corpus_dir="$(cd "$corpus_dir" && pwd)"
    
    local corpus_file="$corpus_dir/${channel_name}_corpus.md"
    
    log_info "Origen: $trans_dir"
    log_info "Destino: $corpus_file"
    echo ""
    
    # Encontrar archivos (sin cambiar de directorio)
    local -a files
    mapfile -t files < <(find "$trans_dir" -maxdepth 1 -name "*.txt" -type f | sort -f)
    
    if [[ ${#files[@]} -eq 0 ]]; then
        log_error "No se encontraron archivos .txt"
        return 1
    fi
    
    log_info "Archivos encontrados: ${#files[@]}"
    
    # Crear corpus
    {
        echo "# $channel_name - Knowledge Corpus"
        echo
        echo "- **Generado en:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
        echo "- **Directorio:** \`$trans_dir\`"
        echo "- **Archivos incluidos:** ${#files[@]}"
        echo
        echo "---"
        echo
        echo "## Tabla de contenidos"
        echo
    } > "$corpus_file"
    
    # Primera pasada: TOC y metadatos
    local -a titles urls anchors basenames
    for f in "${files[@]}"; do
        local title="" url="" basename_f
        basename_f=$(basename "$f")
        
        title=$(grep -m1 -E '^#[[:space:]]*Título:' "$f" 2>/dev/null | sed -E 's/^#[[:space:]]*Título:[[:space:]]*//') || true
        url=$(grep -m1 -E '^#[[:space:]]*URL:' "$f" 2>/dev/null | sed -E 's/^#[[:space:]]*URL:[[:space:]]*//') || true
        
        [[ -z "$title" ]] && title=$(basename "$f" .txt)
        
        local anchor
        anchor=$(slugify "$title")
        
        titles+=("$title")
        urls+=("$url")
        anchors+=("$anchor")
        basenames+=("$basename_f")
        
        echo "- [$title](#${anchor}) — \`$basename_f\`" >> "$corpus_file"
    done
    
    echo -e "\n---\n" >> "$corpus_file"
    
    # Índice de metadatos
    {
        echo "## Índice de archivos (metadatos)"
        echo
        echo "| Archivo | Título | URL |"
        echo "|---|---|---|"
    } >> "$corpus_file"
    
    for i in "${!files[@]}"; do
        local url_display="${urls[$i]:-N/A}"
        echo "| \`${basenames[$i]}\` | ${titles[$i]} | $url_display |" >> "$corpus_file"
    done
    
    echo -e "\n---\n" >> "$corpus_file"
    
    # Contenido de cada archivo
    for i in "${!files[@]}"; do
        {
            echo "## ${titles[$i]}"
            echo
            echo "**Archivo fuente:** \`${basenames[$i]}\`  "
            echo "**URL:** ${urls[$i]:-N/A}  "
            echo "**Anchor:** \`#${anchors[$i]}\`"
            echo
            echo "<!-- ---8<--- [BEGIN FILE: ${basenames[$i]}] ---8<--- -->"
            echo
            
            tr -d '\000' < "${files[$i]}" \
                | sed -E 's/\r$//' \
                | sed 's/\t/    /g' \
                | sed 's/[[:space:]]*$//' \
                | awk '
                    BEGIN { prev_empty = 0 }
                    {
                        if (/^[[:space:]]*$/) {
                            if (!prev_empty) { print }
                            prev_empty = 1
                        } else {
                            print
                            prev_empty = 0
                        }
                    }'
            
            echo
            echo "<!-- ---8<--- [END FILE: ${basenames[$i]}] ---8<--- -->"
            echo -e "\n---\n"
        } >> "$corpus_file"
    done
    
    local corpus_size
    corpus_size=$(du -h "$corpus_file" 2>/dev/null | cut -f1)
    log_success "Corpus creado: $corpus_file ($corpus_size)"
    
    # Guardar en variable global
    LAST_CORPUS_FILE="$corpus_file"
}

# ═══════════════════════════════════════════════════════════════════════════
# PASO 5: DIVIDIR CORPUS (OPCIONAL)
# ═══════════════════════════════════════════════════════════════════════════

step5_split_corpus() {
    print_step "5" "DIVIDIR CORPUS"
    
    local corpus_file="$1"
    local split_size="$2"
    local corpus_dir
    corpus_dir=$(dirname "$corpus_file")
    local prefix="${corpus_dir}/$(basename "$corpus_file" .md)_part_"
    
    log_info "Archivo: $corpus_file"
    log_info "Tamaño máximo por parte: $split_size"
    echo ""
    
    local max_bytes
    max_bytes=$(to_bytes "$split_size")
    
    local current_part=1
    local current_file="${prefix}$(printf "%02d" "$current_part").md"
    local current_size=0
    local in_block=false
    local -a files_in_part=()
    
    # Crear portada primera parte
    {
        echo "# $(basename "$corpus_file" .md) - Parte $current_part"
        echo
        echo "- **Generado en:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
        echo "- **Tamaño máximo por parte:** $split_size"
        echo "- **Archivos incluidos:**"
    } > "$current_file"
    
    while IFS= read -r line; do
        # Detectar inicio de bloque
        if [[ "$line" == *'<!-- ---8<--- [BEGIN FILE:'* ]]; then
            local file_name
            file_name=$(echo "$line" | grep -oP '(?<=\[BEGIN FILE: ).*(?=\] ---8<--- -->)' || true)
            files_in_part+=("$file_name")
            echo "  - \`$file_name\`" >> "$current_file"
            in_block=true
        fi
        
        echo "$line" >> "$current_file"
        current_size=$(stat -c%s "$current_file" 2>/dev/null || echo 0)
        
        if [[ "$line" == *'<!-- ---8<--- [END FILE:'* ]]; then
            in_block=false
        fi
        
        if [[ $current_size -gt $max_bytes ]] && [[ ${#files_in_part[@]} -gt 0 ]] && [[ "$in_block" == false ]]; then
            echo -e "\n---\n" >> "$current_file"
            log_success "Parte $current_part: $(du -h "$current_file" | cut -f1)"
            
            ((current_part++))
            current_file="${prefix}$(printf "%02d" "$current_part").md"
            files_in_part=()
            
            {
                echo "# $(basename "$corpus_file" .md) - Parte $current_part"
                echo
                echo "- **Generado en:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
                echo "- **Tamaño máximo por parte:** $split_size"
                echo "- **Archivos incluidos:**"
            } > "$current_file"
        fi
        
    done < "$corpus_file"
    
    echo -e "\n---\n" >> "$current_file"
    log_success "Parte $current_part: $(du -h "$current_file" | cut -f1)"
    
    # Generar índice
    local index_file="${prefix}index.md"
    {
        echo "# Índice de partes del corpus"
        echo
        echo "- **Corpus original:** \`$(basename "$corpus_file")\`"
        echo "- **Tamaño máximo por parte:** $split_size"
        echo "- **Total de partes:** $current_part"
        echo "- **Generado en:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
        echo
        echo "| Número | Archivo | Tamaño |"
        echo "|---|---|---|"
        for i in $(seq 1 $current_part); do
            local file="${prefix}$(printf "%02d" "$i").md"
            if [[ -f "$file" ]]; then
                local size
                size=$(du -h "$file" | cut -f1)
                echo "| $i | \`$(basename "$file")\` | $size |"
            fi
        done
    } > "$index_file"
    
    log_success "Índice generado: $index_file"
    echo ""
    echo -e "${CYAN}Partes creadas: $current_part${NC}"
}

# ═══════════════════════════════════════════════════════════════════════════
# PASO 6: GENERAR VERSIÓN LIMPIA (PYTHON)
# ═══════════════════════════════════════════════════════════════════════════

step6_clean_version() {
    print_step "6" "GENERAR VERSIÓN LIMPIA"
    
    local corpus_file="$1"
    local max_videos="$2"
    local corpus_dir
    corpus_dir=$(dirname "$corpus_file")
    local output_dir="$corpus_dir/partes_limpias"
    
    log_info "Corpus: $corpus_file"
    log_info "Vídeos por archivo: $max_videos"
    log_info "Destino: $output_dir"
    echo ""
    
    # Crear script Python temporal
    local py_script
    py_script=$(mktemp --suffix=.py)
    
    cat > "$py_script" << 'PYEOF'
#!/usr/bin/env python3
import re
import os
import sys

INPUT_FILE = sys.argv[1]
OUTPUT_DIR = sys.argv[2]
MAX_VIDEOS = int(sys.argv[3])
CHANNEL_NAME = sys.argv[4] if len(sys.argv) > 4 else "corpus"

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Extraer transcripciones
pattern = r'## (.+?)\n\n\*\*Archivo fuente:\*\*.+?\*\*URL:\*\* (https://[^\s]+).+?<!-- ---8<--- \[BEGIN FILE:.+?\] ---8<--- -->\n\n(?:# Título:.+?\n# URL:.+?\n# Idioma:.+?\n#\n)?(.+?)(?=<!-- ---8<--- \[END FILE:)'

matches = re.findall(pattern, content, re.DOTALL)
print(f"Transcripciones encontradas: {len(matches)}")

parte_num = 1
for i in range(0, len(matches), MAX_VIDEOS):
    lote = matches[i:i+MAX_VIDEOS]
    nombre = f"{OUTPUT_DIR}/{CHANNEL_NAME}_{parte_num:02d}.txt"
    
    with open(nombre, 'w', encoding='utf-8') as f:
        for titulo, url, texto in lote:
            texto_limpio = texto.strip()
            texto_limpio = re.sub(r'\[Aplausos\]|\[Música\]|\[Music\]|\[Applause\]', '', texto_limpio)
            texto_limpio = re.sub(r'\s+', ' ', texto_limpio)
            
            f.write(f"TITULO: {titulo.strip()}\n")
            f.write(f"URL: {url}\n")
            f.write(f"CONTENIDO: {texto_limpio}\n")
            f.write("\n---\n\n")
    
    print(f"Creado: {nombre} ({len(lote)} videos)")
    parte_num += 1

print(f"\n✅ Creadas {parte_num-1} partes en '{OUTPUT_DIR}/'")
PYEOF
    
    local channel_name
    channel_name=$(basename "$corpus_file" _corpus.md)
    
    python3 "$py_script" "$corpus_file" "$output_dir" "$max_videos" "$channel_name"
    
    rm -f "$py_script"
    
    log_success "Versión limpia generada en: $output_dir"
}

# ═══════════════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════

main() {
    print_header
    
    # Verificar dependencias
    check_dependencies
    
    # Configurar cookies
    COOKIES_ARGS=""
    if [[ -n "${YT_COOKIES_FROM_BROWSER:-}" ]]; then
        COOKIES_ARGS="--cookies-from-browser ${YT_COOKIES_FROM_BROWSER}"
        log_info "Usando cookies del navegador: $YT_COOKIES_FROM_BROWSER"
    elif [[ -n "${YT_COOKIES_FILE:-}" ]]; then
        COOKIES_ARGS="--cookies ${YT_COOKIES_FILE}"
        log_info "Usando archivo de cookies: $YT_COOKIES_FILE"
    fi
    
    echo ""
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                    CONFIGURACIÓN                              ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # URL del canal
    local channel_url="${1:-}"
    if [[ -z "$channel_url" ]]; then
        channel_url=$(prompt_input "🔗 URL del canal de YouTube")
    fi
    
    if [[ -z "$channel_url" ]]; then
        log_error "URL del canal requerida"
        exit 1
    fi
    
    # Extraer nombre del canal
    local channel_name
    channel_name=$(extract_channel_name "$channel_url")
    if [[ -z "$channel_name" ]]; then
        channel_name=$(prompt_input "📛 Nombre del canal (no se pudo detectar)")
    fi
    
    echo -e "  ${GREEN}✔ Canal detectado: $channel_name${NC}"
    
    # Contar vídeos disponibles en el canal
    echo -e "  ${BLUE}ℹ Contando vídeos del canal...${NC}"
    local total_videos
    total_videos=$(yt-dlp $COOKIES_ARGS --flat-playlist --print "%(id)s" "$channel_url" 2>/dev/null | wc -l)
    echo -e "  ${GREEN}✔ Vídeos disponibles: $total_videos${NC}"
    echo ""
    
    # Directorio base
    BASE_OUTPUT_DIR=$(prompt_input "📁 Directorio base de salida" "./canales")
    
    # Límite de vídeos
    local limit
    limit=$(prompt_input "🔢 Límite de vídeos (0 = todos)" "0")
    
    # Modo resume
    local resume_mode="false"
    if confirm "🔄 ¿Activar modo resume (saltar vídeos ya procesados)?"; then
        resume_mode="true"
    fi
    
    # Crear estructura de carpetas
    local channel_dir="$BASE_OUTPUT_DIR/$channel_name"
    local trans_dir="$channel_dir/transcripciones"
    local corpus_dir="$channel_dir/corpus"
    
    mkdir -p "$channel_dir" "$trans_dir" "$corpus_dir"
    
    # Configurar log
    LOG_FILE="$channel_dir/pipeline_$(date +%Y%m%d_%H%M%S).log"
    log_info "Log guardado en: $LOG_FILE"
    
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}Configuración:${NC}"
    echo -e "  Canal:        $channel_name"
    echo -e "  URL:          $channel_url"
    echo -e "  Directorio:   $channel_dir"
    echo -e "  Límite:       ${limit:-todos}"
    echo -e "  Resume:       $resume_mode"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    if ! confirm "¿Continuar con esta configuración?" "y"; then
        log_info "Operación cancelada"
        exit 0
    fi
    
    # ─────────────────────────────────────────────────────────────────────
    # PASO 1: Obtener URLs
    # ─────────────────────────────────────────────────────────────────────
    local urls_file="$channel_dir/urls.txt"
    local video_count
    
    if [[ -f "$urls_file" ]] && confirm "📋 Ya existe urls.txt. ¿Usar existente?"; then
        video_count=$(wc -l < "$urls_file")
        log_info "Usando lista existente: $video_count vídeos"
    else
        step1_get_urls "$channel_url" "$channel_name" "$channel_dir" "$limit"
        video_count="$LAST_VIDEO_COUNT"
    fi
    
    if [[ -z "$video_count" ]] || [[ "$video_count" -eq 0 ]]; then
        log_error "No se encontraron vídeos"
        exit 1
    fi
    
    # ─────────────────────────────────────────────────────────────────────
    # PASO 2: Analizar idiomas
    # ─────────────────────────────────────────────────────────────────────
    local sub_info
    sub_info=$(step2_analyze_languages "$urls_file")
    
    # Seleccionar idioma
    echo ""
    local lang_code
    lang_code=$(prompt_input "🌐 Código de idioma (ej: es, en, es-orig)")
    
    if [[ -z "$lang_code" ]]; then
        if echo "$sub_info" | grep -q "es-orig"; then
            lang_code="es-orig"
        elif echo "$sub_info" | grep -q "en-orig"; then
            lang_code="en-orig"
        else
            lang_code="es"
        fi
        echo -e "  ${YELLOW}(Usando idioma por defecto: $lang_code)${NC}"
    fi
    
    # ─────────────────────────────────────────────────────────────────────
    # PASO 3: Descargar transcripciones
    # ─────────────────────────────────────────────────────────────────────
    step3_download_transcriptions "$urls_file" "$trans_dir" "$lang_code" "$resume_mode"
    local ok_count="$LAST_OK_COUNT"
    
    if [[ -z "$ok_count" ]] || [[ "$ok_count" -eq 0 ]]; then
        log_error "No se descargaron transcripciones"
        exit 1
    fi
    
    # ─────────────────────────────────────────────────────────────────────
    # PASO 4: Crear corpus
    # ─────────────────────────────────────────────────────────────────────
    step4_create_corpus "$trans_dir" "$corpus_dir" "$channel_name"
    local corpus_file="$LAST_CORPUS_FILE"
    
    # ─────────────────────────────────────────────────────────────────────
    # PASO 5: Dividir corpus (opcional)
    # ─────────────────────────────────────────────────────────────────────
    local corpus_size_bytes
    corpus_size_bytes=$(stat -c%s "$corpus_file" 2>/dev/null || echo 0)
    local corpus_size_mb=$((corpus_size_bytes / 1048576))
    
    echo ""
    log_info "Tamaño del corpus: ${corpus_size_mb}MB"
    
    if [[ $corpus_size_mb -gt 5 ]]; then
        echo ""
        if confirm "📦 El corpus es grande (${corpus_size_mb}MB). ¿Dividirlo en partes?"; then
            local split_size
            split_size=$(prompt_input "📏 Tamaño máximo por parte" "10M")
            step5_split_corpus "$corpus_file" "$split_size"
        fi
    fi
    
    # ─────────────────────────────────────────────────────────────────────
    # PASO 6: Generar versión limpia
    # ─────────────────────────────────────────────────────────────────────
    echo ""
    if confirm "🧹 ¿Generar versión limpia (texto plano)?"; then
        local max_videos
        max_videos=$(prompt_input "📄 Vídeos por archivo" "20")
        step6_clean_version "$corpus_file" "$max_videos"
    fi
    
    # ─────────────────────────────────────────────────────────────────────
    # RESUMEN FINAL
    # ─────────────────────────────────────────────────────────────────────
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    ¡PROCESO COMPLETADO!                       ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BOLD}Archivos generados:${NC}"
    echo -e "  📁 Directorio:      $channel_dir"
    echo -e "  📋 URLs:            $urls_file"
    echo -e "  📝 Transcripciones: $trans_dir/"
    echo -e "  📚 Corpus:          $corpus_file"
    
    if [[ -d "$corpus_dir/partes_limpias" ]]; then
        echo -e "  🧹 Partes limpias:  $corpus_dir/partes_limpias/"
    fi
    
    echo -e "  📊 Log:             $LOG_FILE"
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    
    # Mostrar estructura final
    echo ""
    echo -e "${BOLD}Estructura de archivos:${NC}"
    find "$channel_dir" -type f | head -20 | while read -r f; do
        local size
        size=$(du -h "$f" | cut -f1)
        echo "  $size  $f"
    done
    
    local total_files
    total_files=$(find "$channel_dir" -type f | wc -l)
    if [[ $total_files -gt 20 ]]; then
        echo "  ... y $((total_files - 20)) archivos más"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════════════════

main "$@"

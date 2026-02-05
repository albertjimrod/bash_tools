#!/bin/bash

# Script para mostrar paquetes instalados manualmente y sus descripciones
# Guarda este archivo como user_packages.sh y ejecuta con: chmod +x user_packages.sh && ./user_packages.sh

echo "═══════════════════════════════════════════════════════════════════════"
echo "📊 ANALIZADOR DE PAQUETES INSTALADOS MANUALMENTE"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""

# Obtener lista de paquetes instalados manualmente
echo "🔍 Obteniendo lista de paquetes instalados manualmente..."
user_packages=$(apt-mark showmanual | sort)
total_packages=$(echo "$user_packages" | wc -l)

echo "✅ Se encontraron $total_packages paquetes instalados manualmente"
echo ""
echo "💡 NOTA: Este método usa 'apt-mark showmanual' que muestra paquetes"
echo "instalados manualmente, aunque no es 100% confiable para todos los casos. [[9]]"
echo ""

# Función para obtener descripción de un paquete
get_package_description() {
    local package=$1
    # Intentar obtener descripción con apt show
    description=$(apt show "$package" 2>/dev/null | grep -A1 "^Description:" | tail -1 | sed 's/^ //')
    
    # Si falla, intentar con apt-cache
    if [ -z "$description" ] || [ "$description" == "$package" ]; then
        description=$(apt-cache show "$package" 2>/dev/null | grep "^Description-en:" | head -1 | sed 's/^Description-en: //')
    fi
    
    # Si aún no hay descripción, usar un método alternativo
    if [ -z "$description" ] || [ "$description" == "$package" ]; then
        description=$(dpkg-query -s "$package" 2>/dev/null | grep "^Description:" | sed 's/^Description: //')
    fi
    
    # Si no se encuentra descripción, mostrar mensaje genérico
    if [ -z "$description" ] || [ "$description" == "$package" ]; then
        description="Descripción no disponible"
    fi
    
    echo "$description"
}

# Mostrar información detallada
echo "📋 LISTA DETALLADA DE PAQUETES:"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""

count=0
max_packages=100  # Límite para no sobrecargar la salida

while IFS= read -r package; do
    ((count++))
    
    # Mostrar información del paquete
    echo "📦 Paquete #$count: $package"
    
    # Obtener y mostrar descripción
    desc=$(get_package_description "$package")
    echo "📝 Descripción: $desc"
    echo "─────────────────────────────────────────────────────────────────────"
    
    # Límite para no mostrar demasiados paquetes de una vez
    if [ "$count" -ge "$max_packages" ] && [ "$total_packages" -gt "$max_packages" ]; then
        remaining=$((total_packages - count))
        echo "💡 Se están mostrando los primeros $max_packages paquetes."
        echo "💡 Hay $remaining paquetes más que no se muestran por límite de visualización."
        echo "💡 Para ver todos los paquetes, edita el script y aumenta el valor de 'max_packages'."
        break
    fi
    
done <<< "$user_packages"

echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo "🔍 MÉTODOS USADOS PARA OBTENER INFORMACIÓN:"
echo ""
echo "• Para listar paquetes instalados manualmente: apt-mark showmanual [[9]]"
echo "• Para obtener descripciones detalladas: apt show y apt-cache show [[19]]"
echo "• Método alternativo: dpkg-query para información de paquetes [[17]]"
echo ""
echo "💡 TIP: Puedes obtener más detalles de cualquier paquete con:"
echo "   apt show nombre_del_paquete"
echo "   o"
echo "   apt-cache show nombre_del_paquete [[21]]"
echo "═══════════════════════════════════════════════════════════════════════"

# Opción para exportar a archivo
echo ""
read -p "¿Quieres exportar la lista completa a un archivo? (s/n): " export_choice
if [[ "$export_choice" =~ [sS] ]]; then
    export_file="paquetes_usuario_$(date +%Y%m%d_%H%M%S).txt"
    echo "Exportando lista completa a $export_file..."
    
    echo "LISTA COMPLETA DE PAQUETES INSTALADOS MANUALMENTE" > "$export_file"
    echo "Generado: $(date)" >> "$export_file"
    echo "Total: $total_packages paquetes" >> "$export_file"
    echo "" >> "$export_file"
    echo "PAQUETES:" >> "$export_file"
    echo "==========" >> "$export_file"
    
    count=0
    while IFS= read -r package; do
        ((count++))
        desc=$(get_package_description "$package")
        echo "$count. $package - $desc" >> "$export_file"
    done <<< "$user_packages"
    
    echo "" >> "$export_file"
    echo "Fin del reporte" >> "$export_file"
    echo "✅ Archivo exportado: $export_file"
fi

echo ""
echo "🎉 ¡Análisis completado!"
echo "Total de paquetes instalados manualmente: $total_packages"

#!/bin/bash

> direcciones_unicas.txt

for archivo in *.eml; do
    grep -i "^From:\|^To:\|^Cc:\|^Bcc:" "$archivo" | sed 's/.*<\(.*\)>/\1/' | sed 's/.*: \(.*\)/\1/' | tr ',' '\n'
done | grep '@' | sed 's/^ *//' | sed 's/ *$//' | sort -u >> direcciones_unicas.txt

echo "Direcciones extraídas en: direcciones_unicas.txt"

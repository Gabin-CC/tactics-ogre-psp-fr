#!/bin/bash
# Reconstruit l'ISO française à partir de l'ISO originale et de traduction/final.json.
# Usage : ./reconstruire.sh "chemin/ISO originale.iso" "chemin/ISO sortie.iso"
set -e
IN="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
OUT="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"
cd "$(dirname "$0")"
TMP=$(mktemp -d)
python3 -I outils/extract_usrdir.py "$IN" "$TMP/USRDIR"
python3 -I outils/apply.py "$TMP/USRDIR" traduction/final.json "$IN" "$OUT"
rm -rf "$TMP"
echo "ISO créée : $OUT"

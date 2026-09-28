#!/bin/bash
# ==============================================================================
# Hermes Synaptic Knowledge Hub - Collaborator Setup Script
# Run this on your teammate's machine to connect to the shared Knowledge Hub!
# ==============================================================================

set -e

REPO_URL="${1:-}"

echo "🧠 ========================================================"
echo "   Hermes Synaptic Knowledge Hub - Collaborator Setup"
echo "========================================================"

if [ -z "$REPO_URL" ]; then
  echo "👉 Uso: ./setup_collaborator.sh <URL_DEL_REPOSITORIO_GITHUB>"
  echo "   Ejemplo: ./setup_collaborator.sh git@github.com:rodrigonavarroa0-blip/hermes-hub.git"
  exit 1
fi

HUB_PATH="$HOME/.hermes-hub"

if [ -d "$HUB_PATH" ]; then
  echo "📁 Directorio existente encontrado en $HUB_PATH."
  echo "🔄 Actualizando repositorio..."
  cd "$HUB_PATH"
  git remote set-url origin "$REPO_URL" 2>/dev/null || git remote add origin "$REPO_URL"
  git fetch origin
  git checkout main
  git pull --rebase origin main
else
  echo "📦 Clonando base de conocimiento compartida en $HUB_PATH..."
  git clone "$REPO_URL" "$HUB_PATH"
  cd "$HUB_PATH"
fi

# Setup Virtual Environment if missing
if [ ! -d "$HUB_PATH/.venv" ]; then
  echo "🐍 Creando entorno virtual Python..."
  python3 -m venv "$HUB_PATH/.venv"
fi

echo "📦 Instalando dependencias necesarias..."
"$HUB_PATH/.venv/bin/pip" install --quiet --upgrade pip
"$HUB_PATH/.venv/bin/pip" install --quiet "fastmcp>=0.1.0" "pydantic>=2.0.0" "uvicorn" "starlette" "pyyaml" "numpy"

echo "⚡ Reconstruyendo base de datos vectorial..."
"$HUB_PATH/.venv/bin/python" "$HUB_PATH/config/ingest_skills.py"

echo ""
echo "✅ ¡Configuración completada con éxito!"
echo "--------------------------------------------------------"
echo "🚀 Ahora ambos comparten exactamente el mismo cerebro."
echo "👉 Para sincronizar manualmente en cualquier momento:"
echo "   $HUB_PATH/bin/hermes sync"
echo "--------------------------------------------------------"

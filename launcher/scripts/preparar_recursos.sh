#!/usr/bin/env bash
# Copia /api (sin .venv/storage/etc., ver api/.dockerignore) y los `dist/` ya
# compilados de panel/web-publica a un directorio de staging que
# tauri.conf.json empaqueta como recursos (`stack/api`, `stack/panel/dist`,
# `stack/web-publica/dist`). Se invoca automáticamente como
# `beforeBuildCommand` de `tauri build`.
set -euo pipefail
cd "$(dirname "$0")/.."

(cd .. && npm run build --workspace panel --workspace web-publica)

rm -rf resources-build
mkdir -p resources-build/panel resources-build/web-publica
rsync -a --exclude-from=../api/.dockerignore ../api/ resources-build/api/
cp -r ../panel/dist resources-build/panel/dist
cp -r ../web-publica/dist resources-build/web-publica/dist

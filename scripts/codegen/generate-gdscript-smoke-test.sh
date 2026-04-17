#!/usr/bin/env bash
# generate-gdscript-smoke-test.sh
#
# Generates GDScript client bindings for the smoke_test SpacetimeDB module by
# reusing the pinned C# codegen front-end first and then emitting repo-owned
# GDScript artifacts under tests/fixtures/gdscript_generated/smoke_test/.
# The delegated C# frontend still runs the authoritative `spacetime generate`
# `--lang csharp` path before the GDScript emitter executes.
#
# Usage (run from repo root):
#   bash scripts/codegen/generate-gdscript-smoke-test.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
C_SHARP_FRONTEND_DIR="${REPO_ROOT}/demo/generated/smoke_test"
OUTPUT_DIR="${REPO_ROOT}/tests/fixtures/gdscript_generated/smoke_test"

echo "Refreshing authoritative C# bindings via the existing frontend..."
bash "${REPO_ROOT}/scripts/codegen/generate-smoke-test.sh"

echo "Generating GDScript bindings into: ${OUTPUT_DIR}"
python3 "${REPO_ROOT}/scripts/codegen/generate-gdscript-bindings.py" \
  --csharp-bindings-dir "${C_SHARP_FRONTEND_DIR}" \
  --out-dir "${OUTPUT_DIR}" \
  --module-name "smoke_test" \
  --regen-command "bash scripts/codegen/generate-gdscript-smoke-test.sh"

echo "Generated GDScript bindings written to: ${OUTPUT_DIR}"
find "${OUTPUT_DIR}" -maxdepth 2 -type f | sort

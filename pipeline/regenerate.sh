#!/usr/bin/env bash
#
# regenerate.sh — regenera toda a app a partir das amostras em data/raw/samples/.
#
# Corre a cadeia completa do pipeline e trata do passo fácil de esquecer
# (consolidar a community_matrix onde o prepare a lê).
#
# Uso:
#   pipeline/regenerate.sh             cadeia completa (inclui anotação de traços)
#   pipeline/regenerate.sh --no-batch  salta a anotação de traços (lenta) e reusa
#                                       a community_matrix existente — útil quando
#                                       só mudaram CSV de docs/ ou código a jusante.
#
# A identidade das amostras é tratada pelo registo (data/sample_registry.tsv):
# largar ficheiros em data/raw/samples/ e correr este script é tudo o que é preciso.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PY="${PYTHON:-python3}"
GENUS="data/raw/ncbi_genus_summary.jsonl"
SAMPLES="data/raw/samples"
PERSAMPLE="data/derived/per_sample"
COMMUNITY="data/derived/community_matrix.tsv"

run_batch=1
case "${1:-}" in
  --no-batch) run_batch=0 ;;
  "" ) ;;
  * ) echo "Opção desconhecida: $1 (usa --no-batch ou nada)"; exit 2 ;;
esac

echo "==> Regenerar app  (root: $ROOT)"

if [[ $run_batch -eq 1 ]]; then
  echo "==> [1/5] Anotação de traços + community_matrix (batch_pipeline)…"
  "$PY" pipeline/batch_pipeline.py \
      --reports "$SAMPLES" \
      --genus   "$GENUS" \
      --out-dir "$PERSAMPLE"
  echo "==> [2/5] Consolidar community_matrix em data/derived/…"
  cp "$PERSAMPLE/community_matrix.tsv" "$COMMUNITY"
else
  echo "==> [1-2/5] (--no-batch) a reusar community_matrix existente"
  [[ -f "$COMMUNITY" ]] || { echo "ERRO: $COMMUNITY não existe; corre sem --no-batch."; exit 1; }
fi

echo "==> [3/5] Matriz de composição…"
"$PY" pipeline/build_composition_matrix.py

echo "==> [4/5] Diversidade beta (Bray-Curtis + PCoA + modelo de projeção)…"
"$PY" pipeline/build_beta_diversity.py

echo "==> [5/5] Dados estáticos da plataforma (app/data/*.json)…"
"$PY" pipeline/prepare_platform_data.py

n=$(($(wc -l < data/sample_registry.tsv) - 1))
echo
echo "==> Concluído. $n amostras no registo (data/sample_registry.tsv)."
echo "    Servir a app:  cd app && $PY -m http.server 8000   →  http://localhost:8000"

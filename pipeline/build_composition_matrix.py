#!/usr/bin/env python3
"""
build_composition_matrix.py — gera a matriz de composição género × amostra.

File-driven: processa TODAS as amostras presentes em data/raw/samples/.
Para adicionar/remover amostras basta adicionar/remover ficheiros lá — não é
preciso editar este script.

Para cada *.report_bracken.txt:
  - Corre o parser bracken_to_profile (parse_bracken_report)
  - Colapsa a género (lógica já no parser)
  - Renormaliza a coluna para somar 1.0

Output: data/derived/composition_matrix.tsv
  Linhas = géneros (taxon_name), colunas = amostras (prefixo numérico do ficheiro).
  Géneros ausentes numa amostra → 0.0.
"""

import sys
import os
import re
from pathlib import Path

# Reutiliza o parser existente
sys.path.insert(0, str(Path(__file__).parent))
from bracken_to_profile import parse_bracken_report

ROOT        = Path(__file__).resolve().parent.parent
SAMPLES_DIR = ROOT / "data" / "raw" / "samples"
OUTPUT_FILE = ROOT / "data" / "derived" / "composition_matrix.tsv"


def sample_id(filename):
    """Prefixo numérico do nome do ficheiro (ex: '1', '23'); fallback ao nome."""
    m = re.match(r'^(\d+)_', filename)
    return m.group(1) if m else filename.split('.')[0]


def sort_key(p):
    """Ordena prefixos numéricos por valor; nomes não-numéricos a seguir, por ordem."""
    sid = sample_id(p.name)
    return (0, int(sid)) if sid.isdigit() else (1, sid)


def main():
    files = sorted(SAMPLES_DIR.glob("*.report_bracken.txt"), key=sort_key)

    if not files:
        sys.exit(f"Erro: nenhuma amostra encontrada em {SAMPLES_DIR}.")

    print(f"A processar {len(files)} amostras...", file=sys.stderr)

    # Primeira passagem: recolher todos os géneros e abundâncias por amostra
    # data[sample_id] = {genus_name: relative_abundance, ...}
    data = {}
    all_genera = set()

    for f in files:
        sid = sample_id(f.name)
        total_reads, genera = parse_bracken_report(str(f))

        # Construir dict genus_name → reads; colapsar duplicados de nome (improvável mas seguro)
        genus_reads = {}
        for g in genera:
            name = g['name']
            genus_reads[name] = genus_reads.get(name, 0) + g['reads']

        # Renormalizar pela soma dos reads atribuídos a género
        total_genus_reads = sum(genus_reads.values())
        if total_genus_reads == 0:
            sys.exit(f"Erro: amostra {sid} sem reads de género.")

        sample_ab = {name: reads / total_genus_reads for name, reads in genus_reads.items()}
        data[sid] = sample_ab
        all_genera.update(sample_ab.keys())

        col_sum = sum(sample_ab.values())
        print(f"  {sid:>3}: {len(sample_ab)} géneros, soma={col_sum:.6f}", file=sys.stderr)

    # Ordenar géneros (alfabético) e amostras (numérico)
    genera_sorted = sorted(all_genera)
    samples_sorted = sorted(data.keys(), key=int)

    print(f"\nTotal géneros únicos: {len(genera_sorted)}", file=sys.stderr)

    # Escrever matriz
    with open(OUTPUT_FILE, 'w') as fh:
        header = "genus\t" + "\t".join(samples_sorted)
        fh.write(header + "\n")
        for genus in genera_sorted:
            row = [genus] + [f"{data[sid].get(genus, 0.0):.8f}" for sid in samples_sorted]
            fh.write("\t".join(row) + "\n")

    print(f"\nMatriz escrita: {OUTPUT_FILE}", file=sys.stderr)
    print(f"Dimensões: {len(genera_sorted)} géneros × {len(samples_sorted)} amostras", file=sys.stderr)


if __name__ == "__main__":
    main()

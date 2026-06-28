#!/usr/bin/env python3
"""
sample_registry.py — registo persistente accession → número de amostra.

A identidade de uma amostra é a sua **accession** (ENA/SRA: ERR/SRR/DRR), única e
intrínseca ao ficheiro — NÃO o prefixo numérico do nome (que pode colidir entre
cohorts e exige coordenação manual). Cada accession recebe um número estável,
gravado em `data/sample_registry.tsv`.

Mecanismo (file-driven, à prova de esquecimento): largar novos ficheiros em
`data/raw/samples/` e correr o pipeline atribui automaticamente o próximo número
às accessions novas; as accessions já registadas mantêm o seu número para sempre.

Consultar a correspondência número ↔ amostra: abrir `data/sample_registry.tsv`
(colunas: number, accession, filename).
"""

import re
from pathlib import Path

ROOT          = Path(__file__).resolve().parent.parent
SAMPLES_DIR   = ROOT / "data" / "raw" / "samples"
REGISTRY_PATH = ROOT / "data" / "sample_registry.tsv"

ACCESSION_RE = re.compile(r'([EDS]RR\d+)')      # ENA/SRA run accessions
# Sufixos que o pipeline acrescenta ao nome da amostra. Removidos no fallback para
# que a MESMA amostra dê a mesma identidade quer venha do relatório, da coluna da
# community_matrix, ou de um ficheiro per_sample.
_STEM_RE = re.compile(
    r'(\.report_bracken.*'
    r'|_taxon_trait_annotations\.tsv'
    r'|_community_trait_annotations\.tsv'
    r'|_profile\.tsv)$'
)
_LEADING_NUM = re.compile(r'^(\d+)_')


def accession_of(name):
    """Accession (ERR/SRR/DRR) do nome de ficheiro/coluna.
    Fallback (sem accession): nome sem os sufixos do pipeline — também único,
    por imposição do sistema de ficheiros."""
    m = ACCESSION_RE.search(name)
    return m.group(1) if m else _STEM_RE.sub('', name)


def _leading_number(name):
    m = _LEADING_NUM.match(name)
    return int(m.group(1)) if m else None


def _read_rows():
    """Lê o registo como lista de (number:int, accession, filename)."""
    rows = []
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH) as f:
            next(f, None)  # header
            for line in f:
                p = line.rstrip('\n').split('\t')
                if len(p) >= 2 and p[0].isdigit():
                    rows.append((int(p[0]), p[1], p[2] if len(p) >= 3 else ''))
    return rows


def load_registry():
    """dict accession -> número (int). {} se o registo não existir."""
    return {acc: num for num, acc, _ in _read_rows()}


def _write(rows):
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_PATH, 'w') as f:
        f.write("number\taccession\tfilename\n")
        for num, acc, fn in sorted(rows, key=lambda r: r[0]):
            f.write(f"{num}\t{acc}\t{fn}\n")


def ensure_registry(samples_dir=SAMPLES_DIR):
    """Garante número para cada amostra em samples_dir; persiste; devolve dict
    accession -> número.

    - Accessions já registadas mantêm o número.
    - Na **primeira criação** do registo, cada accession herda o prefixo numérico
      do nome (se livre) — preserva a numeração atual da plataforma.
    - Depois disso, accessions novas recebem sempre o próximo número livre (máx+1),
      em bloco contíguo e previsível.
    """
    rows = _read_rows()
    reg = {acc: num for num, acc, _ in rows}
    filenames = {acc: fn for _, acc, fn in rows}
    used = set(reg.values())
    first_time = not rows

    def next_free():
        n = max(used, default=0) + 1
        while n in used:
            n += 1
        return n

    files = sorted(Path(samples_dir).glob("*.report_bracken.txt"),
                   key=lambda p: (_leading_number(p.name) or 1_000_000, p.name))
    changed = not REGISTRY_PATH.exists()
    for p in files:
        acc = accession_of(p.name)
        filenames.setdefault(acc, p.name)
        if acc in reg:
            continue
        desired = _leading_number(p.name)
        num = desired if (first_time and desired is not None and desired not in used) else next_free()
        reg[acc] = num
        used.add(num)
        changed = True

    if changed:
        _write([(num, acc, filenames.get(acc, '')) for acc, num in reg.items()])
    return reg


def number_of(name, registry):
    """Número (str) da amostra, dado o nome de ficheiro/coluna e o registo."""
    acc = accession_of(name)
    num = registry.get(acc)
    if num is None:
        raise KeyError(f"amostra sem número no registo: {name} (accession {acc}). "
                       f"Corre ensure_registry() primeiro.")
    return str(num)


if __name__ == "__main__":
    import sys
    reg = ensure_registry()
    print(f"Registo: {len(reg)} amostras → {REGISTRY_PATH}", file=sys.stderr)

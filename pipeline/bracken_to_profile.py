#!/usr/bin/env python3
"""
bracken_to_profile.py — converte um relatório Bracken (*.report_bracken.txt)
para o formato normalizado de 4 colunas que sumtraits_local.py aceita.

Output TSV (com header):
  taxon_id  taxon_name  taxon_lineage  relative_abundance

Colapsa ao nível de género: reads_taxon de todas as espécies (S) são somadas
ao género pai canónico (G). Ranks não canónicos (R, R1, R2, K, G1, G2, O1…)
são ignorados na linhagem mas mantidos na stack para rastrear a hierarquia.
"""

import argparse
import sys

# Ranks canónicos reconhecidos; todos os outros são intermediários ignorados.
CANONICAL = {'D', 'P', 'C', 'O', 'F', 'G', 'S'}
# Ordem dos 6 níveis acima de espécie usados na linhagem de output.
LINEAGE_ORDER = ('D', 'P', 'C', 'O', 'F', 'G')


def parse_bracken_report(path):
    """
    Lê o relatório e devolve (total_reads, genera).
    genera: lista de dicts {taxid, name, lineage, reads}.
    """
    genera = {}   # taxid -> dict
    # stack de (depth, rank_code, taxid, name_stripped)
    stack = []
    total_reads = None

    with open(path) as fh:
        for lineno, raw in enumerate(fh, 1):
            raw = raw.rstrip('\n')
            if not raw.strip():
                continue
            parts = raw.split('\t')
            if len(parts) < 6:
                continue

            _, reads_clade_str, reads_taxon_str, rank_code, taxid_str, name_field = (
                parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
            )
            try:
                reads_clade = int(reads_clade_str)
                reads_taxon = int(reads_taxon_str)
                taxid       = int(taxid_str)
            except ValueError:
                sys.stderr.write(f"[warn] linha {lineno} ignorada (parse error)\n")
                continue

            name_stripped = name_field.lstrip()
            # 2 espaços por nível de indentação
            depth = (len(name_field) - len(name_stripped)) // 2

            # Total reads = reads_clade da primeira linha (raiz da árvore)
            if total_reads is None:
                total_reads = reads_clade

            # Descartar da stack entradas com depth >= actual (já não são ancestrais)
            while stack and stack[-1][0] >= depth:
                stack.pop()

            stack.append((depth, rank_code, taxid, name_stripped))

            if rank_code == 'G':
                # Filtrar ancestrais canónicos D/P/C/O/F (excluindo o próprio G)
                ancestors = {
                    rc: nm
                    for (_, rc, _, nm) in stack[:-1]
                    if rc in ('D', 'P', 'C', 'O', 'F')
                }
                slots = [ancestors.get(r, '') for r in LINEAGE_ORDER]
                slots[-1] = name_stripped          # slot G
                lineage = '|'.join(slots) + '|'   # trailing | → slot S vazio

                genera[taxid] = {
                    'taxid':   taxid,
                    'name':    name_stripped,
                    'lineage': lineage,
                    'reads':   reads_taxon,        # 0 após redistribuição Bracken
                }

            elif rank_code == 'S':
                # Encontrar o G canónico mais próximo na stack (excluindo S actual)
                for _, rc, tid, _ in reversed(stack[:-1]):
                    if rc == 'G':
                        if tid in genera:
                            genera[tid]['reads'] += reads_taxon
                        break

    if not total_reads:
        sys.exit("Erro: total de reads não determinado (ficheiro vazio ou inválido).")

    return total_reads, list(genera.values())


def write_profile(total_reads, genera, out_path):
    genera_with_reads = sorted(
        (g for g in genera if g['reads'] > 0),
        key=lambda g: g['reads'], reverse=True,
    )
    fh = open(out_path, 'w') if out_path != '-' else sys.stdout
    try:
        fh.write('taxon_id\ttaxon_name\ttaxon_lineage\trelative_abundance\n')
        total_ab = 0.0
        for g in genera_with_reads:
            rel_ab = g['reads'] / total_reads
            total_ab += rel_ab
            fh.write(f"{g['taxid']}\t{g['name']}\t{g['lineage']}\t{rel_ab:.8f}\n")
    finally:
        if fh is not sys.stdout:
            fh.close()
    return len(genera_with_reads), total_ab


def main():
    ap = argparse.ArgumentParser(
        description="Converte Bracken report para perfil normalizado de 4 colunas."
    )
    ap.add_argument('report', help="*.report_bracken.txt")
    ap.add_argument('-o', '--output', default='-',
                    help="Ficheiro de output TSV (default: stdout)")
    args = ap.parse_args()

    total_reads, genera = parse_bracken_report(args.report)
    n, total_ab = write_profile(total_reads, genera, args.output)

    sys.stderr.write(
        f"[ok] total reads (raiz): {total_reads}\n"
        f"[ok] géneros com reads: {n}\n"
        f"[ok] abundância relativa total: {total_ab:.6f}\n"
    )


if __name__ == '__main__':
    main()

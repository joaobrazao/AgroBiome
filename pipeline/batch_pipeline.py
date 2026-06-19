#!/usr/bin/env python3
"""
batch_pipeline.py — modo batch do pipeline metaTraits.

Para cada relatório Bracken encontrado em --reports (glob: *.report_bracken*):
  1. Converte para perfil normalizado de 4 colunas  (bracken_to_profile)
  2. Anota traços e agrega à comunidade              (sumtraits_local)

Outputs por amostra em --out-dir:
  <sample>_profile.tsv
  <sample>_taxon_trait_annotations.tsv
  <sample>_community_trait_annotations.tsv

Com --matrix (default): também escreve community_matrix.tsv
  linhas = amostras | colunas = features da anotação comunitária
"""

import argparse
import csv
import sys
from pathlib import Path

# Permite executar a partir de qualquer directório.
sys.path.insert(0, str(Path(__file__).parent))
from bracken_to_profile import parse_bracken_report, write_profile
from sumtraits_local import load_summary, parse_profile, write_taxon_table, write_community_table


# --------------------------------------------------------------------------- #
# Extracção do nome de amostra a partir do nome de ficheiro
# --------------------------------------------------------------------------- #
def sample_name_from(path: Path) -> str:
    """
    Remove sufixos do tipo .report_bracken* para obter um prefixo limpo.
    Exemplos:
      ERR123_db3.bracken.kraken2.report_bracken.txt → ERR123_db3
      test.report_bracken.txt.txt                   → test
    """
    name = path.name
    idx = name.find(".report_bracken")
    return name[:idx] if idx > 0 else path.stem


# --------------------------------------------------------------------------- #
# Processamento de uma amostra
# --------------------------------------------------------------------------- #
def process_sample(report_path: Path, genus_db: dict, out_dir: Path) -> tuple[str, dict]:
    """
    Corre o pipeline completo para uma amostra.
    Devolve (sample_name, {feature: relative_abundance}).
    """
    sample = sample_name_from(report_path)

    # ---- passo 1: Bracken → perfil normalizado ----
    total_reads, genera = parse_bracken_report(str(report_path))
    if not genera:
        # Amostra degenerada (sem qualquer atribuição a género). Levantar erro
        # normal — apanhado pelo loop principal e registado, em vez de abortar
        # todo o batch (sumtraits faria sys.exit por soma de abundância = 0).
        raise ValueError("amostra sem géneros (degenerada)")
    profile_path = out_dir / f"{sample}_profile.tsv"
    write_profile(total_reads, genera, str(profile_path))

    # ---- passo 2: perfil → anotação de traços ----
    taxa = parse_profile(str(profile_path))
    dbs  = [("genus", genus_db)]

    write_taxon_table(
        taxa, dbs,
        str(out_dir / f"{sample}_taxon_trait_annotations.tsv"),
    )
    community_path = out_dir / f"{sample}_community_trait_annotations.tsv"
    total_ab, unclass_ab, n_traits = write_community_table(taxa, dbs, str(community_path))

    sys.stderr.write(
        f"  [ok] {sample}: {len(genera)} géneros | "
        f"traços: {n_traits} | ab total: {total_ab:.4f} | "
        f"não-classif.: {unclass_ab:.4f}\n"
    )

    # Ler features para a matriz consolidada
    features: dict[str, float] = {}
    with open(community_path) as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            features[row["feature"]] = float(row["relative_abundance"])

    return sample, features


# --------------------------------------------------------------------------- #
# Matriz consolidada amostras × features
# --------------------------------------------------------------------------- #
def write_matrix(sample_features: dict[str, dict], out_path: Path) -> None:
    """
    Escreve TSV: linhas = amostras, colunas = features (união de todas as amostras).
    Valores ausentes ficam a 0.0.
    """
    all_features = sorted({f for feats in sample_features.values() for f in feats})
    with open(out_path, "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["sample"] + all_features)
        for sample, feats in sample_features.items():
            w.writerow([sample] + [feats.get(f, 0.0) for f in all_features])
    sys.stderr.write(
        f"[matrix] {len(sample_features)} amostras × {len(all_features)} features "
        f"→ {out_path}\n"
    )


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="Batch pipeline metaTraits (Bracken → traços).")
    ap.add_argument("--reports", required=True,
                    help="Directório com relatórios Bracken (*.report_bracken*)")
    ap.add_argument("--genus", required=True,
                    help="ncbi_genus_summary.jsonl")
    ap.add_argument("--out-dir", required=True,
                    help="Directório de output (criado se não existir)")
    ap.add_argument("--pattern", default="*.report_bracken*",
                    help="Glob para encontrar relatórios (default: %(default)s)")
    ap.add_argument("--no-matrix", dest="matrix", action="store_false",
                    help="Não escrever a matriz consolidada amostras × features")
    ap.set_defaults(matrix=True)
    args = ap.parse_args()

    reports_dir = Path(args.reports)
    out_dir     = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    report_files = sorted(reports_dir.glob(args.pattern))
    if not report_files:
        sys.exit(f"Nenhum ficheiro encontrado em {reports_dir} com padrão '{args.pattern}'.")

    sys.stderr.write(f"[batch] {len(report_files)} amostra(s) encontrada(s)\n")
    sys.stderr.write(f"[batch] a carregar BD de traços…\n")
    genus_db = load_summary(args.genus)
    sys.stderr.write(f"[batch] {len(genus_db)} géneros na BD\n\n")

    sample_features: dict[str, dict] = {}
    errors = []

    for rp in report_files:
        try:
            sample, feats = process_sample(rp, genus_db, out_dir)
            sample_features[sample] = feats
        except Exception as exc:
            sys.stderr.write(f"  [ERRO] {rp.name}: {exc}\n")
            errors.append(rp.name)

    sys.stderr.write(
        f"\n[batch] concluído: {len(sample_features)} amostras OK"
        + (f", {len(errors)} com erro: {errors}" if errors else "")
        + "\n"
    )

    if args.matrix and sample_features:
        write_matrix(sample_features, out_dir / "community_matrix.tsv")


if __name__ == "__main__":
    main()

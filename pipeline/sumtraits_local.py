#!/usr/bin/env python3
"""
sumtraits_local.py — reprodução offline do workflow sumTraits (metaTraits/EMBL).

Enriquece um perfil taxonómico com os traços harmonizados da metaTraits
(descarregados em JSONL) e produz dois outputs no formato do site:

  1. <prefix>_taxon_trait_annotations.tsv   — traços por taxon
  2. <prefix>_community_trait_annotations.tsv — agregação ao nível da comunidade

A anotação de cada taxon é resolvida pela linhagem, do nível mais específico
para o menos específico, entre os ficheiros de summary fornecidos
(--species, --genus, --family). Para perfis 16S, o nível de género é o
adequado e normalmente o único necessário.

NOTA: a coluna 'source_databases' do output por-taxon não consta dos ficheiros
de summary da metaTraits (só 'unique_databases'); fica vazia.
"""

import argparse
import json
import re
import sys
from collections import defaultdict


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #
def slug(text):
    """Normaliza um rótulo para o estilo de 'feature' do site."""
    return re.sub(r"[^a-z0-9]+", "_", str(text).lower()).strip("_")


def parse_majority(majority_label, is_discrete):
    """
    Devolve (estado, percentagem) para discretos, ou (mediana_float, None)
    para numéricos. 'No robust majority' -> (None, None).
    """
    if majority_label == "No robust majority":
        return None, None
    if not is_discrete:
        # "Median: 53.75 %" / "Median: 3606331.0 bp" / "Median: 22.2 Celsius"
        m = re.search(r"Median:\s*(-?[\d.]+)", majority_label)
        return (float(m.group(1)) if m else None), None
    # discreto: "false: (100%)" / "level 1: (80%)" / "rod-shaped: (100%)"
    m = re.match(r"(.+?):\s*\((\d+(?:\.\d+)?)%\)", majority_label)
    if m:
        return m.group(1), float(m.group(2))
    return None, None


def value_type_of(summary):
    """boolean | factor | numeric, a partir do registo de summary."""
    if not summary["is_discrete"]:
        return "numeric"
    keys = {k.lower() for k in summary.get("percentages", {})}
    if keys and keys <= {"true", "false"}:
        return "boolean"
    return "factor"


# --------------------------------------------------------------------------- #
# Carregamento da BD de traços (JSONL keyed por tax_name)
# --------------------------------------------------------------------------- #
def load_summary(path):
    """tax_name -> {trait_name -> summary_dict}"""
    db = {}
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            db[rec["tax_name"]] = {s["name"]: s for s in rec["summaries"]}
    return db


# --------------------------------------------------------------------------- #
# Parsing do perfil (formato normalizado de 4 colunas)
# --------------------------------------------------------------------------- #
def parse_profile(path):
    """
    Lê TSV: taxon_id, taxon_name, taxon_lineage, relative_abundance.
    Devolve lista de dicts com ranks extraídos da linhagem.
    Linhagem: Domain|Phylum|Class|Order|Family|Genus|Species|
    """
    RANKS = ["domain", "phylum", "class", "order", "family", "genus", "species"]
    taxa = []
    with open(path) as fh:
        header = fh.readline().rstrip("\n").split("\t")
        idx = {name: i for i, name in enumerate(header)}
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < len(header):
                parts += [""] * (len(header) - len(parts))
            lineage = parts[idx["taxon_lineage"]]
            fields = lineage.split("|") if lineage else []
            ranks = {}
            for i, r in enumerate(RANKS):
                ranks[r] = fields[i].strip() if i < len(fields) and fields[i].strip() else None
            taxa.append({
                "taxon_id": parts[idx["taxon_id"]],
                "taxon_name": parts[idx["taxon_name"]],
                "taxon_lineage": lineage,
                "rel_abundance": float(parts[idx["relative_abundance"]] or 0.0),
                "ranks": ranks,
            })
    return taxa


# --------------------------------------------------------------------------- #
# Resolução de anotação por linhagem
# --------------------------------------------------------------------------- #
def resolve_annotation(taxon, dbs):
    """
    dbs: lista de (rank, db) do mais específico para o menos.
    Devolve (annotation_dict, rank_usado, nome_usado) ou (None, None, None).
    """
    for rank, db in dbs:
        name = taxon["ranks"].get(rank)
        if name and name in db:
            return db[name], rank, name
    return None, None, None


# --------------------------------------------------------------------------- #
# Output 1: traços por taxon
# --------------------------------------------------------------------------- #
def write_taxon_table(taxa, dbs, out_path):
    cols = ["taxon_id", "taxon_name", "taxon_lineage", "trait", "value_type",
            "consensus_value", "consensus_bool", "consensus_numeric_value",
            "support_count", "support_percentage", "total_evidence",
            "source_databases", "databases", "status"]
    n_rows = 0
    with open(out_path, "w") as out:
        out.write("\t".join(cols) + "\n")
        for t in taxa:
            ann, _, _ = resolve_annotation(t, dbs)
            if not ann:
                continue
            for trait, s in sorted(ann.items()):
                vt = value_type_of(s)
                state, pct = parse_majority(s["majority_label"], s["is_discrete"])
                if s["majority_label"] == "No robust majority":
                    status = "no_robust_majority"
                    cons_val, cons_bool, cons_num, supp_pct = "", "", "", ""
                else:
                    status = "consensus"
                    if vt == "numeric":
                        cons_val = state
                        cons_bool, cons_num, supp_pct = "", state, ""
                    elif vt == "boolean":
                        cons_val = str(state).lower()
                        cons_bool = "True" if str(state).lower() == "true" else "False"
                        cons_num, supp_pct = "", pct
                    else:  # factor
                        cons_val = state
                        cons_bool, cons_num, supp_pct = "", "", ""
                row = [
                    t["taxon_id"], t["taxon_name"], t["taxon_lineage"],
                    trait, vt, cons_val, cons_bool, cons_num,
                    s.get("num_observations", ""), supp_pct,
                    s.get("num_observations", ""),
                    "",  # source_databases: indisponível no summary
                    s.get("unique_databases", ""), status,
                ]
                out.write("\t".join("" if v is None else str(v) for v in row) + "\n")
                n_rows += 1
    return n_rows


# --------------------------------------------------------------------------- #
# Output 2: agregação ao nível da comunidade
# --------------------------------------------------------------------------- #
def write_community_table(taxa, dbs, out_path):
    total = sum(t["rel_abundance"] for t in taxa)
    if total <= 0:
        sys.exit("Soma de abundâncias relativas é zero.")

    # Classifica cada taxon: anotado (com género/nível na BD) ou não-classificado.
    classified = []          # (abundância, annotation_dict)
    unclassified_ab = 0.0
    for t in taxa:
        ann, _, _ = resolve_annotation(t, dbs)
        if ann:
            classified.append((t["rel_abundance"], ann))
        else:
            unclassified_ab += t["rel_abundance"]

    # Universo de traços = todos os que aparecem em qualquer anotação presente.
    traits = {}
    for _, ann in classified:
        for name, s in ann.items():
            traits.setdefault(name, value_type_of(s))

    rows = []  # (trait, summary_type, feature, relative_abundance)
    for trait in sorted(traits):
        vt = traits[trait]
        tslug = slug(trait)
        annotated_ab = 0.0

        if vt == "numeric":
            wsum = 0.0
            for ab, ann in classified:
                s = ann.get(trait)
                if not s:
                    continue
                med, _ = parse_majority(s["majority_label"], False)
                if med is not None:
                    wsum += ab * med
                    annotated_ab += ab
            mean = (wsum / annotated_ab) if annotated_ab > 0 else 0.0
            unannot = total - unclassified_ab - annotated_ab
            rows.append((trait, "numeric_mean", f"{tslug}.mean", mean))
            rows.append((trait, "unannotated", f"{tslug}.unannotated", unannot))
            rows.append((trait, "unclassified", f"{tslug}.unclassified", unclassified_ab))

        elif vt == "boolean":
            ab_true = ab_false = ab_nomaj = 0.0
            for ab, ann in classified:
                s = ann.get(trait)
                if not s:
                    continue
                annotated_ab += ab
                state, _ = parse_majority(s["majority_label"], True)
                if state is None:
                    ab_nomaj += ab
                elif str(state).lower() == "true":
                    ab_true += ab
                else:
                    ab_false += ab
            unannot = total - unclassified_ab - annotated_ab
            rows.append((trait, "consensus_true", f"{tslug}.true", ab_true))
            rows.append((trait, "consensus_false", f"{tslug}.false", ab_false))
            rows.append((trait, "no_majority", f"{tslug}.no_majority", ab_nomaj))
            rows.append((trait, "unannotated", f"{tslug}.unannotated", unannot))
            rows.append((trait, "unclassified", f"{tslug}.unclassified", unclassified_ab))

        else:  # factor
            by_state = defaultdict(float)
            ab_nomaj = 0.0
            for ab, ann in classified:
                s = ann.get(trait)
                if not s:
                    continue
                annotated_ab += ab
                state, _ = parse_majority(s["majority_label"], True)
                if state is None:
                    ab_nomaj += ab
                else:
                    by_state[state] += ab
            unannot = total - unclassified_ab - annotated_ab
            if by_state:
                dom = max(by_state, key=by_state.get)
                dom_ab = by_state[dom]
                other_ab = sum(v for k, v in by_state.items() if k != dom)
            else:
                dom, dom_ab, other_ab = "other", 0.0, 0.0
            rows.append((trait, "consensus_majority", f"{tslug}.{slug(dom)}", dom_ab))
            rows.append((trait, "consensus_other", f"{tslug}.other", other_ab))
            rows.append((trait, "no_majority", f"{tslug}.no_majority", ab_nomaj))
            rows.append((trait, "unannotated", f"{tslug}.unannotated", unannot))
            rows.append((trait, "unclassified", f"{tslug}.unclassified", unclassified_ab))

    with open(out_path, "w") as out:
        out.write("trait\tsummary_type\tfeature\trelative_abundance\n")
        for trait, st, feat, val in rows:
            out.write(f"{trait}\t{st}\t{feat}\t{val}\n")

    return total, unclassified_ab, len(traits)


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="Reprodução local do sumTraits.")
    ap.add_argument("--profile", required=True, help="Perfil TSV (taxon_id, taxon_name, taxon_lineage, relative_abundance)")
    ap.add_argument("--genus", help="ncbi_genus_summary.jsonl")
    ap.add_argument("--species", help="ncbi_species_summary.jsonl (opcional)")
    ap.add_argument("--family", help="ncbi_family_summary.jsonl (opcional)")
    ap.add_argument("--out-prefix", required=True)
    args = ap.parse_args()

    # Ordem de resolução: espécie -> género -> família (mais específico primeiro)
    dbs = []
    if args.species:
        dbs.append(("species", load_summary(args.species)))
    if args.genus:
        dbs.append(("genus", load_summary(args.genus)))
    if args.family:
        dbs.append(("family", load_summary(args.family)))
    if not dbs:
        sys.exit("Forneça pelo menos um ficheiro de summary (--genus/--species/--family).")

    taxa = parse_profile(args.profile)

    n_taxon = write_taxon_table(taxa, dbs, f"{args.out_prefix}_taxon_trait_annotations.tsv")
    total, unclass, n_traits = write_community_table(
        taxa, dbs, f"{args.out_prefix}_community_trait_annotations.tsv")

    sys.stderr.write(
        f"[ok] taxa lidos: {len(taxa)} | linhas por-taxon: {n_taxon} | "
        f"traços na comunidade: {n_traits}\n"
        f"[ok] abundância total: {total:.6f} | não-classificada: {unclass:.6f}\n")


if __name__ == "__main__":
    main()

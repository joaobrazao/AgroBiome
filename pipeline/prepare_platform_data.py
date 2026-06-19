#!/usr/bin/env python3
"""
prepare_platform_data.py — gera os JSON estáticos para o MVP da plataforma.

File-driven: processa todas as amostras presentes na community_matrix /
composition_matrix. A exclusão de amostras faz-se a montante (removendo os
ficheiros em data/raw/samples/ e regenerando), não aqui.

Outputs em app/data/:
  compositions.json  — géneros × amostras (para Bray-Curtis no browser)
  pcoa.json          — PC1/PC2 das amostras (para gráfico de ordenação)
  traits/<sid>.json  — perfis de traços por amostra (filtrados por relevância)
  group_scores.json  — scores dos grupos interpretativos por amostra
"""

import json
import sys
import re
import csv
from pathlib import Path

ROOT       = Path(__file__).resolve().parent.parent
OUT_DIR    = ROOT / "app" / "data"
DERIVED    = ROOT / "data" / "derived"
DOCS       = ROOT / "docs"

COMP_FILE   = DERIVED / "composition_matrix.tsv"
PCOA_FILE   = DERIVED / "pcoa_coordinates.tsv"
TRAIT_FILE  = DERIVED / "community_matrix.tsv"
CLASSIF_FILE = DOCS / "classificacao_tracos.csv"
TRAIT_NAMES_FILE = OUT_DIR / "trait_names.json"

KEEP_CATS = {'agronomico', 'incerto'}

GROUP_SCORES_FILE  = DOCS / "tracos_por_grupo.csv"


def sample_prefix(name):
    """'10_ERR15663939_db3' → '10'"""
    m = re.match(r'^(\d+)', name)
    return m.group(1) if m else name


def build_keep_slugs():
    """
    Lê classificacao_tracos.csv e devolve o conjunto de feature slugs a manter.
    Mantém categorias 'agronomico' e 'incerto'; exclui 'sem_relevancia'.
    Faz o mapeamento nome_display → slug via trait_names.json.
    """
    tn = json.loads(TRAIT_NAMES_FILE.read_text())
    name_to_slug = {v: k for k, v in tn.items()}

    keep_names = set()
    with open(CLASSIF_FILE, newline='') as f:
        reader = csv.reader(f, delimiter=';')
        next(reader)  # header: trait;type;category
        for row in reader:
            if len(row) < 3:
                continue
            # row[0]=nome, row[1]=tipo, row[2]=categoria
            # (linhas malformadas onde nome contém ';' têm row[2]='discreto'/tipo
            # e row[3]=categoria — mas essas são sempre sem_relevancia, ignoramos)
            if row[2] in KEEP_CATS:
                keep_names.add(row[0])

    keep_slugs = {name_to_slug[n] for n in keep_names if n in name_to_slug}
    return keep_slugs


def build_compositions():
    print("compositions.json...", file=sys.stderr)
    with open(COMP_FILE) as f:
        reader = csv.reader(f, delimiter='\t')
        header = next(reader)
        samples = header[1:]  # already numeric strings: '1','2',...

        genera = []
        matrix = []
        for row in reader:
            genera.append(row[0])
            matrix.append([round(float(v), 6) for v in row[1:]])

    data = {"genera": genera, "samples": samples, "matrix": matrix}
    out = OUT_DIR / "compositions.json"
    out.write_text(json.dumps(data, separators=(',', ':')))
    print(f"  {len(genera)} géneros × {len(samples)} amostras → {out.stat().st_size//1024} KB",
          file=sys.stderr)


def build_pcoa():
    print("pcoa.json...", file=sys.stderr)
    with open(PCOA_FILE) as f:
        reader = csv.reader(f, delimiter='\t')
        header = next(reader)   # sample, PC1, PC2, ...
        pc1_idx, pc2_idx = 1, 2

        samples, pc1, pc2 = [], [], []
        for row in reader:
            samples.append(row[0])
            pc1.append(round(float(row[pc1_idx]), 6))
            pc2.append(round(float(row[pc2_idx]), 6))

    # Percentagem de variância explicada (hardcoded dos logs do build_beta_diversity)
    data = {"samples": samples, "pc1": pc1, "pc2": pc2,
            "pct_var": [19.7, 11.9]}
    out = OUT_DIR / "pcoa.json"
    out.write_text(json.dumps(data, separators=(',', ':')))
    print(f"  {len(samples)} amostras → {out.stat().st_size} bytes", file=sys.stderr)


def build_traits():
    # Um ficheiro JSON por amostra: platform/data/traits/<sid>.json
    # Filtrado para os slugs agronomicamente relevantes (spec secção 3).
    print("traits/<sid>.json...", file=sys.stderr)
    traits_dir = OUT_DIR / "traits"
    traits_dir.mkdir(exist_ok=True)

    keep_slugs = build_keep_slugs()
    print(f"  Slugs relevantes: {len(keep_slugs)}", file=sys.stderr)

    with open(TRAIT_FILE) as f:
        reader = csv.reader(f, delimiter='\t')
        all_features = next(reader)[1:]
        # Manter só features cujo slug (antes do '.') está em keep_slugs
        keep_idx = [i for i, ft in enumerate(all_features)
                    if ft.split('.')[0] in keep_slugs]
        keep_feats = [all_features[i] for i in keep_idx]

        sizes = []
        for row in reader:
            sid = sample_prefix(row[0])
            vals = {}
            for i, feat in zip(keep_idx, keep_feats):
                fv = float(row[i + 1])  # +1: row[0] é o sample name
                if fv > 0:
                    vals[feat] = round(fv, 6)
            out = traits_dir / f"{sid}.json"
            out.write_text(json.dumps(vals, separators=(',', ':')))
            sizes.append(out.stat().st_size)

    avg_kb = sum(sizes) // len(sizes) // 1024
    print(f"  {len(sizes)} ficheiros, média {avg_kb} KB/amostra → "
          f"{traits_dir}", file=sys.stderr)


def build_group_scores():
    """
    Pré-calcula os scores dos 19 grupos interpretativos para as 47 amostras.
    Usa tracos_por_grupo.csv para mapear grupos a traços e trait_names.json
    para converter display-name -> slug.
    Guardado em group_scores.json para cálculo dinâmico de percentis no browser.
    """
    print("group_scores.json...", file=sys.stderr)

    # 1. Mapear display_name -> slug via trait_names.json
    tn = json.loads(TRAIT_NAMES_FILE.read_text())
    name_to_slug = {v: k for k, v in tn.items()}

    # 2. Ler tracos_por_grupo.csv -> grupos discretos e grupo 11 (numérico)
    group_slugs = {}   # group_id -> [slug, ...]
    group_type  = {}   # group_id -> 'discreto' | 'numerico'
    with open(GROUP_SCORES_FILE, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            gid   = row['group_id']
            trait = row['trait']
            ttype = row['type']
            slug  = name_to_slug.get(trait)
            if slug is None:
                continue  # sem mapeamento de slug
            if gid not in group_slugs:
                group_slugs[gid] = []
                group_type[gid]  = ttype
            group_slugs[gid].append(slug)

    # 3. Ler community_matrix — determinar colunas disponíveis
    with open(TRAIT_FILE) as f:
        reader = csv.reader(f, delimiter='\t')
        header = next(reader)
        col = {c: i for i, c in enumerate(header)}

    # 4. Para cada grupo discreto: lista de índices de colunas slug.true presentes
    group_cols = {}    # group_id -> [col_idx, ...]
    for gid, slugs in group_slugs.items():
        if gid == '11':
            continue  # tratado separadamente
        idxs = []
        for slug in slugs:
            feat = slug + '.true'
            if feat in col:
                idxs.append(col[feat])
        group_cols[gid] = idxs

    # Grupo 11 — só as 3 colunas numéricas
    G11_PH   = 'ph_growth.mean'
    G11_TEMP = 'temperature_growth.mean'
    G11_SAL  = 'salinity_growth.mean'
    for feat in (G11_PH, G11_TEMP, G11_SAL):
        if feat not in col:
            sys.exit(f"Feature obrigatória ausente na community_matrix: {feat}")

    # 5. Iterar amostras e calcular scores
    samples    = []
    group_data = {gid: [] for gid in group_cols}
    g11_ph, g11_temp, g11_sal = [], [], []

    with open(TRAIT_FILE) as f:
        reader = csv.reader(f, delimiter='\t')
        next(reader)  # skip header
        for row in reader:
            sid = sample_prefix(row[0])
            samples.append(sid)
            for gid, idxs in group_cols.items():
                if idxs:
                    score = sum(float(row[i]) for i in idxs) / len(idxs)
                else:
                    score = 0.0
                group_data[gid].append(round(score, 6))
            g11_ph.append(round(float(row[col[G11_PH]]),   4))
            g11_temp.append(round(float(row[col[G11_TEMP]]), 2))
            g11_sal.append(round(float(row[col[G11_SAL]]),  4))

    # 6. Relatório
    print(f"  Grupos detectados: {sorted(group_cols.keys())}", file=sys.stderr)
    for gid in sorted(group_cols.keys()):
        n_slugs = len(group_slugs.get(gid, []))
        n_cols  = len(group_cols[gid])
        note = " *** SEM COLUNAS .true ***" if n_cols == 0 else ""
        print(f"    {gid}: {n_slugs} traços no CSV → {n_cols} colunas .true na matrix{note}",
              file=sys.stderr)

    data = {
        "samples": samples,
        "groups":  {gid: vals for gid, vals in group_data.items()},
        "g11":     {"ph": g11_ph, "temp": g11_temp, "sal": g11_sal},
    }
    out = OUT_DIR / "group_scores.json"
    out.write_text(json.dumps(data, separators=(',', ':')))
    print(f"  {len(samples)} amostras → {out.stat().st_size} bytes → {out}", file=sys.stderr)


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    build_compositions()
    build_pcoa()
    build_traits()
    build_group_scores()
    print("\nDone. Ficheiros em app/data/", file=sys.stderr)

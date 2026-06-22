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
TRAIT_PT_FILE      = DOCS / "tracos_traducao.csv"
PER_SAMPLE_DIR     = DERIVED / "per_sample"
GROUP_GENERA_DIR   = OUT_DIR / "group_genera"
GENUS_GROUPS_FILE  = OUT_DIR / "genus_groups.json"
TOP_GENERA_PER_GROUP = 8


def slug(s):
    """slug(trait) — minúsculas, runs de não-alfanuméricos -> '_' (igual ao pipeline)."""
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')


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


def build_trait_names_pt():
    """
    Gera trait_names_pt.json = {slug: trait_pt} a partir de tracos_traducao.csv.
    O slug é calculado de trait_en (chave estável do pipeline); só a apresentação
    usa trait_pt. As chaves deste ficheiro são também o universo dos 360 traços
    apresentados (após remoção do grupo 13), usado no KPI 'indicadores >5%'.
    """
    print("trait_names_pt.json...", file=sys.stderr)
    pt = {}
    with open(TRAIT_PT_FILE, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pt[slug(row['trait_en'])] = row['trait_pt']
    out = OUT_DIR / "trait_names_pt.json"
    out.write_text(json.dumps(pt, ensure_ascii=False, separators=(',', ':')))
    print(f"  {len(pt)} traços traduzidos → {out}", file=sys.stderr)


def build_group_genera():
    """
    Para cada amostra e cada grupo discreto, pré-calcula os géneros que mais
    contribuem (drill-down §8): géneros com consensus_bool=True para >=1 traço
    booleano do grupo, ordenados pela sua abundância relativa na amostra.
    Output: group_genera/<sid>.json = {group_id: [[genus, frac], ...top N]}.
    O grupo 11 (ótimos ambientais, numérico) é excluído.
    """
    print("group_genera/<sid>.json...", file=sys.stderr)
    GROUP_GENERA_DIR.mkdir(exist_ok=True)

    # 1. grupo -> set de nomes de traço discretos (exclui grupo 11 numérico)
    group_traits = {}   # gid -> set(trait_name)
    trait_groups = {}   # trait_name -> set(gid)
    with open(GROUP_SCORES_FILE, newline='') as f:
        for row in csv.DictReader(f):
            if row['group_id'] == '11' or row['type'] != 'discreto':
                continue
            gid, tr = row['group_id'], row['trait']
            group_traits.setdefault(gid, set()).add(tr)
            trait_groups.setdefault(tr, set()).add(gid)

    # 2. abundância de género por amostra (composition_matrix: géneros × amostras)
    with open(COMP_FILE) as f:
        reader = csv.reader(f, delimiter='\t')
        comp_samples = next(reader)[1:]
        genus_abund = {sid: {} for sid in comp_samples}   # sid -> {genus: frac}
        for row in reader:
            genus = row[0]
            for sid, v in zip(comp_samples, row[1:]):
                fv = float(v)
                if fv > 0:
                    genus_abund[sid][genus] = fv

    # 3. percorrer os taxon_trait_annotations por amostra
    files = sorted(PER_SAMPLE_DIR.glob("*_taxon_trait_annotations.tsv"))
    written = 0
    for fp in files:
        sid = sample_prefix(fp.name)
        abund = genus_abund.get(sid, {})
        genus_groups = {}   # genus -> set(gid) positivos
        with open(fp) as f:
            reader = csv.reader(f, delimiter='\t')
            header = next(reader)
            ci = {c: i for i, c in enumerate(header)}
            i_name, i_trait = ci['taxon_name'], ci['trait']
            i_bool = ci['consensus_bool']
            for r in reader:
                if r[i_bool] != 'True':
                    continue
                gids = trait_groups.get(r[i_trait])
                if not gids:
                    continue
                genus_groups.setdefault(r[i_name], set()).update(gids)

        # 4. por grupo: géneros positivos ordenados por abundância
        #    top = [[genus, frac], ...]; more = nº de géneros contribuintes além do top
        out_obj = {}
        for gid in group_traits:
            ranked = [
                (g, abund.get(g, 0.0))
                for g, gs in genus_groups.items() if gid in gs and abund.get(g, 0.0) > 0
            ]
            ranked.sort(key=lambda t: t[1], reverse=True)
            top = [[g, round(a, 6)] for g, a in ranked[:TOP_GENERA_PER_GROUP]]
            out_obj[gid] = {"top": top, "more": max(0, len(ranked) - len(top))}

        (GROUP_GENERA_DIR / f"{sid}.json").write_text(
            json.dumps(out_obj, ensure_ascii=False, separators=(',', ':')))
        written += 1

    print(f"  {written} amostras → {GROUP_GENERA_DIR}", file=sys.stderr)


def build_genus_groups():
    """
    Mapa global género -> grupos discretos para os quais o género é positivo
    (consensus_bool=True em >=1 traço do grupo). A pertença é intrínseca ao
    género (vem da BD de traços), independente da amostra; por isso é única e
    serve o drill-down §8 da plataforma calculado sobre a AMOSTRA INPUT
    (géneros do input ponderados pela abundância do input), em vez do match.
    Output: genus_groups.json = {genus_name: [gid, ...]}. Grupo 11 excluído.
    """
    print("genus_groups.json...", file=sys.stderr)

    trait_groups = {}   # trait_name -> set(gid) (exclui grupo 11 numérico)
    with open(GROUP_SCORES_FILE, newline='') as f:
        for row in csv.DictReader(f):
            if row['group_id'] == '11' or row['type'] != 'discreto':
                continue
            trait_groups.setdefault(row['trait'], set()).add(row['group_id'])

    genus_groups = {}   # genus -> set(gid)
    files = sorted(PER_SAMPLE_DIR.glob("*_taxon_trait_annotations.tsv"))
    for fp in files:
        with open(fp) as f:
            reader = csv.reader(f, delimiter='\t')
            header = next(reader)
            ci = {c: i for i, c in enumerate(header)}
            i_name, i_trait, i_bool = ci['taxon_name'], ci['trait'], ci['consensus_bool']
            for r in reader:
                if r[i_bool] != 'True':
                    continue
                gids = trait_groups.get(r[i_trait])
                if gids:
                    genus_groups.setdefault(r[i_name], set()).update(gids)

    out = {g: sorted(gs, key=lambda x: (len(x), x)) for g, gs in genus_groups.items()}
    GENUS_GROUPS_FILE.write_text(
        json.dumps(out, ensure_ascii=False, separators=(',', ':')))
    print(f"  {len(files)} amostras → {len(out)} géneros → {GENUS_GROUPS_FILE}", file=sys.stderr)


def build_group_scores():
    """
    Pré-calcula os scores dos 18 grupos interpretativos para as amostras da coleção.
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
    build_trait_names_pt()
    build_group_scores()
    build_group_genera()
    build_genus_groups()
    print("\nDone. Ficheiros em app/data/", file=sys.stderr)

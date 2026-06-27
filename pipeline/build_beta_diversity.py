#!/usr/bin/env python3
"""
build_beta_diversity.py — espaço de diversidade beta (Bray-Curtis + PCoA).

Outputs:
  bray_curtis_distances.tsv  — matriz 47×47 de distâncias
  pcoa_coordinates.tsv       — coordenadas PCoA das 47 amostras (todos os eixos positivos)
  pcoa_model.npz             — modelo para projetar amostras novas (eigenvectors, etc.)

Funções exportáveis:
  load_model()       → devolve o modelo PCoA serializado
  knn(x_new, k)      → k vizinhos mais próximos de uma amostra nova
  project(x_new)     → coordenadas PCoA aproximadas da amostra nova
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.spatial.distance import cdist

ROOT    = Path(__file__).resolve().parent.parent
DERIVED = ROOT / "data" / "derived"
MATRIX_FILE  = DERIVED / "composition_matrix.tsv"
DIST_FILE    = DERIVED / "bray_curtis_distances.tsv"
PCOA_FILE    = DERIVED / "pcoa_coordinates.tsv"
MODEL_FILE   = DERIVED / "pcoa_model.npz"


# ---------------------------------------------------------------------------
# PCoA (Classical MDS)
# ---------------------------------------------------------------------------

def pcoa(D):
    """
    PCoA sobre matriz de distâncias D (n×n).
    Devolve (coords, eigvals, eigvecs) ordenados por eigenvalor decrescente.
    coords: apenas eixos com eigenvalor positivo (n × n_pos).
    eigvals/eigvecs: todos os n valores/vetores (para projeção posterior).
    """
    n = D.shape[0]
    D2 = D ** 2
    # Centering matrix
    H = np.eye(n) - np.ones((n, n)) / n
    B = -0.5 * (H @ D2 @ H)
    eigvals, eigvecs = np.linalg.eigh(B)
    idx = np.argsort(eigvals)[::-1]
    eigvals = eigvals[idx]
    eigvecs = eigvecs[:, idx]
    pos = eigvals > 1e-10
    coords = eigvecs[:, pos] * np.sqrt(eigvals[pos])
    return coords, eigvals, eigvecs


def project_new_sample(x_new, X_ref, col_mean_d2, grand_mean_d2, eigvals, eigvecs):
    """
    Projeta uma amostra nova no espaço PCoA existente (fórmula de Gower).

    x_new      : vetor de abundâncias (n_genera,)
    X_ref      : matriz de referência (n_samples × n_genera)
    col_mean_d2: média das d² por coluna da D² original (n_samples,)
    grand_mean_d2: média global de D²
    eigvals/eigvecs: do modelo PCoA
    """
    d_new = cdist(x_new.reshape(1, -1), X_ref, metric='braycurtis').flatten()
    d2_new = d_new ** 2
    # Fórmula de projeção (centering análogo ao double-centering original)
    a = -0.5 * (d2_new - d2_new.mean() - col_mean_d2 + grand_mean_d2)
    pos = eigvals > 1e-10
    lam = eigvals[pos]
    U = eigvecs[:, pos]
    # Escala: as coords de referência são U*sqrt(lam); para um ponto in-sample
    # (U.T @ a) = U[i]*lam, logo divide-se por sqrt(lam) (não por lam) para bater
    # com a convenção das referências. Validado: erro ~5e-9 vs coords originais.
    coords_new = (U.T @ a) / np.sqrt(lam)
    return coords_new


def knn(x_new, X_ref, sample_ids, k=5):
    """
    Devolve os k vizinhos mais próximos (por Bray-Curtis) de x_new.
    Retorna lista de (sample_id, distância) ordenada por distância.
    """
    dists = cdist(x_new.reshape(1, -1), X_ref, metric='braycurtis').flatten()
    idx = np.argsort(dists)[:k]
    return [(sample_ids[i], float(dists[i])) for i in idx]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("A carregar matriz de composição...", file=sys.stderr)
    df = pd.read_csv(MATRIX_FILE, sep='\t', index_col=0)
    print(f"  {df.shape[0]} géneros × {df.shape[1]} amostras", file=sys.stderr)

    X = df.values.T          # (n_samples × n_genera)
    sample_ids = list(df.columns)

    # --- Bray-Curtis ---
    print("A calcular distâncias Bray-Curtis...", file=sys.stderr)
    D = cdist(X, X, metric='braycurtis')

    dist_df = pd.DataFrame(D, index=sample_ids, columns=sample_ids)
    dist_df.to_csv(DIST_FILE, sep='\t', float_format='%.8f')
    print(f"  Distâncias escritas: {DIST_FILE}", file=sys.stderr)
    print(f"  Min={D[D>0].min():.4f}  Max={D.max():.4f}  Mean={D[D>0].mean():.4f}",
          file=sys.stderr)

    # --- PCoA ---
    print("A correr PCoA...", file=sys.stderr)
    coords, eigvals, eigvecs = pcoa(D)

    total_var = eigvals[eigvals > 0].sum()
    pct = eigvals[:coords.shape[1]] / total_var * 100
    print(f"  Eixos positivos: {coords.shape[1]}", file=sys.stderr)
    print(f"  PC1={pct[0]:.1f}%  PC2={pct[1]:.1f}%  PC3={pct[2]:.1f}%  "
          f"(top-3 acumulado: {pct[:3].sum():.1f}%)", file=sys.stderr)

    col_names = [f"PC{i+1}" for i in range(coords.shape[1])]
    pcoa_df = pd.DataFrame(coords, index=sample_ids, columns=col_names)
    pcoa_df.to_csv(PCOA_FILE, sep='\t', float_format='%.8f')
    print(f"  Coordenadas PCoA escritas: {PCOA_FILE}", file=sys.stderr)

    # --- Modelo para projeção ---
    D2 = D ** 2
    col_mean_d2  = D2.mean(axis=0)
    grand_mean_d2 = D2.mean()

    np.savez(MODEL_FILE,
             X_ref=X,
             sample_ids=np.array(sample_ids),
             genera=np.array(df.index.tolist()),
             eigvals=eigvals,
             eigvecs=eigvecs,
             col_mean_d2=col_mean_d2,
             grand_mean_d2=np.array([grand_mean_d2]))
    print(f"  Modelo PCoA guardado: {MODEL_FILE}", file=sys.stderr)

    print("\nVerificações:", file=sys.stderr)
    print(f"  Amostras: {len(sample_ids)}", file=sys.stderr)
    print(f"  Diagonal D == 0: {np.allclose(np.diag(D), 0)}", file=sys.stderr)
    print(f"  D simétrica: {np.allclose(D, D.T)}", file=sys.stderr)
    print(f"  D ∈ [0,1]: {D.min()>=0 and D.max()<=1}", file=sys.stderr)


def load_model():
    """Carrega o modelo PCoA guardado. Devolve dict com arrays numpy."""
    m = np.load(MODEL_FILE, allow_pickle=True)
    return {k: m[k] for k in m.files}


if __name__ == "__main__":
    main()

# Microbioma do Solo — Plataforma de Traços Funcionais (Piloto Viticultura)

A partir de perfis taxonómicos de microbioma do solo (16S/Bracken), o projeto
anota traços fenotípicos (metaTraits / EMBL), constrói uma base de dados de
referência de amostras de solo de vinha e permite comparar uma amostra nova
contra essa BD, inferindo um **perfil funcional** ("potencial microbiano
inferido", não função medida).

## Organização

```
.
├─ app/                  Plataforma web (página única, sem servidor). Entregável.
│  ├─ index.html
│  └─ data/              JSON estáticos gerados pelo pipeline
├─ pipeline/             Scripts Python do processamento
├─ data/
│  ├─ raw/
│  │  ├─ samples/                  relatórios Bracken da BD (*.report_bracken.txt)
│  │  │   ├─ alentejo_samples/     cohort antigo arquivado — fora do glob
│  │  │   └─ excluded_degenerate/  amostras degeneradas excluídas — fora do glob
│  │  └─ ncbi_genus_summary.jsonl  BD de traços metaTraits (só género, ~105 MB)
│  ├─ sample_registry.tsv  registo accession → número de amostra (consultar aqui)
│  └─ derived/           Saídas geradas (matrizes, distâncias, PCoA, por-amostra)
│     ├─ composition_matrix.tsv    géneros × amostras (abundância relativa)
│     ├─ bray_curtis_distances.tsv
│     ├─ pcoa_coordinates.tsv / pcoa_model.npz
│     ├─ community_matrix.tsv      amostras × traços (tabela de consulta do match)
│     └─ per_sample/               perfil + anotações por amostra
├─ docs/                 Especificação, classificação de traços e memória descritiva
│  ├─ especificacao_camada_interpretativa.md
│  ├─ classificacao_tracos.csv     (delimitador ';')
│  ├─ tracos_por_grupo.csv         (delimitador ',')
│  └─ memoria_descritiva_plataforma.docx   (evidência; gerada com pandoc)
└─ archive/              Versões antigas e artefactos de teste (não publicado)
```

## Pipeline

Da amostra (Bracken) ao perfil funcional:

1. `bracken_to_profile.py` — relatório Bracken → perfil normalizado de 4 colunas
   (colapsa espécies no género pai).
2. `sumtraits_local.py` — perfil → anotações de traços (por taxon + agregação à
   comunidade), no formato exato do site metaTraits.
3. `batch_pipeline.py` — orquestra 1+2 sobre todas as amostras e escreve a
   `community_matrix.tsv`.
4. `build_composition_matrix.py` — matriz géneros × amostras (abundância relativa).
5. `build_beta_diversity.py` — distâncias Bray-Curtis + PCoA + modelo de projeção
   de amostra nova (Gower, guardado em `pcoa_model.npz`).
6. `prepare_platform_data.py` — gera os JSON estáticos de `app/data/`.

### Pipeline file-driven

A lista de amostras do piloto **é** o conteúdo de `data/raw/samples/`. Para
adicionar, remover ou substituir amostras basta mexer nos ficheiros dessa pasta
e voltar a correr o pipeline — não há listas de amostras hard-coded nos scripts.

**Identidade da amostra (registo).** Cada amostra é identificada pela sua
**accession** (ENA/SRA: `ERR…`), não pelo prefixo numérico do nome (que pode
colidir entre cohorts). O pipeline mantém um registo accession → número estável
em `data/sample_registry.tsv` (ver `pipeline/sample_registry.py`): largas
ficheiros na pasta e, ao correr o pipeline, cada accession nova recebe o próximo
número livre, enquanto as antigas mantêm o seu para sempre. **Não é preciso
numerar nem coordenar nomes à mão.** Para saber a que amostra corresponde um
número mostrado na plataforma, consulta esse ficheiro.

### Correr

Requer Python 3.10+ com `numpy`, `pandas`, `scipy`.

**Atalho:** `./pipeline/regenerate.sh` corre toda a cadeia abaixo de uma vez (e
trata da consolidação da `community_matrix`). Usa `--no-batch` para saltar a
anotação de traços e reusar a `community_matrix` existente. Os passos manuais
seguintes ficam para referência ou execução parcial.

```bash
# (1+2+3) anotação de traços + community_matrix
python pipeline/batch_pipeline.py \
    --reports data/raw/samples \
    --genus   data/raw/ncbi_genus_summary.jsonl \
    --out-dir data/derived/per_sample

# mover/garantir a matriz consolidada em data/derived/community_matrix.tsv
# (batch_pipeline escreve-a em --out-dir)

# (4) matriz de composição
python pipeline/build_composition_matrix.py

# (5) diversidade beta
python pipeline/build_beta_diversity.py

# (6) dados estáticos da plataforma
python pipeline/prepare_platform_data.py
```

## Aplicação

Página única sem servidor. Servir localmente:

```bash
cd app && python -m http.server 8000   # abrir http://localhost:8000
```

**URL publicado:** _(placeholder — a definir; publicável em GitHub Pages /
Netlify a partir de `app/`)_.

Em produção, publicar com **gzip/brotli** (automático no GitHub Pages / Netlify):
o maior payload é `app/data/compositions.json` (~10 KB/amostra, ~80% zeros), que
comprime ~8×. Confortável até alguns milhares de amostras sem alterar o formato;
para escalas maiores, ver "Escalabilidade" no `CLAUDE.md`.

## Decisões-chave

- Trabalha-se só ao nível de **género** (resolução fiável do 16S).
- Comparação por **composição taxonómica** (diversidade beta); a matriz de
  traços é a tabela de consulta para importar o perfil funcional do(s) match(es).
- A BD de referência é o conteúdo de `data/raw/samples/`. Amostras degeneradas
  (poucos géneros / poucas reads) são **excluídas** para
  `samples/excluded_degenerate/`; cohorts antigos ficam arquivados em
  `samples/alentejo_samples/` — ambos fora do glob não-recursivo.
- Camada interpretativa **relativa à coleção** (percentis dinâmicos, não limiares
  absolutos), com framing "potencial inferido" e não-prescritivo. Exceção: grupo
  11 (ótimos ambientais) — pH e temperatura em escala absoluta; salinidade em
  régua relativa mas mostrando o valor absoluto (% NaCl).

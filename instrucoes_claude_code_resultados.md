# AgroBiome Digital — Instruções de implementação da nova página de resultados

**Destinatário:** Claude Code
**Ficheiro-alvo:** `app/index.html` (aplicação single-file servida em GitHub Pages)
**Referência visual:** `exemplo_resultados_agrobiome.html` (protótipo com amostra fictícia; usar como referência de layout, estética e estrutura, **não** copiar texto nem dados — o conteúdo final é gerado a partir dos dados reais)

---

## 0. Contexto e âmbito

Esta especificação descreve a reformulação da **página de resultados** do AgroBiome Digital. A aplicação analisa relatórios taxonómicos Kraken2/Bracken e infere o potencial funcional da comunidade microbiana do solo, ao nível de género (resolução do 16S). Serve dois públicos em simultâneo: produtores (linguagem corrente) e agrónomos (camada técnica).

Restrições transversais, a respeitar em todas as secções:

- **Manter a arquitetura single-file** (HTML + CSS + JS num só ficheiro), compatível com GitHub Pages.
- **Fundo claro e imprimível.** Nada de fundos escuros — a página tem dupla função: ferramenta interativa e evidência documental do dossier (indicador "1 produto/serviço" do Voucher para Startups).
- **Português europeu correto e acentuado** em toda a interface. O protótipo de referência tem acentos em falta por uma limitação de codificação; o texto final **deve** ser ortograficamente correto.
- **Regra de enquadramento (inviolável):** a plataforma **descreve** o potencial microbiano inferido; **nunca recomenda** ações agronómicas (fertilizar, inocular, corrigir pH, etc.) nem emite juízos de valor ("bom"/"mau" solo). "Alto" significa apenas posição elevada face à coleção de referência, não mérito.
- **Separação motor de match / camada interpretativa:** o emparelhamento entre a amostra e a coleção usa **exclusivamente** a composição taxonómica (Bracken, distância Bray-Curtis). Os traços funcionais **nunca** são usados no match — apenas na interpretação pós-match.

---

## 1. Amostra de teste (botão de exemplo)

No ecrã de entrada (carregamento de amostra), acrescentar um botão **"Carregar amostra de exemplo"**.

- Ao ser premido, injeta o relatório Bracken da **amostra 10** da coleção e corre o pipeline normal de análise, como se o utilizador a tivesse carregado.
- **Não excluir** a amostra 10 da distribuição de referência no cálculo dos níveis relativos (ver §15). É um placeholder assumido, a substituir mais tarde por uma amostra de demonstração dedicada.
- Objetivo: permitir experimentar a plataforma sem ficheiro próprio.

---

## 2. Remover o grupo "Metabolismo geral" — remoção total

O grupo **group_id 13 — "Metabolismo geral"** (10 traços: NiFe-hidrogenase, catalase, hidrogenase, oxidase, fenilalanina-amónia-liase, hemólise, produção de hidrogénio, produção de melanina, requisito de biotina, requisito de cobalamina) é **removido por completo, sem vestígios**:

- Não aparece em nenhuma vista de apresentação (chips, teias, cartões, tabela de indicadores, agregados).
- **É removido também do pipeline e dos ficheiros CSV de saída** — não é apenas ocultado. Eliminar as 10 entradas e quaisquer referências ao group_id 13 em código e dados.

Consequência: passam a existir **18 grupos** funcionais e **360 traços**. Todas as referências de interface a "19 grupos" passam a "18 grupos".

---

## 3. Hierarquia das secções (ordem "resposta primeiro")

Reordenar a página de resultados para entregar a leitura útil antes da mecânica do método. Ordem vertical:

1. Faixa persistente inferido-vs-medido (§4)
2. Painel-sumário: KPIs + heatmap de chips (§5)
3. Duas teias (§7)
4. Perfil funcional interpretado (§8)
5. Composição da comunidade observada — sunburst + diversidade (§9)
6. Indicadores funcionais — tabela (§10)
7. Ótimos ambientais — cartão detalhado (§11)
8. Evidência do match — PCoA + vizinhos (§12)
9. Rodapé com atribuição e exportação (§13)

A ordenação PCoA/vizinhos, que antes abria a página, passa para o fim como evidência do método.

---

## 4. Faixa persistente inferido-vs-medido

Faixa fina, **sempre visível** no topo dos resultados (não dentro de `<details>`). Texto (sentido):

> Os indicadores exprimem o **potencial microbiano inferido** a partir da composição da comunidade — leitura comparativa face à coleção, **não** uma medição química ou de atividade do solo. A plataforma descreve o estado microbiano; não constitui recomendação agronómica.

Estilo discreto (fundo âmbar muito claro), legível na impressão.

---

## 5. Painel-sumário: KPIs + heatmap de chips

### 5.1 KPIs (quatro)

Grelha de quatro cartões de indicador:

1. **Géneros detetados** — contagem de géneros após colapso ao nível de género.
2. **Diversidade da comunidade** — rótulo relativo (baixa/moderada/alta) face à coleção (ver §9.2); o valor numérico de Shannon fica em nota secundária, não como número cru principal.
3. **Indicadores funcionais (>5%)** — contagem de traços presentes em mais de 5% da comunidade. Universo: os traços apresentados (os 360, após remoção do grupo 13). Métrica **exclusiva do sumário** — não altera nem aparece nas outras vistas.
4. **Ótimos ambientais (resumo)** — três bandas compactas (pH, temperatura, salinidade) como relance; o detalhe vive no cartão da §11.

*(A "confiança do match", presente em versões anteriores, foi removida. Não reintroduzir.)*

### 5.2 Heatmap de chips

Fila com os **18 grupos funcionais** como etiquetas (chips). O **fundo de cada chip** codifica o nível (baixo/moderado/alto) segundo a escala teal (§6) — a fila funciona como heatmap de uma linha. Mini-legenda "baixo → alto" junto ao título.

Nota: o título atual ("Assinatura por grupo funcional") é vago e quase colide com "assinatura funcional" das teias. Renomear para algo como **"Níveis por grupo (vista rápida)"**.

---

## 6. Escala de cor teal (sequencial)

Substituir a codificação categórica antiga (azul/verde/âmbar) por uma **escala sequencial de um só matiz** (teal), em que a intensidade comunica baixo→alto sem necessidade de decorar a legenda. Aplicar de forma **coerente** a chips, pills dos cartões e legenda.

| Nível | Fundo | Texto |
|---|---|---|
| baixo | `#9FE1CB` | `#04342C` |
| moderado | `#1D9E75` | `#04342C` |
| alto | `#085041` | `#E1F5EE` |

Não usar escala divergente (vermelho→verde): implicaria juízo mau→bom, que o enquadramento proíbe. O matiz único exprime intensidade/posição, não valor.

---

## 7. Duas teias (radar 9 + 8)

Dois gráficos radar, lado a lado, repartindo **17 dos 18 grupos** por afinidade temática. O grupo 11 "Óticos ambientais" **não entra nas teias** (é lido em escala absoluta na §11), pelo que a Teia 2 fica com 8 eixos. Cada eixo representa a **posição relativa da amostra face à coleção** (centro = fundo da distribuição; bordo = topo), na mesma lógica de percentil dos níveis (§15).

**Teia 1 — Ciclos biogeoquímicos** (9 eixos): N-fixação (1a), N-nitrificação (1b), N-desnitrificação (1c), N-amonificação (1d), Enxofre/anoxia (4), Fe/Mn redox (6), Metilotrofia (5), Carbono autotrófico (9), Fósforo (7).

**Teia 2 — Matéria orgânica, função e condição** (8 eixos): Decomposição-fibras (3a), Decomposição-proteínas (3b), Decomposição-xenobióticos (3c), Decomposição-geral (3d), PGP (8), Stress/resiliência (10), Arejamento (2), Agregação/armazenamento (12).

Convenção de **nomes curtos** dos eixos (para caber sem colisão):

- Teia 1: `N: fixação`, `N: nitrificação`, `N: desnitrif.`, `N: amonificação`, `Enxofre/anoxia`, `Fe/Mn redox`, `Metilotrofia`, `C autotróf.`, `Fósforo`
- Teia 2: `Decomp. fibras`, `Decomp. proteínas`, `Decomp. xenobiót.`, `Decomp. geral`, `PGP`, `Stress`, `Arejamento`, `Agregação`

Implementação: SVG client-side gerado a partir dos valores reais (não imagem estática). Cor distinta por teia (identificador de teia, não de nível).

---

## 8. Perfil funcional interpretado

Um **cartão por grupo** (18 cartões), cada um com:

- **Nome em linguagem corrente** (produtor).
- **Frase-síntese em camadas:** leitura corrente com o **termo técnico entre parênteses** na mesma frase — camada única, não dois modos comutáveis. Ex.: *"Forte capacidade de libertar azoto a partir da matéria orgânica (potencial de amonificação/mineralização elevado)."*
- **Pill de nível** (baixo/moderado/alto) na escala teal (§6).
- **Drill-down** em `<details>` ("Géneros que mais contribuem"): ao abrir, lista os **3 a 5 géneros** mais contribuintes daquele grupo, com a respetiva fração, mais um "(+N géneros)" discreto. Colapsado por defeito, para conter o excesso de informação.

As frases-síntese saem das regras de redação por grupo (resumo baseado em regras das leituras mais extremas, **não** geração livre por IA).

---

## 9. Composição da comunidade (observada)

Cartão que descreve **o que está presente** na amostra — distinto do potencial funcional inferido (rotular claramente para não confundir as duas categorias).

### 9.1 Sunburst

Anéis concêntricos taxonómicos (reino → … → género), **client-side** (Plotly `sunburst` ou D3), alimentado pelo relatório Bracken já parseado em JS. **Não** usar KronaTools (é Perl, gera HTML offline à parte, não corre no browser).

- **Agregar a cauda rara** num setor "Outros".
- **Limitar a profundidade** dos anéis para legibilidade.

### 9.2 Diversidade interpretada

Riqueza de géneros e índice de Shannon posicionados face à distribuição da coleção e apresentados como **rótulo relativo (baixa/moderada/alta)**, não como número cru (Shannan nu não é interpretável pelo produtor). O valor numérico fica em camada técnica secundária.

---

## 10. Indicadores funcionais (tabela)

Tabela traço-a-traço (a "Tabela A" existente): cada linha é um traço individual com a **fração da comunidade** que o possui (métrica única apresentada: a fração `true`). Manter a **pesquisa/filtro** para o utilizador localizar traços. É a camada de maior grão, que serve auditoria e verificação do dossier.

---

## 11. Ótimos ambientais (cartão detalhado)

Cartão com pH, temperatura e salinidade preferenciais da comunidade, em **escala absoluta com bandas de referência** (não a escala relativa dos grupos funcionais). Inferidos da preferência ambiental dos microrganismos presentes — rotular como preferência inferida, **não** medição do solo. O resumo de relance está nos KPIs (§5.1); este cartão é o detalhe.

---

## 12. Evidência do match (sempre visível)

Cartão **sempre visível** (já não recolhido em `<details>`), no fim dos resultados:

- Ordenação **PCoA** (Bray-Curtis, PC1/PC2), com a posição da amostra.
- Tabela das **amostras mais semelhantes** da coleção com as respetivas distâncias.
- Nota de que o perfil funcional é importado destes vizinhos por proximidade composicional.

O número de vizinhos a apresentar é parâmetro a fixar (sugestão: 5).

---

## 13. Atribuição, rodapé e impressão (PDF)

### 13.1 Rodapé de ecrã (letra pequena)

> AppGenomics · projeto Vouchers para Startups (PRR/IAPMEI) · amostras processadas com Kraken2/Bracken e perfil funcional inferido com metaTraits.

### 13.2 Cabeçalho e rodapé de impressão (`@media print`)

Visíveis **apenas na impressão/exportação para PDF** (não ocupam espaço no ecrã interativo):

- **Cabeçalho de PDF:** AppGenomics · "Perfil Funcional do Microbioma do Solo" · identificação da amostra · data · versão da coleção. (Sem logótipo — apenas texto.)
- **Rodapé de PDF:** referência do projeto (Vouchers para Startups, PRR/IAPMEI).

### 13.3 Exportação

Botão **"Exportar PDF"** que aciona a impressão do browser (`window.print()`). Garantir que `@media print` força fundo claro e oculta controlos interativos (botões, campos de pesquisa).

---

## 14. Resumo das três vistas (coerência)

Os mesmos 18 grupos são descritos com grão crescente em três vistas — manter cada uma claramente a um nível distinto, para não parecerem repetição:

- **Chips** (§5.2) — nível de relance.
- **Teias** (§7) — forma/assinatura.
- **Cartões** (§8) — leitura completa com géneros.

A **tabela de indicadores** (§10) é a única que desce ao traço individual e ao número exato.

---

## 15. Notas transversais de lógica de dados

- **Níveis relativos (baixo/moderado/alto):** escala **dinâmica baseada em percentis**, calculada em runtime, posicionando a amostra na distribuição da coleção para cada grupo/eixo. Regra geral: a amostra consultada é **excluída** da distribuição de referência no cálculo (para não se comparar consigo mesma). **Exceção:** a amostra de teste (amostra 10, §1) **não** é excluída — placeholder assumido.
- **Métrica apresentada:** a fração `true` (percentagem da comunidade com a função) é a única métrica exibida nos indicadores.
- **Ótimos ambientais:** escala **absoluta** com bandas de referência — distinta da relativa.
- **Match:** apenas composição taxonómica (Bray-Curtis); traços funcionais nunca entram no match.
- **Indicadores >5%:** contagem de traços com fração > 5%, sobre o universo dos 360 traços apresentados; métrica exclusiva do sumário.

---

## 16. Tradução dos traços para português europeu

Os traços estão atualmente **em inglês** nos dados e no código. Todos os nomes de traço visíveis na interface (cartões §8, tabela de indicadores §10, drill-downs) **devem ser apresentados em português europeu**.

Abordagem: um **ficheiro de mapeamento** `tracos_traducao.csv` (colunas `trait_en`, `trait_pt`, e `group_id` para contexto), consumido pelo pipeline/app para substituir o rótulo apresentado. Os identificadores internos e os dados de cálculo continuam a usar a chave inglesa (`trait_en`); só a apresentação usa `trait_pt`. Isto preserva a estabilidade do pipeline e a rastreabilidade.

A estrutura facilita a tradução: dos 360 traços, quase todos seguem o padrão `prefixo: termo`, com apenas **24 prefixos distintos**. A tradução é, por isso, semi-sistemática — os prefixos traduzem-se uma vez (ex.: `enzyme activity:` → `atividade enzimática:`, `carbon source:` → `fonte de carbono:`, `degradation:` → `degradação:`), e os termos (substratos, compostos, enzimas) caso a caso, com rigor terminológico de microbiologia.

O ficheiro `tracos_traducao.csv` é produzido à parte (ver conversa) e entregue junto com esta especificação. Os 10 traços do grupo 13 **não** constam dele (foram removidos, §2).

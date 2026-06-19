# Especificação — Camada Interpretativa da Plataforma

**Projeto:** Voucher 24025 — AppGenomics, Lda
**Âmbito:** definição da camada que transforma os perfis de traços funcionais (inferidos da composição da comunidade) numa leitura legível para o utilizador final. Trabalho de **definição**; implementação no Claude Code.
**Público-alvo:** produtor agrícola **e** técnico (registo em camadas).
**Estatuto:** definição fechada, salvo pendentes dependentes de dados (fim do documento).

---

## 1. Princípios transversais

1. **Natureza do dado.** Indicadores de *potencial* funcional inferido da composição da comunidade (sequenciação genética), **não** medição química/atividade do solo.
2. **Comparação vs. interpretação.** O match entre amostras (vizinhos mais próximos) assenta **só na composição** (Bracken); os traços **não** entram na similaridade. Os traços são apenas a camada de leitura.
3. **Régua na fração `true`.** Para cada traço discreto, a grandeza usada (régua e tabela) é a fração `true` — % da comunidade que **tem** a função. `false`, `no_majority` e `unannotated` não são exibidos nem usados.
4. **Leitura comparativa.** Grupos funcionais → régua relativa (baixo/moderado/alto, percentis dinâmicos da coleção); ótimos ambientais → escala absoluta com banda.
5. **Regra dura — descreve, não recomenda.** Descreve estado microbiano; nunca recomendação agronómica.
6. **Seleção de traços.** Dos 2650 traços da base de referência, retêm-se os **370** das listas 1+2 (relevantes/incertos); os 2280 sem relevância são **excluídos na fase offline** (ver `classificacao_tracos.csv`).

## 2. Convenção de linguagem (camadas)

Linguagem corrente (produtor) + termo técnico entre parênteses/detalhe (técnico). Um só texto serve ambos. Não requer seletor de modo.

## 3. Fundamentação da estrutura de grupos

Estrutura validada contra a literatura de indicadores funcionais microbianos de saúde do solo. Pontos confirmados: C/N/P/S como ciclos centrais (fosfatases = indicador de P; α-glucosidase/quitinase = C/N); FAPROTAX confirma quimio-heterotrofia, redução de nitrato e fixação de azoto como funções dominantes; oxidação de ferro e vias do enxofre como funções próprias; metilotrofia/metanotrofia como categorias autónomas; necessidade de **separar amonificação de nitrificação** (processos distintos, a modelar em separado).

**Limitação registada:** a literatura usa também indicadores de **patogenicidade/supressividade**; estes dados não os suportam (só hemólise, marginal), pelo que essa dimensão **não é coberta** — não se cria grupo vazio.

## 4. Cabeçalho de *framing* (texto literal)

**Linha visível (permanente):**
> Indicadores do potencial microbiano do solo, inferidos da composição da comunidade. Leitura comparativa, não medição.

**Bloco "Como interpretar" (recolhível):**
> Cada indicador resulta da composição microbiana da amostra, estimada por sequenciação genética — reflete o *potencial* da comunidade, não uma medição direta da química ou da atividade do solo. Os rótulos (baixo / moderado / alto) são relativos à coleção de amostras analisadas: "alto" significa acima do habitual nas parcelas semelhantes, não um valor absoluto. Esta ferramenta descreve o estado microbiano; não constitui recomendação agronómica.

## 5. Grelha de grupos (19 grupos/subgrupos) e frases-síntese

Frases em camadas, parametrizadas por baixo/moderado/alto (régua relativa), salvo grupo 11 (absoluto) e grupo 13 (genérico).

### Ciclo do azoto (subdividido)

**1a. Fixação de azoto** *(termo: diazotrofia, nitrogenase)*
- Baixo: "Poucos microrganismos capazes de captar azoto do ar — habitual, é sempre uma minoria (fixação de azoto abaixo do habitual)."
- Moderado: "Capacidade de captar azoto do ar dentro do habitual."
- Alto: "Mais microrganismos do que o habitual capazes de captar azoto do ar (fixação de azoto elevada)."

**1b. Nitrificação** *(termo: nitrificação, oxidação de amónia)*
- Baixo: "Conversão de amónio em nitrato abaixo do habitual."
- Moderado: "Conversão de amónio em nitrato dentro do habitual."
- Alto: "Conversão de amónio em nitrato acima do habitual — nitrato mais disponível, mas também mais sujeito a lixiviação."

**1c. Desnitrificação / redução de nitrato** *(termo: desnitrificação, redução de nitrato/nitrito)*
- Baixo: "Poucos sinais de perda de azoto por via gasosa (desnitrificação abaixo do habitual)."
- Moderado: "Sinais de perda gasosa de azoto dentro do habitual."
- Alto: "Sinais acima do habitual de perda de azoto por via gasosa — associada a zonas com pouco oxigénio (desnitrificação elevada)."

**1d. Amonificação / mineralização de azoto** *(termo: amonificação, urease)*
- Baixo: "Libertação de azoto a partir de matéria orgânica abaixo do habitual."
- Moderado: "Libertação de azoto a partir de matéria orgânica dentro do habitual."
- Alto: "Libertação de azoto a partir de matéria orgânica acima do habitual."

### Oxigénio e carbono

**2. Arejamento do solo** *(termo: equilíbrio aeróbios/anaeróbios)*
- Baixo: "Circulação de ar abaixo do habitual — compatível com solo mais compactado ou húmido."
- Moderado: "Circulação de ar dentro do habitual."
- Alto: "Boa circulação de ar — solo bem arejado e drenado."

**3a. Decomposição — fibra e polímeros vegetais** *(termo: degradação de celulose, lenhina, quitina, xilano, amido)*
- Baixo: "Capacidade de decompor fibra vegetal abaixo do habitual."
- Moderado: "Capacidade de decompor fibra vegetal dentro do habitual."
- Alto: "Capacidade de decompor fibra vegetal acima do habitual."
- *Nota local:* a decomposição de celulose e lenhina é feita sobretudo por fungos, invisíveis a este método; um valor baixo não significa ausência.

**3b. Decomposição — proteínas** *(termo: proteólise — caseína, gelatina, colagénio)*
- Baixo: "Capacidade de decompor matéria proteica abaixo do habitual."
- Moderado: "Capacidade de decompor matéria proteica dentro do habitual."
- Alto: "Capacidade de decompor matéria proteica acima do habitual."

**3c. Decomposição — compostos recalcitrantes / poluentes** *(termo: degradação de aromáticos, hidrocarbonetos)*
- Baixo: "Poucos sinais de capacidade para degradar compostos persistentes ou poluentes."
- Moderado: "Capacidade de degradar compostos persistentes dentro do habitual."
- Alto: "Capacidade acima do habitual para degradar compostos persistentes ou poluentes (potencial de biorremediação)."

**3d. Decomposição — geral** *(termo: quimio-heterotrofia, fermentação)*
- Baixo: "Atividade geral de decomposição abaixo do habitual."
- Moderado: "Atividade geral de decomposição dentro do habitual."
- Alto: "Atividade geral de decomposição acima do habitual."

### Enxofre, metano, metais

**4. Enxofre / sinais de anoxia** *(termo: ciclo do enxofre, metanogénese)*
- Baixo: "Sem sinais relevantes de zonas sem oxigénio (esperado em solo arejado)."
- Moderado: "Alguns sinais de microambientes sem oxigénio."
- Alto: "Sinais acima do habitual de zonas sem oxigénio — compatível com encharcamento ou compactação."

**5. Metilotrofia / metanotrofia** *(termo: oxidação de metano e metanol)*
- Baixo: "Poucos microrganismos que consomem metano ou metanol."
- Moderado: "Consumo de compostos de um carbono dentro do habitual."
- Alto: "Mais microrganismos do que o habitual que consomem metano/metanol — relevante para mitigar emissões de metano."

**6. Ferro e manganês (redox)** *(termo: redução/oxidação de Fe e Mn)*
- Baixo: "Poucos sinais de transformação de ferro/manganês."
- Moderado: "Transformação de ferro/manganês dentro do habitual."
- Alto: "Sinais acima do habitual de transformação de ferro/manganês — indicador de condições de redução, associadas a encharcamento."

### Nutrientes e interação com a planta

**7. Fósforo** *(termo: fosfatases — mineralização de P)*
- Baixo: "Capacidade de disponibilizar fósforo abaixo do habitual."
- Moderado: "Capacidade de disponibilizar fósforo dentro do habitual."
- Alto: "Capacidade de disponibilizar fósforo acima do habitual — mineralização ativa de fósforo do solo."

**8. Promoção de crescimento vegetal (PGP)** *(termo: auxina, sideróforos, ACC-deaminase, biocontrolo)*
- Baixo: "Poucos sinais de microrganismos promotores de crescimento vegetal."
- Moderado: "Presença de promotores de crescimento dentro do habitual."
- Alto: "Presença acima do habitual de microrganismos promotores de crescimento — produção de hormonas vegetais, captação de ferro e potencial de biocontrolo."

**9. Carbono autotrófico / fototrofia** *(termo: fixação de CO₂, fototrofia, RuBisCO)*
- Baixo: "Poucos microrganismos que fixam carbono diretamente."
- Moderado: "Capacidade de fixação de carbono dentro do habitual."
- Alto: "Mais microrganismos do que o habitual capazes de fixar carbono diretamente (fototrofia/quimioautotrofia)."

### Resiliência, ambiente, estrutura

**10. Resistência a stress** *(termo: resiliência — esporulação, mobilidade, tolerâncias)*
- Baixo: "Marcadores de resistência a condições adversas abaixo do habitual."
- Moderado: "Marcadores de resistência dentro do habitual."
- Alto: "Marcadores de resistência acima do habitual — comunidade mais preparada para seca ou perturbação."

**11. Ótimos ambientais da comunidade** *(escala absoluta, não relativa)*
- **pH:** "A comunidade microbiana é típica de solos de reação neutra (pH ótimo predito ≈ 7,2)."
  - Bandas: ácido < 6,0 · ligeiramente ácido 6,0–6,5 · neutro 6,5–7,5 · alcalino > 7,5.
- **Salinidade:** "Comunidade adaptada a baixa salinidade — sem sinais de stress salino (salinidade ótima predita ≈ [valor])."
  - Bandas: baixa · moderada · alta. *(cortes por afinar — pendente)*
- **Temperatura:** "Comunidade mesófila — adaptada a temperaturas moderadas (temperatura ótima predita ≈ [valor] °C)."
  - Bandas: psicrófila · mesófila (~20–40 °C) · termófila. *(cortes por afinar — pendente)*
- *Ressalva:* parecem medições, mas são o ótimo *inferido* da comunidade, não o valor medido no solo.

**12. Agregação / armazenamento** *(termo: exopolissacáridos, PHB/PHA)*
- Baixo: "Produção de substâncias que agregam o solo abaixo do habitual."
- Moderado: "Produção de substâncias que agregam o solo dentro do habitual."
- Alto: "Produção acima do habitual de substâncias que ajudam a estruturar o solo e a reter água."

**13. Metabolismo geral** *(grupo residual — frase genérica)*
- Baixo / Moderado / Alto: "Outros marcadores metabólicos da comunidade, sem leitura agronómica específica; apresentados a título informativo."
- *(Frase única, não parametrizada; estes traços têm relevância marginal e existem para completude. Visíveis também na tabela técnica.)*

## 6. Régua relativa — regra de cálculo

- Grandeza: fração `true` de cada traço.
- Cortes (percentis) **calculados dinamicamente** em tempo de execução, sobre a coleção embebida.
- **Amostra consultada excluída** da distribuição de referência (evita auto-contaminação).
- *Caveat:* dinâmico ≠ robusto; com poucas amostras a leitura é provisória.

## 7. Tabelas técnicas (vista detalhada)

Vistas separadas da síntese, para o técnico. Valores crus, sem rótulos. Os traços discretos e os numéricos são grandezas distintas (fração vs. valor com unidade) e ficam em **duas tabelas separadas**.

### Tabela A — Traços funcionais (discretos)

Duas colunas:
- **Indicador** — nome do traço.
- **% da comunidade** — fração `true`, isto é, percentagem da comunidade total que tem a função (mesmo quando minoritária). Denominador = comunidade total (não apenas os anotados).

### Tabela B — Ótimos ambientais (numéricos, grupo 11)

Duas colunas:
- **Indicador** — pH ótimo, salinidade ótima, temperatura ótima.
- **Valor estimado** — valor inferido, com unidade (ex.: 7,2 · 32 °C). Não é fração nem percentagem.

### Alterações ao HTML atual

Header atual: `Trait | Type | Inferred state | Coverage (annotated)`.
- `Trait` → **Indicador**.
- `Type` → **removida**.
- `Inferred state` → na Tabela A passa a **% da comunidade** (fração `true`); na Tabela B é **Valor estimado**.
- `Coverage (annotated)` → **removida** (aspeto demasiado técnico; a camada de "confiança" derivada da cobertura já fora descartada).
- Os traços numéricos (pH/salinidade/temperatura) saem da tabela dos discretos e passam para a Tabela B própria.

## 7-bis. Interface e textos (pt-PT)

Toda a interface em **português de Portugal**.

**Título e subtítulo:**
- Título: **AgroBiome Digital — Perfil Funcional do Microbioma do Solo**
- Subtítulo: **Inferir traços funcionais por comparação com amostras de solo de vinha**

**Rótulos e mensagens:**
- "Neighbors (k)" → **Amostras semelhantes a mostrar** (sem o "k").
- Botão "Analyze" → **Analisar**.
- Mensagem de estado "Done. Nearest neighbor: sample 10 (Bray-Curtis = 0.0001). 398 reference genera matched." → **Concluído. Amostra mais semelhante: amostra 10 (Bray-Curtis = 0,0001). 398 géneros de referência correspondidos.** (manter "Bray-Curtis"; usar vírgula decimal.)

**Tabelas:**
- Tabela A: título **Indicadores funcionais** (sem o sufixo do vizinho/distância).
- Tabela A: **omitir as linhas cujo valor de "% da comunidade" seja 0%**.
- Tabela B: título **Ótimos ambientais**.

**Ordem dos grupos / layout:**
- O grupo 11 (Ótimos ambientais) passa a ser **o último** da secção sintetizada (resolve a quebra visual provocada pelo seu bloco largo).
- Estética: refinar espaçamento, hierarquia tipográfica e consistência dos cartões, **mantendo o layout atual** (melhoria genérica, sem redesenho).

**Nota de evolução (não implementar agora):**
- A base de dados passará a ter **metadados por amostra** (ex.: localização). Esses campos deverão futuramente ser exibidos algures na interface. A arquitetura deve prever a sua existência, mas **não se implementa nesta fase**.

## 8. Pendentes (dependentes de dados)

1. **Cortes de percentil (régua):** resolvidos dinamicamente; qualidade escala com nº de amostras.
2. **Bandas de salinidade e temperatura (grupo 11):** dependem da escala do *pipeline*; cortes do pH são robustos, os outros dois por ancorar.

# Changelog — AgroBiome Digital

Registo das versões do entregável. Datas em ISO (AAAA-MM-DD).

## [v0.2] — 2026-06-29

### Adicionado
- Faixa de financiamento PRR (logótipos PRR · República Portuguesa · Financiado
  pela União Europeia — NextGenerationEU) e texto de financiamento, visíveis na
  aplicação e na exportação PDF (`app/assets/barra_logos_prr.png`).
- Cartão "Base de dados de referência" na aplicação, com números derivados
  dinamicamente dos dados (amostras, géneros, indicadores, grupos).
- Formulário opcional de **metadados agronómicos** no painel de upload (nome/parcela,
  região, cultura, casta, data, tipo de solo, modo de produção, coberto vegetal,
  rega, fertilização recente, observações), com cartão "Identificação da amostra"
  no relatório.
- **Relatório PDF institucional**: capa com identificação e financiamento PRR,
  resumo executivo automático, cabeçalho corrente e bloco "Metodologia e limitações".
- **Exportação de dados em JSON** estruturado (metadados, metodologia, correspondência,
  diversidade, ótimos ambientais, indicadores funcionais e ressalvas).
- `requirements.txt` com as dependências Python do pipeline.
- README: secções "Estado do repositório" e "Reprodutibilidade"; nota sobre a
  diferença entre o registo histórico de amostras e a coleção ativa.

### Corrigido
- README: referência à memória descritiva passa a apontar para o ficheiro `.pdf`
  existente (antes `.docx`).
- Cartão de referência: removidas notas/ressalvas duplicadas e simplificado o título.

## [v0.1] — piloto inicial
- Aplicação web de página única para análise de relatórios Bracken 16S de solo
  de vinha: comparação composicional (Bray-Curtis), inferência de potencial
  funcional por proximidade, visualização PCoA, grupos funcionais, ótimos
  ambientais e exportação PDF.
- Pipeline bioinformático (Bracken → perfil → traços → matrizes → diversidade
  beta → JSON estáticos) e base de referência de amostras de solo de vinha.
- Memória descritiva técnica e especificação da camada interpretativa.

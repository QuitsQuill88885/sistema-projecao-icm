## A cifra ficou limpa, e a sugestão passou a enxergar o acervo inteiro

Esta versão junta duas coisas grandes que estavam prontas mas presas aqui.

### 3.963 linhas de letra consertadas na cifra

A folha do músico mostrava `Jelsus`, `velrei`, `precilosas`, `santildade` — uma
letra intrusa enfiada no meio da palavra. Montei um ambiente de OCR de verdade
para reler as páginas na placa de vídeo e descobri que **não adiantava**: o lixo
está impresso no próprio PDF do livro digital. O motor de OCR lê `velrei` porque
é `velrei` que está desenhado ali.

Quem consertou foi outra coisa: **saber que `velrei` não é palavra e `verei` é.**
Três juízes independentes decidem cada troca — um dicionário de português de
416.782 palavras, o vocabulário do próprio hinário, e a exigência de que sobre
**uma única** palavra possível. Onde sobra mais de uma (`Iindo` pode virar `indo`
ou `lindo`), nada é tocado.

E ainda uma corroboração por cima: **3.452 linhas tiveram toda troca confirmada
pela letra que sobe no telão**, e as 90 que só o dicionário apoiava foram
recusadas — ali estavam `a- le- lui- a` virando `a- le- ui- a` e o `SIb` virando
`Slb`.

- linhas corrompidas: **3.992 → 1.688**
- o que o músico vê quebrado: **2.595 → 642** (−75%)
- louvores com pelo menos uma linha ruim: **1.752 → 1.160**
- acordes no acervo: **116.878, intactos** — cada caractere removido levou o
  recálculo da coluna de todos os acordes à direita dele (4.102 reposicionados)
- os marcadores dourados do telão: **2.642, intactos**

### A sugestão de louvores enxergava só 2.459 dos 2.574

O índice pontua por vetor de palavras, e o arquivo de vetores estava parado em
10/08. Os louvores acrescentados depois existiam na lista mas não tinham vetor —
e **louvor sem vetor nunca é sugerido, sem dar erro nenhum.**

- **Avulsos 2026: 0 de 113 apareciam. Agora 90.**
- "Meus louvores": 0 de 2 → 2 de 2. O `ELE É O LEÃO DA TRIBO DE JUDÁ` saiu de
  invisível para **280 versículos**, começando por Gênesis 49:9 (*"Judá é um
  leãozinho"*), que é a raiz da figura.
- louvores distintos que aparecem em alguma sugestão: **1.540 → 1.625**

### A tipologia dos obreiros entrou

O programa usava um resumo de 131 figuras. O material dos obreiros, com **307**,
estava guardado sem ser usado. Conferido antes de ligar: é superconjunto exato —
as mesmas 131 com significado idêntico, mais 178.

Prova no caso que deu origem à ferramenta: **Deuteronômio 24:4** passou a trazer
`QUEM PODERÁ` no trio.

### A terceira vaga da sugestão voltou

A mesma peça existe na Coletânea de 2018 e na Antiga — 867 louvores têm cópia. O
índice guardava as duas, e em 58% dos versículos uma das três vagas ia embora no
título repetido. Agora **31.094 de 31.102 versículos entregam três louvores
diferentes.**

### E as Propriedades do Windows pararam de mentir

O `Instalar-o-Sistema.exe` mostrava **2.8.1** nas Propriedades desde sempre,
mesmo instalando outra versão. O instalador, o baixador e o programa agora
carimbam a mesma versão, no texto e na tupla.

## Como atualizar

Baixe o **Instalar-o-Sistema.exe** e instale por cima. Suas configurações e seus
louvores próprios não são tocados.

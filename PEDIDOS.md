# Sistema — tudo o que foi pedido

Levantamento de tudo que o Samuel pediu desde o começo, o que já está pronto e o que falta.
Atualizado em 09/08/2026 · versão atual **1.3.0**

---

## ✅ PRONTO E TESTADO

### Louvores
- [x] Coletânea completa da ICM — **2.459 louvores**
- [x] Busca por número, nome **ou trecho da letra**
- [x] Busca funciona **com ou sem acento** ("coracao" acha "CORAÇÃO")
- [x] Numeração: avulsos = **AV**, contracapa = **CC** (primeiro da lista)
- [x] Marcadores `CORO`, `FINAL`, `BIS`, `CORO (2X)` como rótulo amarelo
- [x] `(BIS)` e `(2X)` amarelos **no meio da linha** (igual Maanaim)
- [x] Palavra **"fim"** no canto do último slide
- [x] Duplo-clique no louvor manda para a Lista de Projeção
- [x] Slides longos paginados (máx. 8 linhas, padrão Maanaim)
- [x] Linhas quilométricas quebradas na vírgula
- [x] Todos os slides do mesmo louvor no **mesmo tamanho de letra**

### Bíblia
- [x] Almeida Revista e Corrigida completa
- [x] 1 clique projeta · 2 cliques guarda na lista
- [x] ▶ segue a leitura sozinho, cruzando capítulos e livros
- [x] ◀ volta respeitando a ordem escolhida e depois retrocede sozinho
- [x] Vários versículos **juntos na mesma tela** (como o Glorifica)
- [x] Marcar ✓ projeta ao vivo, sem apertar botão
- [x] Um versículo marcado sozinho = versículo normal (não estica)

### Projeção
- [x] Visual **1:1 com a ICM** (conferido contra fotos da transmissão)
- [x] Fonte **Futura Heavy** — a mesma do Maanaim
- [x] Auto-ajuste: nada é cortado no telão
- [x] Dois estilos: **Padrão** e **Mapa-múndi**
- [x] Fade suave entre slides
- [x] Tela de espera automática entre louvores
- [x] Congelar (o telão segura enquanto você prepara)
- [x] Detecta o projetor e joga tela cheia nele sozinho
- [x] Setas do teclado funcionam mesmo com a projeção na frente
- [x] Cursor some sozinho na projeção

### Outros
- [x] Timer, Relógio (com data por extenso), Texto e Avisos
- [x] Avisos que se montam sozinhos pelos cultos da igreja
- [x] Aviso do **próximo culto** considera a hora de agora
- [x] Fundos por categoria + adicionar os seus
- [x] Tela de espera escolhida continua valendo ao reabrir
- [x] **Slides de PowerPoint e PDF** da Escola Bíblica
- [x] Menu ☰ com editor de louvores, dados da igreja e restaurações
- [x] Apresentação de boas-vindas na primeira vez

### Programa
- [x] **.EXE de verdade**, sem navegador, com janela e ícone próprios
- [x] Abre em **~2,6 segundos** (era 8) — instalação em pasta, sem descompactar
- [x] Instalador com atalhos e pastas do usuário
- [x] Configurações sobrevivem à atualização
- [x] Janela centralizada, tamanho civilizado
- [x] Ícone do Sistema (não mais o do Python)
- [x] **Nenhuma janela preta de CMD piscando** (netsh, LibreOffice e abertura)
- [x] **Barra de carregamento que anda de verdade** — 9 marcos reais + rastejo
      entre eles; é texto dourado escrito sobre o trilho, não pintura parada
- [x] Splash sem o "Initializing" em inglês e com "Projeção" acentuado
- [x] Executável se identifica como **"Sistema"** no firewall e nas propriedades
- [x] Instalador fixa no **menu Iniciar** e cria atalho na Área de Trabalho

### Controle pelo celular
- [x] Página no celular, sem instalar nada — QR code no menu ☰
- [x] Funciona pelo **hotspot do celular** ou wi-fi da igreja, sem internet
- [x] Escolher louvor, slide, livro/capítulo/versículo
- [x] Avançar, voltar, tela de espera, congelar, tamanho da letra
- [x] **Prévia ao vivo** do telão no celular
- [x] Bíblia em passos (livro → capítulo → versículo), sem rolagem infinita

#### Auditoria do celular — 18 defeitos confirmados, 18 corrigidos
Seis frentes auditaram o celular contra o computador; um cético derrubou 2 achados
falsos. Os que sobraram, todos corrigidos:
- [x] **Congelado mentia**: a prévia continuava mudando enquanto escrevia
      "CONGELADO — o telão não muda". O POST de `/api/tela` estava FORA do
      `if (!est.freeze)`. Agora guarda `est.telaCongelada` e publica esse quadro.
- [x] **Descongelar não devolvia a imagem** na janela própria (.exe): o código só
      tratava `projWin`, faltava o `CANAL`
- [x] **Janela do telão fechada deixava o celular "AO VIVO" pra sempre** — o vigia
      tinha `!nativo()`, que exclui justamente o .exe. Novo `Ponte.projecao_aberta()`
- [x] Celular não percebia o computador parar de responder → `ESTADO["ts"]` + `idade`
- [x] Projeção fechada: o rodapé do celular agora apaga em vez de fingir que pegou
- [x] Prévia baixava o fundo inteiro 1,4×/s → `GET /api/tela?n=` devolve só o número
      quando nada mudou (bateria e hotspot da igreja agradecem)
- [x] Grade de slides nunca esvaziava (o `if` recusava `slides: 0`)
- [x] Celular não mostrava qual louvor/slide está no ar → publica `louvor/slide/slidepp`
- [x] Congelar demorava até 2,5s e o 2º toque desfazia → acende na hora e manda o
      ALVO (`{on}`), não "inverta"
- [x] Botão Voltar da Bíblia sumia ao rolar → `.trilha` virou `position:sticky`
- [x] **Não dava pra juntar versículos pelo celular** → segurar o dedo guarda na lista
- [x] **Só aparecia o número do versículo** → faixa com o texto, pra conferir antes
- [x] Prévia comia 59% da tela → toque recolhe (fica guardado no celular)
- [x] Voltar um passo jogava a rolagem pro topo → devolve onde parou
- [x] Livro atual não ficava marcado na lista (era código morto)
- [x] Livro de um capítulo só (Judas, Obadias…) pula direto pros versículos
- [x] Busca de livro por abreviação: `sl`→Salmos, `gn`→Gênesis, `1jo`→1 João

---

## ⏳ A FAZER — o que você apontou por último

### Erros a corrigir
- [ ] **Barra de estado desatualizada** — dizia "Em espera" projetando 2 versículos
- [ ] Brilho vermelho em volta da prévia ficou confuso
- [ ] **Troca de estilo (Padrão ↔ Mapa-múndi) não atualiza os avisos**
- [x] **Lista de Projeção não rolava e vazava para fora da janela** — os
      versículos guardados ficavam invisíveis. Causa: `#painel>*{flex-shrink:0}`
      tem ID e vencia a classe `.fila-itens` por especificidade, então a lista
      não podia encolher. Medido: terminava em y=961 numa janela de 700.
      Agora termina em 690, rola, e tem barra de rolagem visível.

### Melhorias pedidas
- [ ] **Remover o ✕** (desligar telão) — ninguém vai usar isso na igreja
- [x] **Botão "Espera" eliminado** — "Parar de projetar" já devolve a tela de
      espera, então era botão repetido ocupando espaço lá em cima
- [ ] Menu de baixo (frente/trás/A+/A−) **bem menor e melhor desenhado**
- [ ] Achar **jeito melhor de juntar versículos** (o ✓ não ficou bom)
- [ ] Aproveitar o **espaço vazio do meio** em vez de espremer tudo à direita
- [ ] Louvor escolhido precisa **mostrar que está selecionado** na lista da esquerda
- [ ] **Duplo-clique num slide** deve mandar para a Lista também
- [ ] Lista de Projeção: louvores e versículos juntos, de forma elegante
- [ ] Aba Texto: **tirar o botão "Projetar"** (já atualiza ao vivo)
- [ ] Menus internos menores em geral — "as pessoas não são cegas"

---

## 💤 GUARDADO PARA DEPOIS

- [ ] Numeração dupla 2018 / antiga (ex.: "204 / 1103") com opção de mostrar ou esconder
- [ ] Importar louvores do Glorifica (.xbY / TXT / Telegram) para pegar correções
- [ ] Aplicar os fundos novos no Glorifica antigo
- [ ] Publicar no GitHub (repositório local já pronto, falta só o login)
- [ ] Levar todas as funções do computador para o celular (falta Lista, Fundos, Texto, Timer)

---

## Como testar sem se enganar

1. O **.exe carrega uma cópia própria** dos arquivos. Editar o código e testar no exe
   não funciona — rode `python sistema.py` na pasta do projeto, ou recompile.
2. Ao depurar o celular: qualquer `fetch('/api/comandos')` feito à mão **rouba o comando**
   do aplicativo. Mande o comando de fora (script) e confira por `/api/estado`.
3. O navegador guarda os arquivos em cache. Se algo não mudar, force recarregar.

---

## 📌 PEDIDOS ABERTOS — registro para não se perder

### Bugs que você apontou e ainda NÃO estão resolvidos
- [x] **Busca do CELULAR não está ranqueada.** Corrigi só no computador. Procurar
      "Resplandece" no celular ainda traz louvores da letra antes do próprio
      "RESPLANDECE, Ó JERUSALÉM". Mesma regra do computador: título igual >
      título que começa > título que contém > palavras soltas no título > letra.
      Ignorar acento E pontuação ("resplandece jerusalem" acha "RESPLANDECE, Ó JERUSALÉM").
- [x] **A+ / A− pelo celular não funciona.**
- [ ] **Caixa de busca do celular encavala a lista** (item cortado atrás do campo).
- [x] **Lista de Projeção no celular** — VER a lista e ADICIONAR louvores/versículos.
      Palavras dele: é mais importante que controlar a projeção, porque o grupo
      de louvor precisa montar o que vai ser projetado.
      (comandos addlouvor / tirardalista / irpara já existem no computador)

### Ideias novas, ainda não começadas
- [x] **Histórico e painel de louvores.** Guardar o que foi projetado em cada
      culto, com o TEMPO que cada louvor ficou no ar. Painel mostrando: mais
      cantados, mais tempo projetados, escolhidos por período (mês, últimos meses).
- [x] **Ligação Bíblia ↔ louvor.** Ao abrir uma passagem, sugerir louvores cuja
      MENSAGEM combina. Exemplos dele: Isaías 60:1 ("levanta-te, resplandece")
      → "Resplandece, ó Jerusalém"; Neemias (reconstrução) → louvor de obra e
      reconstrução. É análise do conteúdo da letra, não busca por palavra.
- [ ] **Categorias do culto da ICM.** Classificar os louvores por função no
      culto: clamor, dedicação, glorificação etc. O culto sempre começa por um
      louvor de clamor. (ele ia continuar a explicação — confirmar a lista completa)

- [ ] **A página de reset / "voltar às configurações de fábrica" está bagunçada.**
      Pedido dele em 22/08/2026: são várias opções soltas, sem organização —
      refazer a tela inteira, deixar bonita e clara (o que cada reset apaga, e
      o que NÃO se perde). NÃO é urgente; ele mesmo disse "é só pra anotar,
      a gente faz outro dia".

### Decisões já tomadas (para não reabrir)
- Identificação de coletânea: **agrupada por cabeçalho** na busca por NÚMERO;
  ranqueada por proximidade na busca por TEXTO. Sem sigla para decorar.
- Instalador: um só programa. Com a pasta `Conteudo` do lado = completo;
  sem ela = enxuto.
- GitHub: repositório PÚBLICO só com código.
  https://github.com/QuitsQuill88885/sistema-projecao-icm
- Fonte Futura: fica no pacote que ele distribui (decisão dele). Não vai para
  o repositório público.

---

## 🎸 PEDIDOS DE 30/08/2026 — CIFRAS (anotado com ele falando; nada começado)

Ele pediu explicitamente para eu **registrar tudo em MD**, porque a conversa é
longa e um dia o chat vai ter de ser trocado: *"se você não montar um histórico
de tudo que eu tenho falado, você vai ficar maluco"*.

- [ ] **As notas flutuam no lugar errado.** A posição do acorde sobre a sílaba
      está saindo torta em bastante louvor. É o defeito mais grave da cifra
      hoje — o instrumentista lê a nota em cima da sílaba errada. (A coluna
      vem do OCR, no campo `a: [[coluna, acorde], ...]`.)
- [x] **RESTAURAR o traço separador de nota.** Existia e sumiu: um tracinho
      **bem delicado** no meio das letras, mostrando exatamente onde a nota
      troca. Palavras dele: *"não fica ridículo, mostra exatamente onde troca
      nota"*. Ele quer de volta.
- [ ] **Mapear os louvores pelos vídeos do YouTube**, do jeito que são
      realmente cantados e tocados lá. Motivo concreto: **"Tenho uma Candeia"
      (CIA 143)** está tão mal escrito na cifra que ele, com a coletânea
      oficial original 100% na frente, acha feio tocar como está escrito.
      *"Nosso sistema vai ficar melhor do que as próprias coletâneas."*
- [ ] **Introduções.** Ele vai mandar as introduções de alguns louvores.
- [ ] **Enarmonia maluca.** Tem cifra com um monte de bemol/sustenido sem
      necessidade ("aquela bolinha maluca lá, nada a ver"). Ele vai mandando as
      correções para notas mais coerentes, louvor a louvor.

### ✅ Feito nesta rodada (v2.8.0)
- [x] Acordes impossíveis corrigidos: `F#0 C0 B0 F0` (o **grau** foi escaneado
      como ZERO — provado pela vizinhança: `B°→E7→Am`, `F#°→G`), `D71→D7`,
      `A18→A`, `A1→A`, `Bmm→Bm`. Mais 227 normalizações de `º` (ordinal) para
      `°` (grau), que conviviam no mesmo acervo.
- [x] **A+ / A− pelo celular** (era o item aberto lá de cima) — agora com o
      mostrador de tamanho que só existia no computador.
- [x] **Caixa de busca do celular encavalando a lista** — resolvido com
      `scroll-padding-top` medido no ar, não chutado.

### Buscador solto (fora do programa) — pedido de 30/08/2026
- [x] **Buscador dos 2.459 louvores como página única**, com a MESMA engine do
      Sistema (número por igualdade, busca pelo som, trecho da letra). Existe em
      duas formas: artifact publicado (link fixo) e **arquivo `louvores.html` de
      1,6 MB que roda OFFLINE** — ele salva em Arquivos no iPhone e abre no
      Safari, sem internet e sem Claude. Palavras dele: *"é ouro puro"*.
- [ ] **O mesmo, para as CIFRAS.** Ele pediu na sequência: um buscador de cifras
      que dê para baixar e abrir no iPhone. *"Ajuda de um jeito que você não tem
      ideia."* Mesmo molde do de louvores: um HTML sozinho, sem servidor.
- [ ] Ideia dele que ficou de fora: publicar o buscador no GitHub Pages.
      **Ele mesmo cancelou** ("a ideia foi horrível, desconsidere") depois que
      levantei que a letra é conteúdo da igreja e repositório público a deixaria
      indexada no Google. Fica o registro para não reabrir por engano.

### 30/08/2026, 4h — diagnóstico das notas flutuando (tarefa programada)
Investigado, **nada alterado no acervo**. O detalhe completo está no
`CONTINUA-AQUI.md`; o resumo:
- **Medido:** 11.823 acordes (13,2%) do Nível 2 e 5.884 (8,1%) do Nível 1 caem
  **depois do fim da letra** — e essa conta só pega os óbvios.
- **Causa achada:** `Conhecimento\cifras_refazer\cifras_python.py` (~linha 480)
  guarda o **texto de uma leitura** e as **colunas de outra**, escolhendo pelo
  critério "quem tem MAIS acordes vence". Coluna só vale junto do texto em que
  foi medida.
- **Conserto:** `t` e `a` andam sempre em par; desempate pela confiança/caixa do
  OCR, não pela contagem. As caixas já estão em `leitura_ouro/` — **não precisa
  de GPU nem de reprocessar PDF**.
- **O tracinho separador nunca existiu no nosso sistema** (conferido no git):
  é o da coletânea impressa. Dá para fazer com marca de largura zero, mas só
  DEPOIS do alinhamento — senão aponta o lugar errado com precisão.

### 30/08/2026 — conserto do alinhamento: 186 linhas feitas, e a parede
- [x] **1.558 linhas consertadas** em três rodadas (186 + 1.083 + 289),
      **3.351 acordes** de volta para cima da sílaba certa. Fonte: os
      `refeito_*.json`, que já existiam e são o único lugar onde texto e coluna
      nasceram juntos; o casamento é por `difflib`, caractere a caractere,
      **tudo local, sem rede**. Nenhum acorde perdido (89.326 e 72.716 seguem
      iguais) e nenhuma notação alterada — foi conserto de POSIÇÃO.
      Fora da letra: `11.823 → 11.617` e `5.884 → 5.815`.
      A melhor prova de que o método está certo: **3.411 das 4.494 linhas
      casadas já estavam no lugar** — ele concorda com o banco onde o banco
      acerta, e só mexe onde há divergência real (mais de 2 caracteres).
      Ainda **não publicado** — precisa de release para chegar na igreja.
- [ ] **Os outros 8.857 quebrados exigem REEXTRAIR os PDFs.** Medido: 4.007 são
      de louvores que não estão nos refeitos, e 4.850 têm no banco acordes que
      nem pertencem àquela linha (é o próprio defeito). Adotar o refeito inteiro
      chegaria a 9% e **apagaria 732 acordes para ganhar 243** — recusado.
- [ ] **O critério "quem tem mais acordes vence" está em DOIS lugares** e
      precisa cair nos dois: `melhor_a()` e o `juntar()` do `cifras_python.py`
      ("só troca se a quantidade de acordes válidos aumentou").
- [ ] **Falta o PDF de origem do Nível 1** — só existem os 3 (Nível II,
      Cifras 2025, Avulsos 2024) em `Pacote completo\PDFs originais`.

### 30/08/2026 — reextração: três descobertas que mudam o jogo
Trabalho completo em `Conhecimento\cifras_refazer\reextracao_2026-08-30\LEIA-ME.md`.
- [x] **O PDF do Nível 1 existe** — `Coletanea Cifrada 2018 Nivel I.pdf`, 398
      páginas, texto limpo, em `C:\Users\Emanuel\Downloads`. Nunca esteve na
      pasta do projeto; era o que faltava para metade do acervo.
- [x] **O Nível II que usávamos é o pior que existe** — é escaneado, a camada de
      texto é o próprio OCR sujo. Em Downloads há a edição DIGITAL
      (`Coletanea cifrada Nivel 2 - ICM.pdf`), que sai limpa.
- [x] **O tracinho separador EXISTE na fonte, como caractere `|`** — e marca
      onde cada acorde entra. Medido: em **3.865 linhas (47,8%) do Nível 2 a
      contagem de `|` bate exatamente com a de acordes** → posição EXATA, sem
      interpolação. É a separação de nota que ele pediu de volta.
- [x] **Segundo erro achado:** a largura do caractere era fixa em 0,52 para
      todos os livros; medida dá 0,4877 / 0,4717 / **0,6368**. No Avulsos são
      22% de erro — ~4 caracteres fora numa linha de 20.
- [ ] **Falta:** leitura própria por livro (Nível 2 pelos `|`; Nível 1 pulando a
      linha de solfejo), a fusão com o banco, e OCR na placa para a Coletânea
      2011, que é imagem pura.

### 30/08/2026 — o tracinho é informação musical (explicação dele)
- [x] **Medida a leitura nova do Nível 2 sob o critério certo:** dos 36.138
      acordes, os **22.394 COM tracinho caem em cima da letra em 99,5%** dos
      casos (105 erros). Os 13.744 sem tracinho são **notas de transição** —
      para essas, cair no vão é o certo, não é defeito.
- [x] **Guardar as colunas dos tracinhos** na linha (campo `m`), para a folha
      desenhar a separação de nota. É o pedido dele, e agora tem de onde tirar.
- [ ] **Distinguir na tela** acorde do ritmo × acorde de transição.
- [ ] **Ler as últimas páginas do livro**, que descrevem os ritmos (Básico,
      Valseado…). Ele disse que os tracinhos existem em função desses ritmos.

---

# 🔴 30/08/2026 — DEPOIS DO PRIMEIRO CULTO DE DOMINGO

Marco: primeira vez usado de verdade num **culto evangelístico de domingo**,
igreja cheia, ele passando louvor do banco dos instrumentistas com o violão na
mão, e o operador impressionado. **Mas o culto foi um MIX de Sistema +
Glorifica**, e por um motivo só: **um louvor novo, muito tocado ali, não existia
no acervo.**

> A lição que fica: cobertura do acervo não é "mais conteúdo", é
> **confiabilidade**. Um louvor faltando derruba a confiança no culto inteiro.

## 1. ACERVO COMPLETO DE LOUVORES — a falha mais cara
- [ ] Varrer a internet atrás de **todo louvor da Maranata**: os novos (mesmo
      fora das fontes que temos), os antigos, e o que estiver associado à
      Maranata no YouTube. Objetivo dele: *"não podemos deixar falhar"*.
- [ ] **Fonte de verdade a definir com ele** — ver a pergunta no fim.

## 2. PALAVRA NO CELULAR — falha "gravíssima" (palavra dele)
- [x] Marcar mais de um versículo é inutilizável: ao tocar, **o texto projetado
      cobre a tela toda**, tapa a área de seleção, e não dá para escolher mais
      nada. O painel de leitura (`.rodape-vers`) é `sticky` e cresce sem teto.
- [x] O certo é **repetir no celular o modelo do computador**: um toque projeta,
      **dois toques guardam na lista** (`app.js:1419` faz exatamente isso).
      O duplo-toque até existe no celular, mas está enterrado atrás do modo
      "✓ Marcar vários", que é o que atrapalha. **Tirar o modo, ficar com o
      duplo-toque.**

## 3. CELULAR NA HORIZONTAL
- [x] Deitando o celular fica "tudo errado, tudo estranho". Ele quer que ao
      virar, o layout **se reorganize** para aproveitar a tela larga — mais
      informação lado a lado, não a mesma coluna esticada.

## 4. CIFRAS — acaba o Nível 1 / Nível 2
Decisão dele: **não vai mais existir "básico 1" e "básico 2" no nosso sistema.**
- [x] Vai haver **UMA coletânea só**, o *"suco do suco"*: a simplicidade e
      eficiência do básico 1 **com alguns arranjos elegantes bem postos** do
      básico 2. Notas com sentido, nem pobre nem cheia à toa.
- [x] A base é a **correção prática dos instrumentistas**. Ele tem a coletânea
      de um **instrumentista veterano**, cheia de modificações à mão, e vai
      mandando fotos louvor a louvor (escritas por cima — vai dar trabalho ler).
- [x] Consequência: o seletor N1/N2 sai da tela.

## 5. ESTRUTURA DE REPETIÇÃO DOS LOUVORES
- [ ] Não está sendo respeitada. Quando o livro traz *1ª estrofe, coro, 2ª
      estrofe, 3ª estrofe*, o que se canta é
      **estrofe → coro → estrofe → coro → estrofe → coro → coro final**.
      Hoje alguns louvores saem na ordem crua do livro.

## 6. Já feito nesta rodada
- [x] Os dois louvores que faltavam (ELE É O LEÃO DA TRIBO DE JUDÁ e
      TODO-PODEROSO ÉS) entraram, com cifra, na **v2.8.1** — publicada e com as
      4 URLs conferidas em 206. Ele não chegou a instalar na igreja.

## 7. ATUALIZADOR NÃO FUNCIONA — é o que trava tudo o resto
Relato dele (30/08): *"não identifica a atualização automaticamente… você clica,
ele fala 'ah, estou baixando zero bytes'… não bate o pacote completo… não fala
nem que você está com a melhor versão"*. **Foi por isso que ele não conseguiu
atualizar na igreja.**
- [x] Já conferido aqui: `versao_mais_nova()` **funciona** — rodei contra o
      GitHub e leu `2.8.1` certinho. O defeito está depois disso.
- [x] Suspeita a investigar: quando ele testou, o instalado era 2.8.0 e o
      release TAMBÉM era 2.8.0 → `tem=false`, e nesse caminho a tela só mostra
      o selo dourado se `/api/conteudo` disser que não falta nada. Se faltar
      conteúdo, ela não diz nada — parece "não identifica".
- [x] "Baixando 0 bytes": ver `_atualizar_thread` + `baixar_retomando`.
      Hipótese: `.parte` velho e completo em `%TEMP%\Sistema-baixando` faz pedir
      um trecho que não existe mais. (Na máquina dele agora não há `.parte`.)

## 8. VERSÍCULO PROJETADO SAI ERRADO
- [x] Mesmo marcando **um só**, o telão mostrava outros junto (*"aparecia o
      primeiro e o sétimo"*). Ele acredita que passar para o modelo do
      computador já resolve — provavelmente é sobra do `escolhidos`/`juntosNoAr`
      do modo "Marcar vários".

## 9. LISTA ÚNICA: louvores + versículos
- [x] Juntar a listinha de versículos com a Lista de Projeção **de maneira
      elegante**. (Já estava no PEDIDOS antigo; ele reforçou hoje.)

## 10. CIFRA NO CELULAR ESTÁ APERTADA
- [x] Falta espaço para o instrumentista operar. O **botão de reduzir tem de
      compactar de verdade o que está em cima** — inclusive encolher a prévia do
      telão, que é o que mais rouba altura.

## 11. CELULAR: falta o aviso do PRÓXIMO CULTO
- [x] A tela de projetar coisas no celular está **confusa de informação**, e
      **não tem o cartaz do próximo culto** — ele foi projetar hoje e não achou.
      No computador existe.

## ✅ BOA NOTÍCIA que ele fez questão de contar
O operador relatou um **erro grave na 2.7.5** (não conseguia passar o louvor).
Ele **tentou reproduzir na 2.8.0 e não conseguiu** — *"foi tentar induzir o erro
e não deu certo"*. O defeito nunca foi descrito direito, mas está resolvido.

---

## DECISÕES DELE — 30/08/2026 (não reabrir sem ele mandar)

**1. Acervo: VARRER TUDO, o mais amplo possível.** Sites de cifra, YouTube,
tudo que tiver cara de Maranata. Eu levantei o risco (letra errada indo pro
telão) e ele escolheu assim mesmo — a falta de louvor já custou um culto.
**Como fica seguro sem estreitar o pedido:** cada louvor carrega a ORIGEM e um
grau de confiança. O que veio de fonte oficial entra limpo; o que veio de
varredura entra marcado, e a marca aparece para o operador. Louvor duvidoso
tem de ser visivelmente duvidoso, nunca silenciosamente errado.

**2. Coletânea única: NASCE DA FUSÃO DOS DOIS.** Cruzar Nível 1 e Nível 2
louvor a louvor, montar a mistura automaticamente, e ele revisa por cima com a
coletânea do instrumentista veterano.

**3. Ordem de ataque: (1) atualizador, (2) ACERVO DE LOUVORES, (3) celular,
(4) cifras.** O acervo na frente porque foi a falha que obrigou o mix com o
Glorifica.

### Correção do diagnóstico do atualizador (ele contou depois)
**Instalar por cima FUNCIONA e funciona bem.** Ele baixou o instalador pequeno
do site do GitHub, rodou por cima da versão antiga, e o programa **reconheceu
como atualização e atualizou com perfeição**. Palavras dele: *"isso foi o seu
maior acerto até agora"*. Então o defeito é **só no botão de atualizar de
dentro do programa** — o caminho manual está de pé e é a saída segura.

### O que já está feito no celular (não publicado)
- Painel de leitura com teto: parou de cobrir a grade de versículos.
- Botão "Marcar vários" escondido; vale o **duplo toque**, como no computador.
- Layout deitado: grade e leitura lado a lado.

## 12. A VISÃO DA COLETÂNEA ÚNICA (palavras dele, 30/08)
> *"Não é pra reduzir a quantidade de notas, inclusive traz até mais do que a
> base comum, mas de forma elegante, de forma perfeita. Tanto o iniciante
> quanto o veterano vão olhar as MESMAS notas e vão se alegrar."*

- o **veterano** vê profundidade para tocar o louvor todo;
- o **iniciante** entende **quais notas pode tocar e quais pode pular**;
- público: *"instrumentistas do povo"*, não o grupo do presbitério onde
  *"não tem uma nota que não seja diminuta e sustenida com baixo em bemol"*.

**A ligação que resolve isso sem inventar régua:** o tracinho `|` do livro JÁ é
essa distinção — com tracinho = dentro do ritmo (o que o iniciante toca); sem
tracinho, no vão = transição (o que ele pode pular, e o veterano toca). Guardar
o tracinho e mostrá-lo na folha entrega a visão dele de graça.

**Por que há correção manual:** *"o louvor tocado presencialmente é muito
melhor, porque essas falhas são corrigidas a todo momento em todas as igrejas."*
A coletânea impressa tem erro de concepção — ele apontou um na foto do 218
MARANATA: a folha põe um acorde, tira o F# no Sol, põe outra nota e segue.

---

# 📍 ESTADO DO PLANO — 30/08/2026, fim da noite

Ordem escolhida por ele: **(1) atualizador · (2) ACERVO · (3) celular · (4) cifras**

| # | item | estado |
|---|---|---|
| 1 | **Atualizador** | **CONSERTADO**, falta compilar e testar |
| 2 | **Acervo de louvores** | **EM ANDAMENTO** — fontes achadas, extração começando |
| 3 | Celular | parcial: painel da Palavra, duplo toque e tela deitada feitos |
| 4 | Cifras / coletânea única | não começado |

## 1. ATUALIZADOR — causa achada e provada
**Não era a internet da igreja.** O programa compilado não levava certificado
nenhum; sem `cacert.pem` o Python cai no depósito do Windows, que numa **máquina
do zero** começa quase vazio. Reproduzi aqui com depósito vazio: falhou com
`CERTIFICATE_VERIFY_FAILED`; com o pacote dentro do programa, passou.
- `cacert.pem` viaja dentro dos três executáveis; **soma** com o depósito do
  Windows (senão quebraria em rede que assina o próprio tráfego).
- O check de versão subiu de 8s para 15s (hotspot é lento).
- **O programa acerta o relógio sozinho**: pega a hora certa por NTP (ou pelo
  cabeçalho `Date` de uma página HTTP simples — nenhum dos dois usa
  certificado), e se estiver fora por mais de um dia, acerta e **tenta baixar de
  novo**. Mexer no relógio exige administrador, então ele pede permissão uma vez.
- Mensagens sem jargão: relógio errado → fala de DATA E HORA; rede que assina o
  tráfego → *"a internet deste lugar não deixa o programa baixar sozinho…
  baixe pelo site e instale por cima"*.
- **Instalar por cima FUNCIONA** e é a saída manual boa (descoberta dele).

## 2. ACERVO — as três fontes, todas melhores que varrer a internet
1. **PDFs já no disco desde agosto**: **523 títulos** que o Sistema não tem —
   **424 do Avulsos 2024**, 86 do Cifras 2025, 53 dos dois níveis.
   (Script `faltantes.py`. Cuidado: título vem CORTADO pela quebra de linha do
   PDF; comparar título inteiro dava 332 faltantes e quase todos eram mentira.
   Casa por começo de título, mínimo 12 caracteres.)
2. **Drive oficial do Departamento de Louvor** (`drivelouvor`, pasta "Material
   para ensaio", link que ele mandou). Baixados 4 decks oficiais de projeção.
   A integração do Drive só enxerga o que foi compartilhado direto — não entra
   em subpasta. Baixar por base64 estoura o contexto; **usar o navegador com
   `https://drive.google.com/uc?export=download&id=…`**, que vai direto ao disco.
3. **`Downloads\PROJEÇÃO R.MS POWER POINT` — 2,2 GB, 587 PowerPoints**:
   `COLETÂNEA IGREJAS 2025` e `LOUVORES AVULSOS 2025` (o acervo do Sistema é de
   **2018**), mais as CIAS **uma por arquivo, com animação**, em 4:3 e 16:9, e a
   Bíblia em slides.

### 🔁 DECISÃO A REVER COM ELE
De manhã ele escolheu **"varrer tudo, o mais amplo possível"** (YouTube, sites
de cifra) porque não havia fonte confiável. **Agora há fonte oficial de sobra.**
Proposta: montar o acervo a partir do oficial e só depois procurar fora.

## LIÇÃO QUE SE REPETIU DUAS VEZES HOJE
Eu disse que só tinha 16 transcrições de doutrina — havia **23 PDFs** em
`Downloads feitos pelo usuário` desde 15/08, que eu não tinha olhado. E quase
saí varrendo a internet atrás de louvor que estava a dois cliques daqui.
**Olhar o disco ANTES de olhar para fora.**

## GRAFIA DOS ACORDES — decidido em 30/08/2026 (não reabrir)
**A sétima maior é sempre `7M`** (`G7M`), como o Cifra Club escreve. Era a
maioria (658 de 937) e é a mais fácil de entender — critério dele: *"quanto
mais fácil de entender for pra todo mundo, melhor"*.
Aplicado: `maj7`, `7+`, `M7` e `(maj7)` → **`7M`**; `dim` → `°`; `aug` → `+`;
`º` → `°`. **295 acordes trocados, 162.103 no total antes e depois.**
⚠️ `M` maiúsculo e `m` minúsculo são acordes DIFERENTES (`GM7` é maior, `Gm7`
é menor). O conserto tem teste que conta os menores antes e depois — ele
disparou uma vez, e o defeito era do próprio teste, que lia o "m" de `maj7`
como menor.

## DE ONDE VEIO A COLETÂNEA ÚNICA
Da conversa do Samuel com o **Xande (Alexandre)**, instrumentista. Ver
`CREDITOS.md` → "Quem ajudou a fazer", e a memória
`project_sistema_coparticipantes`.

---

## 31/08/2026 — ACERVO: 113 louvores novos APLICADOS
Da **Coletânea Cifrada 2025-2026 (a azul)**, com letra, cifra, tom e introdução.
Entraram como **Avulsos 2026**, com a numeração do próprio livro.
`louvores.js` 2.461 → **2.574** · cifras 2.236 → **2.349** (nos três lugares).
Decidido medindo: dos 524 títulos do Avulsos 2018 a azul só tem 52, então ela
**não substitui** o acervo antigo — os dois convivem.

Cinco defeitos pegos ANTES de gravar (todos iriam ao telão da igreja):
nome de autor virando verso (o louvor 5 tem TRÊS linhas de crédito); linha de
acorde com "BIS" no fim virando letra; hífen de alinhamento (`MI-NHA`); o
espaçamento do livro (`À     MI-NHA VOZ`); e pedaços de acorde partidos pelo
PDF (`AUG`, `SUS`, `#7`) virando verso.

## MÉTODO NOVO: a ordem cantada sai do VÍDEO
**Funciona, testado** em "O Senhor da ceifa está chamando" (canal oficial).
Os vídeos da ICM não mostram slides: a letra vem **queimada no rodapé**. Então
o certo é olhar SÓ A FAIXA DE BAIXO e ler com OCR.
Resultado: o coro (*"Fala Deus! Fala Deus! / Toca-me com brasas do altar…"*)
apareceu **4 vezes**, sempre inteiro — a estrutura estrofe→coro→estrofe→coro
que o livro não escreve.
- `yt-dlp` **com `player_client: android`** (o padrão dá 403)
- `OpenCV` para achar a troca de legenda · `RapidOCR` (sem torch) para ler
- roda no Python 3.14, **sem Python paralelo e sem ffmpeg**
- ⚠️ o OCR erra quando pega o quadro na transição: pegar o quadro do MEIO do
  trecho, e **cruzar com a letra que já temos** — o OCR serve para saber a
  ORDEM, não para copiar a letra.

## PEDIDOS DELE — 31/08, madrugada
- [ ] **Aplicar o método do vídeo em massa**, principalmente nos **corinhos e
      louvores de criança (CIAS)** — é onde o problema de repetição mais dói.
      Caçar os links no YouTube.
- [ ] **TENHO UMA CANDEIA (CIA 143)** — *"é difícil entender até a cifra"*.
      Corrigir a cifra **com base no vídeo**, porque a repetição é estranha:
      *"toca rápido, para, toca rápido, para"*.
- [ ] **LOUVOR 483 (CHEGOU O TEMPO DE PENSAR)** — muda de ritmo no meio
      (Básico → Guarânia → Básico → Guarânia). É complexo e *"dá umas travadas"*.
- [ ] Falta o nome de mais um louvor difícil tocado em 30/08 — ele vai mandar.
- [x] **MARANATA (218)** foi projetado no culto de 30/08 e **funcionou
      perfeitamente** — depois de bastante trabalho nele.

---

# ✅ 01/09/2026 — NOITE DE PENDÊNCIAS

Ele: *"vai resolvendo todas as pendências durante a noite. É importante."*

| # | Pendência | O que era, e o que virou |
|---|---|---|
| 2 e 8 | Versículo saía errado ("o 1º e o 7º juntos") | **A causa era do COMPUTADOR**, não do celular: guardar na Lista entrava com `on: true` e `reprojetarVista` projeta juntos assim que houver **qualquer** marcado. Guardar deixou de marcar; o `✓` da Lista continua para quem quiser juntar de propósito. |
| 3 | Celular deitado "fica tudo errado" | Só a aba Bíblia tinha layout deitado. Agora Louvores (lista + slides lado a lado), Telão (dois blocos por linha) e Lista (duas colunas) também. |
| 4 | Acaba o Nível 1 / Nível 2 | Coletânea única publicada na v2.8.2; o seletor saiu dos três arquivos. |
| 7 | Atualizador não funcionava | Certificado + relógio, v2.8.1/2.8.2. |
| 9 | Lista única, "de maneira elegante" | Os dois já moravam na mesma lista; o feio era o **cabeçalho de grupo a cada troca de tipo**, que picava a ordem do culto. Saiu; entrou a **numeração 1, 2, 3**. E o "já cantado" passou a ser simplesmente "está antes do que está no ar". |
| 10 | Cifra apertada no celular | O botão de compactar mexia só na barra e na letra. Agora **recolhe a prévia do telão junto** (24vh, o que mais roubava altura) e encolhe a barra do topo. Só reabre a prévia se foi ele que a fechou, e não sobrescreve a preferência gravada. |
| 11 | Falta o "próximo culto" no celular | O celular tinha 4 recados **fixos**; os quatro que dependem da agenda da igreja (próximo culto, cultos da semana, ceia, vigília) só existiam no computador. Agora o computador **calcula e manda prontos** no estado. Testado: *"AMANHÃ — QUARTA · Culto de Senhoras — 19:30"*. |

**Duas armadilhas de CSS que quase entraram:**
- `.aba[data-aba="telao"]{display:grid}` tem especificidade maior que o
  `[hidden]{display:none}` do navegador — **deitar o celular mostraria todas as
  abas empilhadas**. Guardado com `:not([hidden])`.
- A regra que escondia a prévia com a cifra aberta nascia **morta**: a prévia
  mora no `<header>` e as abas no `<main>`, e o combinador de irmão (`~`) não
  atravessa isso. Removida, com o motivo anotado no arquivo.

## Continua em aberto
- **#5 estrutura de repetição** — feito na Candeia, no 483 e n'O Senhor da Ceifa,
  pelo vídeo/áudio. Falta aplicar em massa; depende dos links que ele mandar.
- **#1 acervo** — as três coletâneas já entraram. Varrer a internet continua sem
  ser necessário.
- Ele ainda deve o **nome de mais um louvor difícil** tocado em 30/08.

## 01/09 — CINCO ITENS ANTIGOS QUE JÁ ESTAVAM PRONTOS

A lista estava desatualizada. Conferi um por um, no código e rodando:

| item | como conferi |
|---|---|
| Busca do celular não ranqueada | `pontuar()` do `controle.html:1568` é **idêntica** à `pontuarLouvor()` do computador |
| A+/A− pelo celular | `#tam`, `pintarTam()`, `escalaMinha` — existe e sincroniza com o PC |
| Lista de Projeção no celular | a aba **Lista** existe, com `addlouvor` e o ✕ para tirar |
| Histórico e painel de louvores | `/api/historico`, `abrirNoAr()`, `pintarPainel()` |
| Ligação Bíblia → louvor | testado com os exemplos DELE: **Isaías 60:1 → "DISPÕE-TE, RESPLANDECE" e "RESPLANDECE, Ó JERUSALÉM"**; Neemias 2:17 → "HINO DE JERUSALÉM"; Salmos 23:1 → "MEU BOM PASTOR" |

**Continuam abertos de verdade:** as categorias do culto (clamor, dedicação,
glorificação — ele ia continuar a lista e não continuou) e a tela de reset
bagunçada, que ele mesmo disse não ser urgente.

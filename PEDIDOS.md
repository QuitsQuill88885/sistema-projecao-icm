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
- [ ] **Busca do CELULAR não está ranqueada.** Corrigi só no computador. Procurar
      "Resplandece" no celular ainda traz louvores da letra antes do próprio
      "RESPLANDECE, Ó JERUSALÉM". Mesma regra do computador: título igual >
      título que começa > título que contém > palavras soltas no título > letra.
      Ignorar acento E pontuação ("resplandece jerusalem" acha "RESPLANDECE, Ó JERUSALÉM").
- [ ] **A+ / A− pelo celular não funciona.**
- [ ] **Caixa de busca do celular encavala a lista** (item cortado atrás do campo).
- [ ] **Lista de Projeção no celular** — VER a lista e ADICIONAR louvores/versículos.
      Palavras dele: é mais importante que controlar a projeção, porque o grupo
      de louvor precisa montar o que vai ser projetado.
      (comandos addlouvor / tirardalista / irpara já existem no computador)

### Ideias novas, ainda não começadas
- [ ] **Histórico e painel de louvores.** Guardar o que foi projetado em cada
      culto, com o TEMPO que cada louvor ficou no ar. Painel mostrando: mais
      cantados, mais tempo projetados, escolhidos por período (mês, últimos meses).
- [ ] **Ligação Bíblia ↔ louvor.** Ao abrir uma passagem, sugerir louvores cuja
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
- [ ] **RESTAURAR o traço separador de nota.** Existia e sumiu: um tracinho
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

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

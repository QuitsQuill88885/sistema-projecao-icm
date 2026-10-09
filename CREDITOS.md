# Créditos

## Autor

**Samuel Mariano Ribeiro**

Concepção, direção do projeto, decisões de produto e de desenho, e todos os
testes em uso real na Igreja Cristã Maranata de Iperó.

O programa nasceu para substituir o Glorifica, descontinuado, e foi construído
com uma régua declarada pelo autor no início:

> *"Com que mão isso não vai ajudar? Quanta pessoa da igreja, simples, velho,
> jovem, sem conhecimento de computador, criança, quanta gente não vai ser
> ajudada com isso?"*

Toda vez que apareceu escolha entre "mais poderoso" e "impossível de errar às
sete da noite de domingo", ganhou a segunda.

## Licenças deste projeto

| Parte | Licença | Arquivo |
|---|---|---|
| Código | MIT | `LICENSE` |
| Conteúdo original | CC BY 4.0 | `LICENSE-CONTEUDO.md` |

Ambas permitem uso comercial. Ambas exigem que o nome do autor continue citado.

---

## Material de terceiros

Nada abaixo pertence ao autor deste projeto, e nada abaixo é coberto pelas
licenças acima. Está aqui para uso da própria igreja.

### Fontes tipográficas — livres, vão embutidas no programa

| Fonte | Autor | Licença | Texto |
|---|---|---|---|
| **Outfit** | Smartsheet Inc. | SIL Open Font License 1.1 | `fontes/OFL-Outfit.txt` |
| **Bebas Neue** | Dharma Type | SIL Open Font License 1.1 | `fontes/OFL-Bebas.txt` |

A Outfit é o desenho de toda a projeção. Foi escolhida por medição: reproduz a
espessura de haste do padrão tipográfico usado pelo presbitério, e as quebras
de linha caem nos mesmos pontos — o operador não percebe diferença.

A SIL OFL permite embutir, copiar, modificar e distribuir, inclusive dentro de
produto comercial. A única exigência é que o arquivo da licença acompanhe a
fonte, e é por isso que os dois `.txt` acima ficam na pasta `fontes/` e vão
dentro do instalador.

**Nenhuma fonte comercial é distribuída com este programa.** Tudo o que a
projeção precisa vai no pacote; o programa não procura fonte instalada na
máquina e não depende de nada estar presente no Windows.

### Conteúdo da igreja

| Item | Origem |
|---|---|
| `dados/louvores.js` | Letras das coletâneas da Igreja Cristã Maranata |
| `cifras/` | Coletâneas cifradas oficiais |
| `animacoes/` | Animações das CIAS |
| `fundos/` | Artes de fundo da igreja |

Material da Igreja Cristã Maranata, usado pela congregação local. Não deve ser
redistribuído separadamente nem publicado como se fosse deste projeto.

### Texto bíblico

`dados/biblia.js` — **Almeida Revista e Corrigida**.

### Se você for reaproveitar este projeto

O código é livre e o conteúdo original também. O material da igreja não é.
Para publicar uma versão sua, troque `dados/louvores.js`, `fundos/`, `cifras/`
e `animacoes/` pelo seu próprio conteúdo. As fontes podem ficar — são livres.

---

## Quem ajudou a fazer

O Sistema foi escrito por uma pessoa só, mas não foi pensado por uma pessoa só.
Estas ideias vieram de gente da igreja, e é justo que os nomes fiquem aqui.

**Tudo o que está nesta página saiu de uma igreja só: a Igreja Cristã Maranata
de Iperó.** Quem testou, quem achou defeito no meio do culto, quem arrumou os
PDFs, quem deu a ideia — todos são de lá. Ninguém de fora fez parte. Nas
palavras do Samuel: *"é um projeto realmente nosso"*.

**Alexandre — o "Xande"**, instrumentista. Foi uma conversa com ele que virou a
chave da coletânea única. Samuel contou que ia levar para o Sistema os acordes
que o Xande anotou à mão na própria apostila, e ele ficou acanhado: *"são notas
que eu mudei, simplificada"*. A resposta foi que é **exatamente isso**: o
Sistema existe para guardar as correções que os instrumentistas fazem na
prática — a igreja inteira já canta o louvor daquele jeito corrigido há muito
tempo, e isso nunca voltava para o papel. As correções dele vão para o Sistema
e passam adiante.

**Kevin**, o operador. Foi o primeiro a operar o Sistema num culto de verdade,
sem ter experiência com computador — e foi por causa dele que o controle pelo
celular deixou de ser conveniência e virou a peça central. Foi ele também quem
achou, em setembro de 2026, que as setas esquerda e direita paravam de trocar o
slide enquanto a cifra estava aberta no computador — um defeito que ninguém
tinha imaginado. E no culto de 26/09/2026, projetando, achou três erros de uma
vez: o louvor 249 (*Esta é a mensagem eterna de Deus*) terminava sem o último
coro; o 97 (*Jesus é o caminho*) mostrava um "BISBIS" no lugar do bis; e os
louvores que repetem a última linha a escreviam duas vezes em vez de mostrá-la
uma vez com o "(2x)" — com a ideia, dele, de que o bis na frente da linha é mais
fácil de seguir. O conserto corrigiu 27 louvores, conferidos na gravação oficial.

No culto do dia seguinte, 27/09/2026, achou mais: o coro do 207 (*Deus enviou
Seu Filho amado*) estava **partido no meio da frase** — "Porque Ele vive," numa
tela e "temor não há." só na seguinte — e levantou a dúvida sobre o "(2x)". Essa
dúvida fez conferir, **pela gravação oficial**, o que se canta em cada um dos
louvores da evangelização das CIAs de outubro/2026: seis estavam errados (69, 97,
79, 226, 242 e *Conheçamos e prossigamos*) e foram consertados na versão 2.9.10.

E num papel escrito à mão, ainda em 27/09/2026, anotou mais dois: o **36**
(*Crucificado foi meu Jesus*) acabava **seco** na segunda estrofe, sem o coro
final, e o **146** (*Existe um alguém que cuida de mim*) não dizia que o coro é
**bis**. Foi esse papel que deu origem ao **Protocolo de Conferência Absoluta** —
ouvir a gravação, ver a cifra, ver o livro e só então consertar. O papel trazia
também o **CIA 91** e o **658**, que ele não chegou a testar porque desistiu do
Sistema no meio do culto; os dois foram conferidos assim mesmo, e o 658 estava
sem o bis de *Exaltar-te-ei, ó Deus*. Os quatro foram consertados na versão 2.9.11.

**Joelma** arrumou e mandou as coletâneas da evangelização das CIAs de outubro de 2026: a
**lista de louvores cifrados oficial da Evangelização** e as partituras **Cias 2026 (outubro)**
em Dó e em Si bemol. Foi dessa lista que saiu, na versão 2.9.9, a **cifra oficial**
dos 11 louvores da evangelização — no lugar das que tinham vindo de leitura de
livro, e uma delas trazia outro louvor inteiro dentro.

**Kevin**, de novo, na versão 2.9.12: viu na igreja que *Jesus é o caminho* saía
com **um bloco por tela**, quando o certo são **dois blocos "cantar 2x" por tela** —
o jeito do slide das crianças. Daí saiu a conferência de **todos** os louvores das
CIAS contra o PowerPoint oficial. E disse, com todas as letras, que a Evangelização
tinha louvor faltando: os avulsos da lista ganharam a animação deles.

**Samuel** operou o Sistema na igreja em 05/10/2026 e ditou o **relatório** que virou a
versão 2.9.12: animação parada, corte seco no fim do louvor das crianças, a animação
virando fundo, a busca lenta, o versículo que esquecia o capítulo, e os louvores
repetidos. E **achou o PowerPoint de 6 GB** das CIAS animadas, que trouxe de volta o
movimento de 147 telas e as animações de 241 louvores (o pacote antigo parava no 142).
E em 09/10 mandou que cada louvor tivesse **uma versão só** — *"o louvor é o mesmo,
caramba"* —, com os números juntos, o novo primeiro: **"69   9990   AV"**. Na 2.9.13
mandou conferir um a um os 63 parecidos que ainda estavam separados.

**Cristiane** mandou os slides da aula e os áudios que fecharam a ordem dos louvores
da Evangelização de outubro de 2026 (o *Você sabe o que é salvação* no meio da aula).

**Luís**, padrasto do Samuel. A ideia da **sugestão de louvores por versículo**
é dele.

**Emanuel**, irmão do Samuel, também contribuiu com ideia no começo do projeto.

---

## Como citar

> **Sistema** — projeção para igrejas, de Samuel Mariano Ribeiro.
> Código sob MIT, conteúdo sob CC BY 4.0.

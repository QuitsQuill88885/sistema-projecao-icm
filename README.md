# Sistema — projeção para a igreja (louvores, Bíblia e slides infantis animados)

Programa de projeção para o culto: letras de louvores, Bíblia, avisos, cronômetro, cifras e as apresentações animadas
das crianças. Roda em **Windows e Linux**, **sem internet**, em **computador fraco**, e é operado por quem não é da
área de informática. O celular vira o controle remoto.

Feito para a Igreja Cristã Maranata de Iperó (SP). Serve a qualquer igreja que queira usá-lo.

**[Baixar a versão mais nova](https://github.com/QuitsQuill88885/sistema-projecao-icm/releases/latest)**

---

## A versão 4.0: sem navegador dentro

A série 3.0 desenhava o telão como uma página web, dentro do navegador embutido do Windows. A 4.0 é um programa só,
que desenha tudo direto pela placa de vídeo (Python + Qt Quick). O motivo foram dois cultos de verdade em que a versão
antiga caiu num computador de 4 GB de memória.

| O que | 3.0.12 | 4.0 |
|---|---|---|
| Processos abertos | 8 | 1 |
| Memória em uso | 549 a 705 MB | 203 a 248 MB |
| Resposta ao clique | 354 ms | 19 a 23 ms |
| Processador, só texto | 6,5 s por minuto | 1,4 s por minuto |
| Do celular ao telão, num notebook AMD E-450 | não medido | 119 ms (meio) |

Prova de resistência num notebook de 2011 (AMD E-450, Radeon HD 6320, Linux) ligado a um projetor 1920x1080: 60
louvores animados em fila, 480 trocas pelo celular, memória entre 326 e 518 MB, nenhuma falha.

Cada número, com onde e como foi medido, está em [docs/motor-nativo.md](docs/motor-nativo.md).

---

## O que ele faz

**Louvores.** 2.778 letras em seis coletâneas, buscáveis por número, por nome ou por um trecho da letra, com ou sem
acento. O mesmo número em coletâneas diferentes aparece separado, cada um debaixo do nome da sua coletânea.

**Bíblia.** Um clique projeta, dois guardam na lista. Avança sozinho de capítulo e de livro e projeta vários
versículos juntos.

**Louvores infantis animados.** 205 louvores com a tela 16:9 animada (a letra que entra, as notinhas que mexem),
tocados como vídeo H.264 pela placa de vídeo, que é o que a máquina fraca aguenta. Dá para desligar a animação num
toque.

**Celular como controle.** Uma página que abre no navegador do celular, pela rede da igreja ou pelo roteador do
próprio celular, com prévia do telão. Não instala nada. O clique segurado não atropela: só avança quando o telão já
mostrou o slide.

**Tela de retorno com os gestos.** Uma segunda tela para quem está à frente das crianças: o gesto de agora, o próximo
e o aviso do próximo louvor. Outro computador com o Sistema, na mesma rede, vira essa tela sozinho.

**Lista de projeção.** Monte a ordem do culto antes de começar. Louvores e versículos ficam em grupos separados; o que
já passou fica riscado.

**Cifras.** Ligadas a cada louvor, com transposição de tom.

**Notebook de tampa fechada (Linux).** Continua projetando pelo HDMI, com o controle no celular.

---

## Instalação

**Windows.** Baixe `Instalar-o-Sistema-completo.exe` e dê dois cliques. Ele instala por cima da versão anterior e não
apaga configurações, louvores próprios, fundos nem o histórico. Se o Windows perguntar se permite o acesso à rede,
responda que sim: é isso que deixa o celular controlar o telão.

| Arquivo | Para quem |
|---|---|
| `Instalar-o-Sistema-completo.exe` | todo mundo: tem tudo dentro, inclusive os louvores infantis animados |
| `Instalar-o-Sistema.exe` | quem já tem os vídeos e quer só atualizar o programa |
| arquivos `sistema-linux-*` | Linux (Mint, Ubuntu e parentes) |

**Linux.** Os três arquivos `sistema-linux-*` e o roteiro de instalação estão na página da versão.

---

## Documentação técnica

Notas de campo, escritas para quem tiver o mesmo problema:

- [Vídeo pela placa num notebook AMD antigo (Radeon HD 6320, driver radeon, UVD)](docs/notebook-amd-radeon-uvd.md):
  quadro verde, quadro preto, `crossing 256MB boundary`, a causa no driver e o conserto.
- [Da página web ao motor nativo](docs/motor-nativo.md): por que a 4.0 existe e o que foi medido.
- [O defeito do filmador](docs/defeito-do-filmador.md): 637 animações que saíam congeladas, e a linha que consertou.

---

## Sobre o conteúdo

O código deste repositório é o **programa**. As letras, a Bíblia, as cifras e os slides infantis são material da
Igreja Cristã Maranata; eles vão dentro do instalador para a igreja usar, e não são nossos para relicenciar. O material
oficial está em <https://louvoricm.org.br>, no aplicativo oficial da igreja e na Livraria ICM.

---

## Licença

- Código: [MIT](LICENSE).
- Conteúdo original do projeto (textos, telas, documentação): [Creative Commons Atribuição 4.0](LICENSE-CONTEUDO.md).

Autor: Samuel Mariano Ribeiro. Quem ajudou está em [CREDITOS.md](CREDITOS.md).

# Sistema — projeção para a igreja

Programa de projeção para o culto: louvores, Bíblia, avisos, cronômetro e
apresentações da Escola Bíblica. Roda em Windows, **sem internet**, e é operado
por quem não é da área de informática.

Feito para a Igreja Cristã Maranata de Iperó, mas serve a qualquer igreja que
queira usá-lo.

> *"Escreve a visão e torna-a bem legível sobre tábuas,
> para que a possa ler quem passa correndo."* — Habacuque 2:2

---

## O que ele faz

**Louvores.** A coletânea inteira, buscável por número, por nome ou por um trecho
da letra — com ou sem acento, com ou sem vírgula. A busca traz primeiro o louvor
cujo **título** bate, e só depois os que citam aquilo no meio da letra.

**Coletâneas convivendo.** O mesmo número existe em coletâneas diferentes com
letras diferentes: o 60 da Coletânea 2018 e o 60 dos CIAS são louvores distintos.
Procurando por número, o Sistema mostra os dois, cada um debaixo do nome da sua
coletânea. Não há sigla para decorar.

**Bíblia.** Um clique projeta, dois guardam na lista. Avança sozinho de capítulo
e de livro, e projeta vários versículos juntos numa tela só.

**Lista de projeção.** Monte a ordem do culto antes de começar. Louvores e
versículos ficam em grupos separados e **não se misturam** na navegação: uma hora
é a hora do louvor, outra é a hora da palavra. O que já passou fica riscado.

**Celular como controle.** Uma página que abre no navegador do celular, pelo
hotspot ou pelo wi-fi da igreja, com prévia ao vivo do telão. Sem instalar nada.

**Cifras.** Ligadas a cada louvor: um botão abre a cifra na página certa, para
quem está tocando.

**Louvores de CIAS com animação.** Quando existe a versão animada, ela substitui
o texto — e dá para desligar num toque.

---

## Instalação

Baixe o instalador e execute. Ele cria o atalho na Área de Trabalho e no menu
Iniciar. Para atualizar, basta instalar por cima: **suas configurações, seus
fundos e seus louvores próprios não são tocados** — eles ficam em
`%APPDATA%\Sistema Projecao`.

---

## Sobre o conteúdo — leia antes de clonar

**Este repositório tem o PROGRAMA, não o conteúdo.** Ficam de fora, de propósito:

| O que | Por quê |
|---|---|
| Louvores e Bíblia | material da Igreja Cristã Maranata |
| Fundos de tela | idem |
| Fonte de projeção | tipografia comercial, licenciada |
| Animações dos CIAS | pacote oficial da igreja |
| Cifras | coletâneas publicadas pela ICM |

Nada disso é nosso para redistribuir. Quem clonar precisa trazer o próprio
conteúdo — o Sistema importa tudo pelo menu, e funciona normalmente sem nada
disso (os botões correspondentes apenas não aparecem).

O material oficial da ICM está em <https://louvoricm.org.br>, no aplicativo
oficial da igreja e na Livraria ICM.

---

## Para quem quiser compilar

Precisa de Python 3 no Windows, com `pyinstaller`, `pywebview`, `pywin32`,
`qrcode`, `pypdf` e `pillow`.

```
python -m PyInstaller --noconfirm "Sistema.spec"
```

Detalhes em [COMO-COMPILAR.md](COMO-COMPILAR.md), inclusive por que o programa é
empacotado em pasta e não em arquivo único (arquivo único descompactava 28 MB a
cada abertura e demorava 8 segundos para abrir).

Ferramentas auxiliares ficam em `ferramentas/`: leitura do pacote de animações,
conversão para WebP e indexação das cifras por louvor.

---

## Créditos

Escrito por Samuel, para a igreja dele, com ajuda do Claude (Anthropic).

O nome veio de Provérbios 31:28.

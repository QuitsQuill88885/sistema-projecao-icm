# Sistema

Projeção para o culto da Igreja Cristã Maranata — louvores, Bíblia, avisos e slides.
Feito para rodar em qualquer computador com Windows, **sem internet** e sem depender de mais nada.

> *"Escreve a visão e torna-a bem legível sobre tábuas, para que a possa ler quem passa correndo."*
> — Habacuque 2:2

---

## O que ele faz

- **Louvores** — a coletânea inteira, com busca por número, nome ou por um trecho da letra (com ou sem acento).
  A letra se ajusta sozinha para caber na tela: nenhum louvor fica cortado.
- **Bíblia** — um clique projeta o versículo; ▶ segue a leitura sozinho, cruzando capítulos e livros.
  Marque vários com ✓ e eles aparecem juntos na mesma tela.
- **Lista de projeção** — monte a ordem do culto (louvores e versículos), reordene arrastando,
  e o Avançar respeita exatamente a sequência que você montou.
- **Slides** — abre PowerPoint e PDF da Escola Bíblica e projeta como se fosse um louvor.
- **Timer, Relógio, Texto e Avisos** — com avisos que se montam sozinhos a partir dos cultos da sua igreja.
- **Fundos** — organizados por categoria, com a tela de espera que aparece sozinha entre os louvores.

O operador sempre sabe o que está no telão: a barra de estado mostra **Projetando ao vivo**,
**Congelado** ou **Projeção fechada**, e a prévia mostra exatamente o que a congregação vê.

## Como instalar

Execute o **`Instalar o Sistema.exe`**. Ele instala o programa, cria o atalho na Área de Trabalho
e no menu Iniciar, e cria as suas pastas em `%APPDATA%\Sistema Projecao`:

- `Meus fundos` — imagens de fundo que você quiser usar
- `Minhas apresentações` — PowerPoint e PDF da Escola Bíblica
- `Meus louvores` — louvores que você adicionar

Suas configurações ficam nessa pasta, **fora do programa**. Ao atualizar, nada se perde.

## Como projetar no projetor

1. Ligue o cabo (HDMI) e aperte <kbd>⊞ Windows</kbd> + <kbd>P</kbd>, escolhendo **Estender**.
2. Clique em **Abrir Projeção**. O Sistema encontra o projetor e joga a tela cheia nele sozinho.

## Para desenvolver

```bash
pip install pywebview pywin32 pyinstaller
python sistema.py
```

Para gerar o instalador, veja os comandos do PyInstaller em [`COMO-COMPILAR.md`](COMO-COMPILAR.md).

---

## Créditos

Este projeto não teria existido sozinho.

- **Glorifica** (glorifica.com.br) — foi a referência e a inspiração. Muitas das melhores ideias daqui
  vieram de lá: a lista de projeção, a exibição de vários versículos juntos, o congelamento da tela.
  O autor fez, sozinho, um trabalho que serviu a igrejas no Brasil inteiro por anos. O mérito é dele.
- **Igreja Cristã Maranata** — pelo padrão visual dos cultos, que este projeto procura respeitar fielmente.
- Ao projeto de código aberto que organizou e publicou a coletânea de louvores em formato legível,
  o que tornou possível carregar a coletânea inteira aqui.

## Sobre o conteúdo

O **código** deste repositório é livre (veja [LICENSE](LICENSE)).

O **conteúdo** que acompanha o programa — fontes tipográficas, artes de fundo, letras dos louvores
e texto bíblico — pertence a terceiros e está aqui apenas para uso da própria igreja.
Não redistribua esse conteúdo separadamente. Se for usar este código em outra igreja,
coloque as suas próprias fontes em `fontes/` e os seus próprios fundos em `fundos/`.

---

Feito com carinho para a Igreja Cristã Maranata de Iperó.

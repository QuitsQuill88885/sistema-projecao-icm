# O defeito do filmador: 637 animações que saíam congeladas

Os louvores infantis do Sistema vêm de um PowerPoint em 16:9 com animações: a letra que entra, notinhas musicais que
mexem, um coração que voa. Para a máquina fraca tocar isso sem esforço, o Sistema **filma** cada clique do slide num
vídeo H.264 curto (a entrada e, quando há movimento contínuo, um laço).

Em 15/11/2026 apareceu que, em 113 louvores, as figurinhas animadas estavam paradas no telão. Eram 637 camadas em 313
slides.

## A causa

O filmador posa o slide quadro a quadro: para cada instante, esconde e mostra as camadas e pede a cada animação o
quadro daquele tempo. O componente que desenha uma camada animada (`AnimSlide`) reiniciava a animação toda vez que
voltava a ficar visível, **depois** de o filmador já ter aplicado o tempo:

```qml
// antes: toda vez que a camada reaparecia, o quadro voltava para o zero
function comecar() {
    timer.stop(); pronta = false; usaB = false
    quadro = 0
    ...
}
```

A animação do **fundo** nunca era escondida, então filmava certo. Toda animação em **camada** saía sempre no quadro 0.
Por isso o defeito passou: os slides em que o movimento estava no fundo estavam bons, e eram os mais testados.

## O conserto

Uma linha: ao recomeçar, se há um tempo imposto, a camada começa no quadro daquele tempo.

```qml
function comecar() {
    timer.stop(); pronta = false; usaB = false
    quadro = (tempo >= 0 && n > 1) ? quadroEm(tempo) : 0
    ...
}
```

Os 113 louvores foram filmados de novo. No louvor usado como prova, os quadros que mudam por volta do laço foram de 0
para 7 e 8.

## O que ficou de lição

- **Hash de quadro decodificado não mede movimento.** Dois quadros visualmente iguais têm hashes diferentes depois da
  compressão. A medida que serviu compara a diferença de imagem entre quadros seguidos, com limiar.
- **Dezoito laços continuaram medindo "parado" e não eram defeito:** em 16 a animação só existe na entrada (o coração
  voa e some), em 2 os quadros da origem são quase iguais. Só olhando as fotos um a um deu para separar.
- **Quem viu primeiro foi o operador, no projetor.** Nenhuma das 63 provas automáticas media se a camada mexia.

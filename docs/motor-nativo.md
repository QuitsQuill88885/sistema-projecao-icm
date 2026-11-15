# Da página web ao motor nativo: por que a 4.0 existe

A série 3.0 do Sistema era um programa em Python que abria o navegador embutido do Windows (Edge WebView2) e desenhava
cada tela como uma página (HTML, CSS, JavaScript). A 4.0 é um programa só: o Python comanda e o Qt Quick desenha tudo
direto pela placa de vídeo. Não há navegador dentro.

Para ser exato: o motor em C++ é o do Qt, usado pronto. O que foi escrito para o Sistema é Python e as telas em QML.

## Por que mudou

Dois cultos de verdade, num computador de igreja com 4 GB de memória:

- **25/10/2026:** o programa caiu no meio do culto. O registro do Windows mostrou o WebView2 com 1,5 GB e o programa
  com 1 GB; levava de 1h35 a 3 h para estourar. No Gerenciador de Tarefas, o Sistema eram 8 processos (1 + 7 do
  navegador embutido).
- **08/11/2026:** seis pedidos de abrir o telão chegaram juntos e abriram seis janelas de navegador. Só uma máquina
  lenta abre essa brecha.

## Os números, lado a lado

| O que | 3.0.12 (página web) | 4.0 (nativa) | Onde foi medido |
|---|---|---|---|
| Processos | 8 | 1 | PC da igreja; computador de desenvolvimento |
| Memória em uso | 549 MB (705 MB no PC da igreja) | 203 a 248 MB | computador de desenvolvimento |
| Resposta ao clique | 354 ms | 19 a 23 ms | prova de carga a 800x600 |
| Processador, só texto | 6,5 s por minuto | 1,4 s por minuto | programa empacotado |
| Do celular ao telão (notebook fraco) | não medido | 60 a 167 ms, meio 119 ms | AMD E-450, Linux |
| Memória no notebook fraco | não medido | 238 a 250 MB, estável | AMD E-450, Linux |
| Navegador dentro | sim | não | |

O que **não** foi medido: as duas versões lado a lado na mesma máquina fraca. As comparações acima são de máquinas
diferentes onde está indicado.

## A prova de resistência (14/11/2026)

O Sistema instalado num notebook AMD E-450 com Radeon HD 6320, telão 1920x1080 no HDMI, comandado pelo celular:

- 60 louvores infantis animados em fila, 480 trocas: memória de 326 MB no começo, pico de 518 MB, 445 MB no fim;
- 0 recusas da placa de vídeo, 0 erros do controle;
- abre em 12 a 13 s nessa máquina.

## O que a 4.0 trouxe

- **Vídeo pela placa no lugar do WebP animado.** O WebP é decodificado pelo processador (736 ms para abrir e 470 ms
  para encolher, a cada abertura, na máquina fraca). As animações viraram MP4 H.264, que a placa decodifica.
- **Imagem parada em JPEG:** 91 ms para abrir e 36 ms na miniatura, contra 139 e 135 ms do WebP.
- **O clique segurado não atropela o telão:** o controle só avança quando o telão já mostrou o slide atual.
- **Tela secundária:** outro computador com o Sistema, na mesma rede, vira a tela de retorno sozinho.
- **Notebook de tampa fechada** continua projetando pelo HDMI (Linux), com o controle no celular.
- **Gestos na tela de retorno** para os louvores infantis, com o aviso do próximo louvor.

## O tamanho da obra

- 6.385 linhas de Python em 8 arquivos e 7.620 linhas de telas em 52 arquivos QML;
- 63 provas automáticas;
- 118 commits de 04/11 a 14/11/2026.

## Três lições que valem para qualquer projeto em Qt Quick

1. **`Repeater` que recria `Text` vaza no Qt 6.12:** cerca de 5 MB a cada 40 trocas. Itens fixos, ou um `Text` só,
   não vazam.
2. **O Qt arredonda o tamanho da letra para pixel inteiro.** Imitar a suavização de letra do Windows por conta própria
   dobra o custo na máquina fraca; medir peso e largura da letra antes de mexer.
3. **Medir a imagem, não o log.** Mais de uma vez uma prova passou com "0 erros" e a tela estava preta.

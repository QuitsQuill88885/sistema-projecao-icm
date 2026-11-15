# Vídeo pela placa num notebook AMD antigo (Radeon HD 6320, driver radeon, UVD)

Notas de campo do Sistema 4.0 rodando em Linux num Sony Vaio com AMD E-450 e Radeon HD 6320 (família PALM,
decodificador de vídeo UVD 2.2, driver `radeon` do kernel). É o computador mais fraco em que o Sistema foi provado.
Tudo aqui foi medido nele, em novembro de 2026, com kernels 6.8 e 7.0.

Se você tem uma placa AMD dessa geração (HD 6xxx de notebook, driver `radeon` e não `amdgpu`) e vê **quadro verde,
quadro preto ou a tela inteira congelando ao tocar vídeo H.264 pela placa (VAAPI)**, este texto pode poupar dias.

## 1. O sintoma

- Vídeo H.264 pela placa (VAAPI) sai verde ou preto, às vezes com o "fantasma" do movimento, sem erro nenhum no log.
- Em outras rodadas, o kernel escreve `crossing 256MB boundary` ou `kernel rejected CS`.
- Parece sorteio: o mesmo vídeo sai bom numa abertura e ruim na seguinte.
- Só aparece com um programa que usa bastante memória de vídeo aberto ao mesmo tempo (no nosso caso, a interface em Qt).
  Com um tocador sozinho quase nunca acontece.

## 2. As duas causas

### 2.1 O alcance do UVD

O UVD dessa geração só enxerga os primeiros 512 MB do endereço da placa (dois segmentos de 256 MB), e um buffer não
pode atravessar a divisa entre segmentos. O driver calcula essa faixa contando do começo de cada domínio de memória.
Quando a BIOS reserva 384 MB de memória de vídeo (o caso deste notebook, sem opção para mudar), a memória GTT começa
em 384 MB e a faixa "permitida" vira 384 a 640 MB:

- de 384 a 512 MB funciona;
- atravessando 512 MB: `crossing 256MB boundary`, e a placa pode travar ao desligar o UVD;
- inteiro acima de 512 MB: quadro preto ou verde, **sem erro**.

### 2.2 A mudança de endereço dentro da GTT

Esta é a causa do "sorteio". Em `radeon_bo_move`, quando um buffer muda de endereço **dentro** da GTT, o driver chama
`radeon_ttm_tt_bind`, que sai logo no começo em `if (gtt->bound) return 0;`. As páginas não são ligadas no endereço
novo, e o UVD passa a ler a página de enchimento no lugar do vídeo comprimido. O resultado é uma sessão de vídeo que
nasce ruim e fica ruim até fechar: só o quadro-chave sai certo (1 em cada 30).

Como isso foi isolado:

- não é endereço fora do alcance: o mesmo endereço dá quadro bom numa sessão e ruim em outra;
- não é atraso: pausando e lendo a superfície 2 s depois, ela continua vazia;
- não é o relógio do UVD nem o corte de relógio gráfico (desligado no teste, estragou igual);
- uma sessão aberta o tempo todo decodifica 11.280 quadros sem um erro; o defeito é na **abertura** da sessão;
- de 33 sessões medidas, a única ruim era a única cujo buffer de entrada foi criado acima de 511 MB e depois movido.

## 3. O conserto

Um módulo `radeon` remendado, instalado por DKMS para sobreviver às atualizações do kernel:

1. a memória de vídeo fica no primeiro segmento (0 a 256 MB); a GTT usada pelo UVD fica só na parte abaixo de 512 MB e
   dentro de um segmento;
2. na mudança de endereço dentro da GTT, o driver espera, desliga as páginas do endereço velho e liga no novo
   (18 linhas).

Prova, com a interface aberta, o telão numa segunda saída e sessão nova de vídeo sem parar:

| | Antes | Depois |
|---|---|---|
| Sessões de vídeo boas | 42 de 55 | 51 de 51 |
| Teste longo (1.160 trocas de slide) | verde voltava com o uso | 189 de 189 sessões boas, 0 erro |
| Temperatura máxima | | 77 °C |

Com cabo HDMI de verdade num monitor 1920x1080: 349 trocas, 39 de 39 sessões boas, 0 erro do driver.

## 4. O que não funciona (para ninguém repetir)

- `radeon.vramlimit=256`: só limita o uso; a GTT continua começando em 384 MB.
- Decodificar pelo processador: funciona, mas num E-450 custa quase o dobro de processador e não era o objetivo.
- **Varrer registradores da placa pela janela do PCI com a máquina em uso congela o notebook na hora.** Ler um
  registrador conhecido por vez funciona; varrer faixa não se faz.
- Uma prova que só conta erros no log não prova nada: a primeira versão do remendo punha o vídeo fora do alcance e
  dava **quadro preto sem erro**. Toda prova de vídeo tem de medir o quadro (brilho, comparação com o decodificado
  pelo processador).

## 5. A pausa a cada recomeço de vídeo

Mesmo com o driver consertado, essa placa para cerca de 340 ms toda vez que um vídeo **recomeça** (reabrir o arquivo
ou voltar à posição zero). Para um laço curto de animação (1 s), isso é uma travadinha por segundo.

O que foi medido:

| Jeito de repetir o laço | Resultado nessa placa |
|---|---|
| Voltar ao começo do arquivo a cada volta | 1 pausa de ~340 ms por volta |
| Dois tocadores revezando | pior: 10 a 15 quadros por segundo e pausas de 800 a 1.100 ms (recomeçar um vídeo para a placa inteira, inclusive o outro que está tocando) |
| **O laço repetido dentro do mesmo arquivo (~30 s por arquivo)** | **0 pausas em 25 s** |

Dentro do mesmo arquivo as voltas correm lisas; a pausa só existe no recomeço do arquivo. Por isso, no Linux, o
Sistema leva os laços das animações repetidos até cerca de 30 s por arquivo (`ffmpeg -stream_loop`). Em placas mais
novas o recomeço custa de 1 a 9 ms e os laços curtos servem.

Outros limites dessa placa que mordem calados:

- o UVD decodifica até 2048x1152: vídeo em pé de celular (1080x1920) passa da altura e cai no processador sem avisar;
- Qt 6.10 em diante exige SSE4.2, que o E-450 não tem: nele o Sistema roda com PySide6 6.9;
- com GLX a VAAPI trava a interface do Qt; com EGL (`xcb_egl`) funciona.

# Sistema v2.9.5

## As setas voltaram a funcionar com a cifra aberta

Quem opera tocando violão deixa a cifra na tela o culto inteiro — e, com ela
aberta, **nenhuma tecla passava o slide**: o telão ficava parado. Agora ← e →
passam o slide normalmente, enquanto ↑, ↓, espaço, PgUp e PgDn continuam
rolando a folha, que é o que a mão procura para ler.

E a folha acompanha: quando o louvor vira, a cifra do louvor novo entra
sozinha. Ler a cifra de um louvor que já saiu do telão é pior que não ter
cifra nenhuma.

*Defeito achado pelo Kevin, operador na ICM Iperó.*

## As cifras foram refeitas, louvor por louvor

154 louvores tiveram a cifra remontada da página do livro, lida em imagem. A
letra que aparece no telão e está na cifra subiu de **94,0% para 96,5%**, e os
louvores com letra faltando caíram de **365 para 178**. Entre os refeitos, 57
ficaram com a letra 100% completa.

**Onze louvores estavam com a cifra de OUTRO louvor** — o pior deles abria a
cifra inteira de outro hino. Seis voltaram com a cifra certa (VEREI JESUS e os
dois PEDRA DE ESQUINA com a letra completa). Os outros cinco, todos avulsos,
tiveram a cifra falsa **retirada**: até a fonte certa aparecer, esses louvores
ficam sem o botão de cifra. A letra no telão não muda em nada.

## Debaixo do capô

- `refaz_1a1.py` e `refaz_avulsos.py`: a página só vale se **provar** ser do
  louvor — tem que cobrir a letra que vai ao telão. Sem essa régua, o conserto
  automático troca lixo por lixo.
- `prova_instalador.py` agora abre o instalador compilado e confere também o
  conserto das setas e a versão lida do `sistema.py`, em vez de um número
  escrito à mão — com o número fixo, ele aprovava o instalador velho.

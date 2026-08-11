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

## Como citar

> **Sistema** — projeção para igrejas, de Samuel Mariano Ribeiro.
> Código sob MIT, conteúdo sob CC BY 4.0.

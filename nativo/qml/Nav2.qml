// ‹ PROJETAR › (o .nav2 da 3.0.13): Abrir Projeção (verde) · Parar de projetar (vermelho) · Projetar (em espera).
// Fica no #painel e, no modo apresentação, na faixa de baixo (os MESMOS botões, mudados de lugar, como o pbMover).
import QtQuick
import "Tema.js" as T

Row {
    id: n2
    property bool projetando: false
    property bool noAr: false
    property real larguraNav: 46            // #pb-faixa.muito .nav2 .nav{flex-basis:40px}
    signal projetar()
    signal anterior()
    signal proximo()
    spacing: T.estilo([".nav2"], false).gap
    Caixa { objectName: "botaoAnterior"; sels: [".ctrl", ".nav2 .nav"]; icone: "ant"; width: n2.larguraNav; height: bProj.height; onClicado: n2.anterior() }
    Caixa {
        id: bProj; objectName: "botaoProjecao"
        width: Math.max(0, n2.width - 2 * n2.larguraNav - 2 * n2.spacing)
        sels: [".ctrl", ".ctrl.projetar", ".nav2 .projetar"]
        estados: n2.projetando ? (n2.noAr ? [".ctrl.projetar.on"] : [".ctrl.projetar.on", ".ctrl.projetar.on.em-espera"]) : []
        icone: n2.noAr ? "descanso" : "play"
        // 11/11 (ele: o verde #2e8b57 "não conversa com as cores do sistema"): só o "Abrir Projeção" muda; o vermelho do
        // "Parar de projetar" e o cinza do "Projetar" em espera seguem os do tema. O ouro velho com borda ele reprovou na
        // tela (08h50). Em prova: "D" = o ouro do Sistema com letra azul-escura; "F" = bronze dourado com letra branca
        // (o contexto botaoAbrir escolhe; sem ele, D)
        readonly property bool abrir: !n2.projetando
        readonly property string tom: typeof botaoAbrir !== "undefined" && botaoAbrir ? botaoAbrir : "F"       // F = a escolhida por ele (11/11 09h02)
        // os tons em prova (as letras das prévias que ele viu): D ouro cheio · F bronze · G só o contorno · H contorno com
        // fundo dourado escuro · L contorno com degradê dourado escuro
        readonly property var tons: ({ "D": ["#f5d76e", "#ffe384", "#0b1526", 0], "F": ["#a8842a", "#b8922f", "#fbf0cf", 0],
                                       "G": ["#1e2d49", "#26375a", "#f5d76e", 2], "H": ["#2a2410", "#3a3216", "#f5d76e", 2],
                                       "L": ["#2a2410", "#3a3216", "#f5d76e", 2],
                                       // 14/11 (ele 12/11 17h43, do bronze: "tá bonito, mas falta alguma coisa (...) não sei se eu
                                       // sinto falta do verde"): em prova, o 5º valor é a cor do contorno. V = o verde escuro do
                                       // modo duas telas · N = o bronze com filete verde · P = o azul do painel, contorno verde, letra ouro
                                       "V": ["#257348", "#2e8b57", "#eafff2", 0], "N": ["#a8842a", "#b8922f", "#fbf0cf", 2, "#2e8b57"],
                                       "P": ["#1b2944", "#22324f", "#f5d76e", 2, "#2e8b57"] })
        readonly property var tomAtual: tons[tom] || tons["F"]
        color: abrir ? (sobre ? tomAtual[1] : tomAtual[0])
                     : T.fundo(st["background"] !== undefined ? st["background"] : st["background-color"])
        border.width: abrir ? tomAtual[3] : bw
        border.color: abrir && tomAtual[3] ? (tomAtual[4] || T.V.ouro) : (st["border-color"] || borda.cor)
        letraFixa: abrir ? tomAtual[2] : ""
        gradient: abrir && tom === "L" ? degrade : null
        Gradient { id: degrade; GradientStop { position: 0; color: "#6b5619" } GradientStop { position: 1; color: "#2a2410" } }
        texto: n2.noAr ? "Parar de projetar" : (n2.projetando ? "Projetar" : "Abrir Projeção")
        larguraTexto: Math.min(rotulo.implicitTextWidth, width - pad[1] - pad[3] - 20)
        onClicado: n2.projetar()
    }
    Caixa { objectName: "botaoProximo"; sels: [".ctrl", ".nav2 .nav"]; icone: "prox"; width: n2.larguraNav; height: bProj.height; onClicado: n2.proximo() }
}

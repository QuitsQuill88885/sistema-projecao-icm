// Os cantos arredondados de uma caixa com conteúdo que não se recorta sozinho (a prévia do telão: overflow:hidden +
// border-radius no CSS). Pinta, por cima, os 4 cantos de fora do arco na cor do fundo: sem camada nem máscara (barato no Vaio).
import QtQuick
import QtQuick.Shapes

Shape {
    id: cr
    property real raio: 8
    property color cor: "black"          // a cor do fundo atrás dos cantos de cima
    property color corBaixo: cor         // e dos de baixo (o fundo do painel é um degradê)
    preferredRendererType: Shape.CurveRenderer
    readonly property real r: raio
    ShapePath {   // cima, esquerda e direita
        strokeColor: "transparent"; fillColor: cr.cor
        PathSvg { path: "M0 0H" + cr.r + "A" + cr.r + " " + cr.r + " 0 0 0 0 " + cr.r + "Z" +
                        "M" + cr.width + " 0V" + cr.r + "A" + cr.r + " " + cr.r + " 0 0 0 " + (cr.width - cr.r) + " 0Z" }
    }
    ShapePath {   // baixo
        strokeColor: "transparent"; fillColor: cr.corBaixo
        PathSvg { path: "M0 " + cr.height + "V" + (cr.height - cr.r) + "A" + cr.r + " " + cr.r + " 0 0 0 " + cr.r + " " + cr.height + "Z" +
                        "M" + cr.width + " " + cr.height + "H" + (cr.width - cr.r) + "A" + cr.r + " " + cr.r + " 0 0 0 " + cr.width + " " + (cr.height - cr.r) + "Z" }
    }
}

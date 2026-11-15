// A CAIXA DE MARCAR do Chromium (<input type=checkbox> com accent-color), medida pixel a pixel no Edge (07/11):
// 17 x 17, cantos de 2 px. Marcada: o verde do accent (#2e8b57, a var(--verde)) com o visto branco de 2 px.
// Desmarcada: branca com borda de 1 px #767676.
import QtQuick
import QtQuick.Shapes

Rectangle {
    id: m
    property bool marcada: false
    property color destaque: "#2e8b57"
    width: 17; height: 17; radius: 2
    color: marcada ? destaque : "white"
    border.width: marcada ? 0 : 1
    border.color: "#767676"
    Shape {
        visible: m.marcada
        anchors.fill: parent
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeColor: "white"; strokeWidth: 2; fillColor: "transparent"
            capStyle: ShapePath.FlatCap; joinStyle: ShapePath.MiterJoin
            startX: 3.5; startY: 9
            PathLine { x: 6.8; y: 12.3 }
            PathLine { x: 13.2; y: 4 }
        }
    }
}

// O selo "✋ gestos" do modo apresentação (.pb-selo da 3.0.13): no canto de baixo do slide que tem gestos para a TV de
// retorno. Fica dentro do slide (anchors no pai).
import QtQuick
import "Tema.js" as T

Rectangle {
    readonly property var s: T.estilo([".pb-selo"], false)
    z: 3
    anchors { right: parent.right; bottom: parent.bottom; rightMargin: s.right; bottomMargin: s.bottom }
    width: linha.width + s.padding[1] + s.padding[3]; height: linha.height + s.padding[0] + s.padding[2]
    radius: s["border-radius"]; color: s.background
    Row {
        id: linha
        anchors.centerIn: parent; spacing: parent.s.gap
        Ico { nome: "mao"; tam: 13; cor: parent.parent.s.color; anchors.verticalCenter: parent.verticalCenter }
        Letra { px: parent.parent.s["font-size"]; weight: parent.parent.s["font-weight"]; color: parent.parent.s.color; text: "gestos"
                anchors.verticalCenter: parent.verticalCenter }
    }
}

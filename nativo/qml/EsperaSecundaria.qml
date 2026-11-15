// A TELA SECUNDÁRIA enquanto NÃO está mostrando o culto (13/11/2026): procurando o computador principal, esperando o
// "Usar as duas telas" de lá, ou reconectando. Ele (13/11 14h12): "não gostei dessa tela do procurando computador
// principal, a pílula não tá muito legal, tem que ser melhorada". Agora é uma tela inteira, no jeito do "Carregando" do
// Sistema: o fundo azul da tela de retorno, a marca, o nome, o recado e a barra dourada que vai e volta.
// A barra anda por ANIMATOR (linha de desenho): não para se o Python estiver ocupado.
import QtQuick
import "Icones.js" as Ic

Rectangle {
    id: es
    property string recado: ""
    property string nome: ""
    readonly property real vh: height / 100
    gradient: Gradient {
        GradientStop { position: 0.0; color: "#10203a" }
        GradientStop { position: 0.45; color: "#12223d" }
        GradientStop { position: 1.0; color: "#0b1526" }
    }
    Column {
        anchors.centerIn: parent; anchors.verticalCenterOffset: -2 * es.vh
        spacing: 2.6 * es.vh
        Image {
            anchors.horizontalCenter: parent.horizontalCenter
            width: 15 * es.vh; height: width; source: Ic.marca(); smooth: true
            sourceSize.width: Math.round(width); sourceSize.height: Math.round(height)
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "Tela secundária"; color: "#eaf0fb"; font.family: "Outfit"; font.pixelSize: 5.4 * es.vh
            font.weight: Font.ExtraBold; font.letterSpacing: 0.5
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            width: Math.min(implicitWidth, es.width * 0.8); horizontalAlignment: Text.AlignHCenter; wrapMode: Text.WordWrap
            text: es.recado; color: "#9db3d6"; font.family: "Outfit"; font.pixelSize: 3 * es.vh
        }
        Item { width: 1; height: 0.4 * es.vh }
        Rectangle {
            id: trilho
            anchors.horizontalCenter: parent.horizontalCenter
            width: 42 * es.vh; height: 0.9 * es.vh; radius: height / 2; color: "#1e2d49"; clip: true
            Rectangle {
                id: ouro
                width: trilho.width * 0.32; height: trilho.height; radius: height / 2
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0; color: "#c9a227" }
                    GradientStop { position: 0.5; color: "#f5d76e" }
                    GradientStop { position: 1; color: "#c9a227" }
                }
                SequentialAnimation {
                    running: es.visible; loops: Animation.Infinite
                    XAnimator { target: ouro; from: -ouro.width; to: trilho.width; duration: 1500; easing.type: Easing.InOutSine }
                    XAnimator { target: ouro; from: trilho.width; to: -ouro.width; duration: 1500; easing.type: Easing.InOutSine }
                }
            }
        }
    }
    Text {
        anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: 3.2 * es.vh }
        text: (es.nome ? "Este computador: " + es.nome + "  ·  " : "") + "Esc: sair  ·  F2: projetar deste computador"
        color: "#556f96"; font.family: "Outfit"; font.pixelSize: 2.1 * es.vh
    }
}

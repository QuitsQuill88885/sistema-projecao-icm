// O cartão "Outro Sistema nesta rede" (13/11/2026): ao abrir, o ouvido achou outro computador já projetando.
// A ESTRUTURA é a do esboço A que ele escolheu (ícone + título, a frase, os dois botões lado a lado). AS CORES são as do
// MODO DUAS TELAS da 3.0.12 (o #dt-cartao do app.css), palavra dele 13/11 15h54: "essa estética de verde escuro ... o que
// eu chamaria de Sistema ICM hacker ... suave, delicada, algo a mais": a borda verde com o brilho verde em volta, o
// círculo quase preto com o símbolo verde, o título em ouro, o texto #cdd9ee, o fundo #1e2d49 -> #16233c.
// O ícone: duas telas com pé, a de trás mais apagada (a que já projeta) e a da frente acesa (esta).
import QtQuick

Item {
    id: c
    property string nome: ""
    signal sim()
    signal nao()
    width: 470; height: cartao.height

    // o brilho verde em volta (box-shadow: 0 0 0 1px #2e8b5733, 0 0 18px #2e8b5740): aros que vão sumindo, sem efeito
    Repeater {
        model: 8
        Rectangle {
            anchors.centerIn: cartao
            width: cartao.width + (index + 1) * 4; height: cartao.height + (index + 1) * 4
            radius: 14 + (index + 1) * 2; color: "transparent"
            border.color: "#2e8b57"; border.width: 2; opacity: 0.20 * Math.pow(0.68, index)
        }
    }
    Rectangle {
        id: cartao
        width: parent.width; height: col.implicitHeight + 44; radius: 14
        gradient: Gradient {
            GradientStop { position: 0; color: "#22324f" }       // o clarão de cima (radial #ffffff12) somado ao #1e2d49
            GradientStop { position: 0.45; color: "#1b2944" }
            GradientStop { position: 1; color: "#16233c" }
        }
        border.color: "#2e8b57"; border.width: 2

        Column {
            id: col
            x: 22; y: 22; width: parent.width - 44; spacing: 13
            Row {
                spacing: 13
                Rectangle {     // .dt-ico: o círculo quase preto com o símbolo verde
                    width: 52; height: 52; radius: 26; color: "#07090e"; border.color: "#3affffff"; border.width: 1
                    Rectangle { anchors.fill: parent; anchors.margins: 1; radius: width / 2; color: "transparent"; border.color: "#332e8b57"; border.width: 1 }
                    // 13/11 15h58 (ele): "não precisa ser dois computadores, só igual o design do Sistema ICM: duas telinhas,
                    // dois retângulos entrelaçadinhos" = o ICO_2TELAS do app.js (rect 2,4 13x9 e rect 9,11 13x9, só o traço)
                    Rectangle { x: 11; y: 14; width: 19.5; height: 13.5; radius: 2.3; color: "transparent"; border.color: "#3fae6f"; border.width: 2.4 }
                    Rectangle { x: 21.5; y: 24.5; width: 19.5; height: 13.5; radius: 2.3; color: "transparent"; border.color: "#3fae6f"; border.width: 2.4 }
                }
                Column {
                    anchors.verticalCenter: parent.verticalCenter; spacing: 3
                    Text { text: "Outro Sistema nesta rede"; color: "#f5d76e"; font.family: "Outfit"; font.pixelSize: 20; font.weight: Font.Bold }
                    Text { text: "encontrado agora, ao abrir"; color: "#9fd3b4"; font.family: "Outfit"; font.pixelSize: 13 }
                }
            }
            Text {
                width: parent.width; wrapMode: Text.WordWrap; textFormat: Text.StyledText
                color: "#cdd9ee"; font.family: "Outfit"; font.pixelSize: 15; lineHeight: 1.3
                text: "O computador <b><font color='#f5d76e'>" + c.nome + "</font></b> já está com o Sistema ICM aberto. Este computador pode ser a <b><font color='#eaf0fb'>tela secundária</font></b> dele."
            }
            Item { width: 1; height: 1 }
            Row {
                spacing: 10; width: parent.width
                Botao { objectName: "outroNao"; txt: "Projetar daqui"; width: (parent.width - 10) * 0.42; onClicado: c.nao() }
                Botao { objectName: "outroSim"; txt: "Ser a tela secundária"; verde: true; width: (parent.width - 10) * 0.58; onClicado: c.sim() }
            }
        }
    }

    component Botao: Rectangle {
        id: b
        property string txt
        property bool verde: false
        signal clicado()
        height: 42; radius: 9
        // 13/11 15h58 (ele): o "Ser a tela secundária" um pouquinho mais escuro
        color: verde ? (area.pressed ? "#1e5f3b" : area.containsMouse ? "#2e8b57" : "#257348")
                     : (area.pressed ? "#131e34" : area.containsMouse ? "#22324f" : "#16233c")
        border.color: verde ? "#3fae6f" : (area.containsMouse ? "#3b5680" : "#2b3d5e"); border.width: verde ? 1 : 1.5
        Text { anchors.centerIn: parent; text: b.txt; color: b.verde ? "white" : "#dbe5f5"; font.family: "Outfit"
               font.pixelSize: 15; font.weight: b.verde ? Font.Bold : Font.Medium }
        MouseArea { id: area; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: b.clicado() }
    }
    component Telinha: Item {
        id: t
        property color cor
        property color miolo
        width: 24; height: 20
        Rectangle { width: 24; height: 15; radius: 3; color: t.miolo; border.color: t.cor; border.width: 2 }
        Rectangle { x: 10; y: 15; width: 4; height: 3; color: t.cor }
        Rectangle { x: 6; y: 18; width: 12; height: 2; radius: 1; color: t.cor }
    }
}

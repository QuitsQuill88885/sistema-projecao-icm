// A TELA DE CARREGAMENTO (o carregando.html da 3.0.12/3.0.13), 08/11/2026: aparece logo ao abrir, enquanto o painel é
// montado (no Vaio ~6 s). Ordem dele (07/11 21h16): "abrir demora uma eternidade, sem tela de carregamento".
// 08/11 17h (ordem dele pela HD): uma JANELINHA pequena e centrada, com a barra dourada de verdade; 17h30 (HD, pela
// reclamação dele de 07/11 "tudo quadrado, sem blur"): CANTOS REDONDOS (16 px, os dos cartões do painel) e SOMBRA suave
// em volta, a janela transparente fora do cartão.
// As animações usam ANIMATORS (rodam na linha de desenho): seguem andando mesmo com o Python montando o painel.
// Medidas do carregando.html: fundo radial #16294a -> #0b1526 (70%), coluna no centro com 18 px entre as peças, a marca
// de 86 px, "Sistema" 26 px peso 800 com 0,5 px de espaço, a frase 13 px #8fa8cf e o rodapé 11 px #556f96 a 18 px do pé.
import QtQuick
import QtQuick.Effects
import "Icones.js" as Ic

Item {
    id: c
    property string msg: "Preparando os louvores e a Bíblia…"
    // a partida do brilho da barra (Animator, roda na linha de desenho), chamada pelo Python com a janela JÁ à vista
    function comecar() { anda.start() }
    readonly property int larg: 260
    readonly property int m: 22                      // a margem da sombra (a janela tem o cartão + 22 px de cada lado)
    readonly property int raio: 16
    // a máscara do canto redondo precisa da placa; no desenho por software (testes sem tela) o cartão fica quadrado
    readonly property bool temPlaca: GraphicsInfo.api !== GraphicsInfo.Software && GraphicsInfo.api !== GraphicsInfo.Unknown
    property real progresso: 0                       // 0..1, mandado pelo Python a cada etapa da subida
    onProgressoChanged: { enche.stop(); enche.from = cheio.x; enche.to = -c.larg * (1 - Math.max(0, Math.min(1, progresso))); enche.start() }
    readonly property real k: 1.032                  // a Painel ICM no tamanho da Segoe (o mesmo encaixe do Letra.qml)

    // A SOMBRA: camadas de preto bem leve, cada uma 3 px maior e mais redonda (sem efeito: desenha em qualquer placa e
    // não custa nada na subida)
    Repeater {
        model: 7
        Rectangle {
            x: c.m - (index + 1) * 3; y: c.m - (index + 1) * 3 + 4
            width: cartao.width + (index + 1) * 6; height: cartao.height + (index + 1) * 6
            radius: c.raio + (index + 1) * 3; color: "black"; opacity: 0.075 - index * 0.009
        }
    }

    Item {
        id: cartao
        anchors.fill: parent; anchors.margins: c.m
        // o fundo: radial-gradient(ellipse at 50% 38%, #16294a 0%, #0b1526 70%), calculado como o navegador e PONTILHADO
        // (ferramentas/gera_fundo_carregando.py; o Shape do Qt fazia anéis). 1:1, sem esticar, com o centro do degradê no
        // mesmo ponto relativo do cartão; cortado no canto redondo pela máscara.
        Item {
            id: fundo
            anchors.fill: parent
            layer.enabled: c.temPlaca
            layer.effect: MultiEffect {
                maskEnabled: true; maskSource: mascara
                maskThresholdMin: 0.5; maskSpreadAtMin: 1.0        // a borda do canto suave, sem serrilhado
            }
            Rectangle { anchors.fill: parent; color: "#0b1526" }
            Image { source: "fundo_carregando.png"; smooth: false; cache: false
                    x: Math.round(fundo.width / 2 - 640); y: Math.round(fundo.height * 0.38 - 760 * 0.38) }
        }
        Item {
            id: mascara
            anchors.fill: parent; visible: false; layer.enabled: true
            Rectangle { anchors.fill: parent; radius: c.raio; color: "white" }
        }
        // o fio fino da borda (o mesmo dos cartões do painel): separa o cartão escuro de um fundo escuro
        Rectangle { anchors.fill: parent; radius: c.raio; color: "transparent"; border.color: "#24375a"; border.width: 1 }

        // uma peça que "sobe": aparece de baixo (10 px) em 0,6 s, com atraso
        component Sobe: Item {
            id: s
            default property alias conteudo: dentro.data
            property int atraso: 0
            implicitWidth: dentro.childrenRect.width; implicitHeight: dentro.childrenRect.height
            Item {
                id: dentro; width: s.width; height: s.height; y: 10; opacity: 0
                // ANIMATORS (08/11 17h30, filmado): com NumberAnimation a entrada CONGELAVA enquanto o Python monta o painel
                // e a janelinha ficou 1,5 s vazia; o Animator roda na linha de desenho e entra na hora
                SequentialAnimation {
                    id: anim; running: true
                    // a PAUSA também tem de ser Animator (a PauseAnimation congelava junto: "Sistema" e a barra só aos 2,7 s)
                    OpacityAnimator { target: dentro; from: 0; to: 0; duration: Math.max(1, s.atraso) }
                    ParallelAnimation {
                        OpacityAnimator { target: dentro; from: 0; to: 1; duration: 600; easing.type: Easing.OutCubic }
                        YAnimator { target: dentro; from: 10; to: 0; duration: 600; easing.type: Easing.OutCubic }
                    }
                }
            }
        }
        Column {
            anchors.centerIn: parent; anchors.verticalCenterOffset: -8
            spacing: 18
            Sobe {
                anchors.horizontalCenter: parent.horizontalCenter
                Image { width: 86; height: 86; source: Ic.marca(); sourceSize.width: 86 * Screen.devicePixelRatio; sourceSize.height: 86 * Screen.devicePixelRatio; smooth: true }
            }
            Sobe {
                anchors.horizontalCenter: parent.horizontalCenter; atraso: 100
                Text { text: "Sistema"; color: "#eaf0fb"; font.family: "Painel ICM"; font.pixelSize: Math.round(26 * c.k); font.weight: 800; font.letterSpacing: 0.5 }
            }
            Sobe {
                anchors.horizontalCenter: parent.horizontalCenter; atraso: 200
                Text { text: c.msg; color: "#8fa8cf"; font.family: "Painel ICM"; font.pixelSize: Math.round(13 * c.k) }
            }
            Sobe {
                anchors.horizontalCenter: parent.horizontalCenter; atraso: 300
                Item { width: c.larg; height: 12 }
                // a BARRA DOURADA DE VERDADE: enche conforme a subida anda (o Python manda o `progresso` por etapa) e um
                // brilho corre por cima. Tudo por ANIMATOR: não congela enquanto o Python monta o painel.
                Rectangle {
                    y: 6; width: c.larg; height: 6; radius: 3; color: "#1e2d49"; clip: true
                    Item {
                        id: cheio
                        width: c.larg; height: 6; x: -c.larg      // vazio: a peça inteira fora, à esquerda
                        clip: true
                        Rectangle {
                            anchors.fill: parent; radius: 3
                            gradient: Gradient { orientation: Gradient.Horizontal
                                GradientStop { position: 0; color: "#b8891f" } GradientStop { position: 0.6; color: "#f5d76e" }
                                GradientStop { position: 1; color: "#fff0b8" } }
                        }
                        Rectangle {                             // o brilho que corre dentro do dourado
                            width: 40; height: 6; opacity: 0.55
                            gradient: Gradient { orientation: Gradient.Horizontal
                                GradientStop { position: 0; color: "#00ffffff" } GradientStop { position: 0.5; color: "#ffffffff" }
                                GradientStop { position: 1; color: "#00ffffff" } }
                            XAnimator on x { id: anda; from: -40; to: c.larg; duration: 1400; loops: Animation.Infinite; running: false }
                        }
                    }
                    XAnimator { id: enche; target: cheio; duration: 450; easing.type: Easing.OutCubic }
                }
            }
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: parent.bottom; anchors.bottomMargin: 18
            text: "Projeção da igreja · funciona sem internet"; color: "#556f96"; font.family: "Painel ICM"; font.pixelSize: Math.round(11 * c.k)
        }
    }
}

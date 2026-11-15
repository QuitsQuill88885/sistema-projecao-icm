// A BARRA DE ROLAGEM das listas do painel (15/11/2026, ele olhando a foto do painel: "Não tem barra de scroll mais agora
// aqui na tela?"). A mesma da aba Apresentações (11/11: "tem que colocar a barra lateral de scroll"): 9 px, puxador
// azul-acinzentado, dourado ao arrastar. Só aparece quando a lista não cabe na altura.
import QtQuick
import QtQuick.Controls as QC
import "Tema.js" as T

QC.ScrollBar {
    policy: size < 1.0 ? QC.ScrollBar.AlwaysOn : QC.ScrollBar.AlwaysOff
    width: 9; minimumSize: 0.08
    contentItem: Rectangle { radius: 4; color: parent.pressed ? T.V.ouro : (parent.hovered ? "#9fb0cc" : "#5a6f93") }
    background: Rectangle { color: "#0a1526" }
}

// A FOLHA EM BC7 (10/11/2026): os recortes que mexem desenhados pela textura NOSSA (textura_bc.py, item
// TexBC), porque o leitor de .ktx do Qt não desenha BC7. A placa recebe a folha comprimida UMA vez (o processador não
// decodifica nada) e cada região só escolhe a célula do quadro. Só é carregado pelo SpriteAnim quando o Sistema oferece
// a folha (NATIVO_BC7=1 e o arquivo existe): fica num arquivo à parte para o "import Casa" não quebrar onde não há TexBC.
import QtQuick
import Casa

Item {
    id: bc
    property var dono: null                          // o SpriteAnim: dados, k, esc, ox, oy
    readonly property var dados: dono ? dono.dados : null
    readonly property bool pronta: guia.pronta
    TexBC { id: guia; visible: false; fonte: bc.dados && bc.dados.folhaBC ? bc.dados.folhaBC : "" }    // só lê o arquivo (no fundo)
    Repeater {
        model: bc.pronta && bc.dados ? bc.dados.regioes : []
        TexBC {
            fonte: bc.dados.folhaBC
            x: bc.dono.ox + modelData.x * bc.dono.esc; y: bc.dono.oy + modelData.y * bc.dono.esc
            width: modelData.w * bc.dono.esc; height: modelData.h * bc.dono.esc
            recorte: Qt.rect(modelData.fx[bc.dono.k] || 0, modelData.fy[bc.dono.k] || 0, modelData.w, modelData.h)
        }
    }
}

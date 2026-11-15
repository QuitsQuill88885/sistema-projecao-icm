// O assistente "ATUALIZAR" (o abrirAssistente('atualizar') da 3.0.13: o #sis-painel-atualizar na caixa do assistente):
// verificar a versão, procurar sozinho ao abrir (a chave atu_auto, a mesma da 3.0.13) e levar para outro computador.
// 08/11/2026: o Verificar e o Atualizar de verdade (o verificarAtualizacao da 3.0.13, frase por frase): Procurando…, Sem
// internet, Já está na mais nova, a linha DOURADA da melhor versão, "Existe a versão X" -> o Confirmar dela -> o andamento
// em % -> o instalador. O Exportar para o pendrive segue avisando até a peça dele.
import QtQuick
import "Tema.js" as T

Aviso {
    id: aa
    titulo: "Atualizar"
    largura: 560
    assistente: true
    botoes: [{ texto: "Fechar", sels: [".big-btn"], nome: "atuFechar" }]
    property bool auto: true
    property bool melhor: false              // .reset-row.melhor: atualizada E completa
    property string status: "Procura a versão mais nova na internet. Suas coisas nunca são apagadas, e o conteúdo pesado não baixa de novo."
    signal recado(string t)
    onBotao: (i) => fechar()
    Connections {
        target: controle
        function onAtualizacao(t) { aa.status = t }
        function onAtuMelhor(b) { aa.melhor = b }
        function onAtuNova(nova, atual, mb) { confirma.nova = nova; confirma.mb = mb; confirma.limitada = controle.conexaoLimitada(); confirma.abrir() }
    }
    onVisibleChanged: if (visible) auto = controle.cfgLer("atu_auto", true) !== false

    ResetRow {
        width: parent.width
        titulo: "Verificar atualização"; sub: aa.status
        classes: aa.melhor ? [".reset-row.melhor"] : []; subOuro: aa.melhor
        botao: "Verificar"; nomeBotao: "atuVerificar"
        onAcionado: { aa.status = "Procurando…"; controle.verificarAtualizacao() }
    }
    Item { width: 1; height: 8 }
    ResetRow {
        width: parent.width
        titulo: "Procurar atualização sozinho ao abrir"
        sub: "Se houver internet, o Sistema avisa quando existir versão nova. Nada se instala sem você mandar."
        botao: aa.auto ? "Ligado" : "Desligado"; nomeBotao: "atuAuto"
        onAcionado: { aa.auto = !aa.auto; controle.cfgGravar("atu_auto", aa.auto) }
    }
    Item { width: 1; height: 8 }
    ResetRow {
        width: parent.width
        titulo: "Levar para outro computador"
        sub: "Grava num pendrive o instalador, as animações, cifras, melodias e as suas configurações — pronto para instalar lá."
        botao: "Exportar"; nomeBotao: "atuExportar"
        onAcionado: aa.recado("Exportar para o pendrive no Sistema Nativo chega numa próxima peça.")
    }
    Item { width: 1; height: 14 }      // .assist-box .sis-painel{margin:0 0 14px} (o 8 da última linha colapsa nele)

    // o confirmar() da 3.0.13 por cima do assistente (o .aviso-limitada do avisoConexao entra quando o Windows diz que a
    // internet é limitada: celular roteado, franquia)
    Aviso {
        id: confirma; objectName: "confirmaAtualizar"
        parent: aa; z: 300
        property string nova: ""
        property bool limitada: false
        property int mb: 0                    // o tamanho MEDIDO do instalador na release (0 = não deu para saber)
        largura: 430; titulo: "Confirmar"
        // o número é o MEDIDO na release: só o programa. O conteúdo (animações das CIAS, cifras, melodias) já está na
        // pasta do usuário e NÃO baixa de novo (o 4.0 toca as animações que a 3.0.x baixou)
        mensagem: (limitada ? "⚠ Você está numa <b>internet limitada</b> (celular ou plano com franquia). Isto vai gastar <b>"
                              + (mb > 0 ? "cerca de " + mb + " MB" : "o tamanho do programa") + "</b> do pacote de dados "
                              + "(só o programa: as animações e cifras você já tem).<br><br>" : "")
                  + "Existe uma versão nova (<b>" + nova + "</b>). Atualizar agora?<br><br>"
                  + "O Sistema vai fechar e reabrir sozinho. Suas coisas não são apagadas, e as animações e cifras não baixam de novo."
        botoes: [{ texto: "Atualizar agora", sels: [".big-btn", ".big-btn.vermelho"], nome: "atualizarAgora" },
                 { texto: "Cancelar", sels: [".big-btn"] }]
        onBotao: (i) => { fechar(); if (i === 0) controle.atualizarAgora() }
    }
}

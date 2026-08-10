/* Ícones SVG embutidos (sem emojis — estáveis em qualquer Windows / .exe offline) */
(function () {
  const S = (p) => '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="1em" height="1em" style="vertical-align:-.15em">' + p + '</svg>';
  const F = (p) => '<svg viewBox="0 0 24 24" fill="currentColor" width="1em" height="1em" style="vertical-align:-.15em">' + p + '</svg>';
  const ICO = {
    louvor: S('<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>'),
    // livro ABERTO com lombada no meio (o anterior parecia um tablet)
    biblia: S('<path d="M12 6.5C10.3 5.2 8.2 4.5 6 4.5H3v13h3c2.2 0 4.3.7 6 2 1.7-1.3 3.8-2 6-2h3v-13h-3c-2.2 0-4.3.7-6 2z"/><path d="M12 6.5v13"/>'),
    timer: S('<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2 2M9 2h6M12 2v3"/>'),
    relogio: S('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>'),
    texto: S('<path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>'),
    fundos: S('<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="8.5" cy="9.5" r="1.5"/><path d="M21 15l-5-5L5 21"/>'),
    estilo: S('<circle cx="13.5" cy="6.5" r="1.5"/><circle cx="17.5" cy="10.5" r="1.5"/><circle cx="8.5" cy="7.5" r="1.5"/><circle cx="6.5" cy="12.5" r="1.5"/><path d="M12 2a10 10 0 1 0 0 20c1.1 0 2-.9 2-2 0-.5-.2-.9-.5-1.3-.3-.3-.5-.8-.5-1.2 0-1 .8-1.8 1.8-1.8H16a6 6 0 0 0 6-6c0-4.4-4.5-8-10-8z"/>'),
    play: F('<path d="M8 5v14l11-7z"/>'),
    ant: S('<path d="M15 18l-6-6 6-6"/>'),
    prox: S('<path d="M9 18l6-6-6-6"/>'),
    reset: S('<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/>'),
    // "Parar de projetar": era uma LUA, que não fala de projeção nenhuma.
    // Câmera de cinema cortada por um traço = parar a exibição.
    descanso: S('<rect x="2.5" y="8.5" width="12" height="9.5" rx="2"/><path d="M14.5 12.2l7-3.7v11l-7-3.7z"/><path d="M3.5 3.5l17 17"/>'),
    // violão — o modo cifra, para quem está no banquinho tocando
    violao: S('<circle cx="8.8" cy="15.2" r="5.6"/><circle cx="8.8" cy="15.2" r="1.7"/><path d="M12.8 11.2l5.6-5.6"/><path d="M16.8 3.6l3.6 3.6"/>'),
    // três bloquinhos de letras: os louvores de CIAS têm exibição própria
    cias: S('<rect x="2.5" y="12.2" width="8.6" height="8.6" rx="1.7"/><rect x="12.9" y="12.2" width="8.6" height="8.6" rx="1.7"/><rect x="7.7" y="3" width="8.6" height="8.6" rx="1.7"/>'),
    preto: F('<rect x="4" y="4" width="16" height="16" rx="2"/>'),
    congelar: S('<path d="M12 2v20M4 5l16 14M20 5L4 19M2 12h20"/>'),
    menu: S('<path d="M3 6h18M3 12h18M3 18h18"/>'),
    slides: S('<rect x="2.5" y="4" width="19" height="12.5" rx="2"/><path d="M12 16.5v3M8.5 19.5h7"/>'),
  };
  // SÍMBOLO DO SISTEMA: "S" com uma trombeta no canto inferior direito
  const MARCA = (tam) =>
    '<svg viewBox="0 0 64 64" width="' + (tam || 34) + '" height="' + (tam || 34) + '" aria-label="Sistema">' +
      '<defs><linearGradient id="sg" x1="0" y1="0" x2="0" y2="1">' +
        '<stop offset="0" stop-color="#f7e08f"/><stop offset="1" stop-color="#d8ac3c"/></linearGradient></defs>' +
      '<circle cx="32" cy="32" r="30" fill="#0f2f5e" stroke="#a31a1a" stroke-width="3"/>' +
      '<path d="M40.5 20.5c-2.6-2.2-6-3.2-9.4-3-4.6.2-8.3 3-8.5 7-.2 4.2 3.3 6.2 8.4 7.6 5.4 1.5 7.3 2.6 7.2 4.8-.1 2.3-2.6 3.9-6.2 4-3.4.1-6.6-1.1-9.1-3.3" ' +
        'fill="none" stroke="url(#sg)" stroke-width="5.5" stroke-linecap="round"/>' +
      /* trombeta: bocal, tubo com pistões e sino aberto */
      '<g transform="translate(30,44) rotate(-28)">' +
        '<rect x="0" y="5.6" width="3" height="3.4" rx="1.4" fill="url(#sg)"/>' +
        '<rect x="2.6" y="6.3" width="12" height="2" rx="1" fill="url(#sg)"/>' +
        '<path d="M14 7.3 L23.5 1.4 Q25.4 7.3 23.5 13.2 Z" fill="url(#sg)"/>' +
        '<rect x="6" y="4.4" width="1.7" height="2" rx=".7" fill="url(#sg)"/>' +
        '<rect x="9" y="4.4" width="1.7" height="2" rx=".7" fill="url(#sg)"/>' +
      '</g>' +
    '</svg>';
  function aplicar(raiz) {
    (raiz || document).querySelectorAll('.ico[data-i]').forEach(el => {
      const k = el.getAttribute('data-i');
      if (ICO[k]) el.innerHTML = ICO[k];
    });
  }
  window.Icones = { aplicar, ICO, MARCA };
  document.addEventListener('DOMContentLoaded', () => aplicar());
})();

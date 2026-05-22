// static/js/motor_shell.js
// Orquestrador HTMX: despacha comandos do backend para o DOM.
// Efeitos visuais em ui_effects.js | Audio em audio_utils.js

import {
    tocarClick, destravarAudioGlobal, playAudio, fadeOutMusic
} from './audio_utils.js';

import {
    typeText, skipCurrentTyping, animacaoTerminal,
    loopAutomatico, esperarVideo, playVideo, showElementById,
    setUiActionMap
} from './ui_effects.js';

// ------------------------------------------------------------------
// Mapa de acoes: backend envia { action, args } via HX-Trigger
// ------------------------------------------------------------------
const uiActionMap = {
    playAudio,
    fadeOutMusic,
    typeText,
    animacaoTerminal,
    loopAutomatico,
    esperarVideo,
    playVideo,
    showElementById,
};

// Injeta o mapa no modulo de efeitos (para postTypingCommand)
setUiActionMap(uiActionMap);

// ------------------------------------------------------------------
// Expoe funcoes ao escopo global para hx-on:click nos templates HTML
// (ES modules nao expõem imports automaticamente ao window)
// ------------------------------------------------------------------
window.fadeOutMusic   = fadeOutMusic;
window.skipCurrentTyping = skipCurrentTyping;

// ------------------------------------------------------------------
// Processador central de HX-Trigger
// ------------------------------------------------------------------
document.body.addEventListener('htmx:afterSwap', (evt) => {
    // Volta ao topo da caixa de dialogo apos cada swap
    const scrollBox = document.getElementById('scroll-box');
    if (scrollBox) scrollBox.scrollTop = 0;

    const header = evt.detail.xhr.getResponseHeader('HX-Trigger');
    if (!header) return;

    let triggers;
    try { triggers = JSON.parse(header); }
    catch (e) { console.error('HX-Trigger JSON invalido:', e); return; }

    (triggers.ui_commands || []).forEach(cmd => {
        const fn = uiActionMap[cmd.action];
        if (!fn) { console.warn('Acao UI desconhecida:', cmd.action); return; }

        if (cmd.action === 'typeText' && cmd.args && !Array.isArray(cmd.args)) {
            fn(cmd.args.elementId, cmd.args.fullText, cmd.args.speed,
               cmd.args.playTypingSounds, cmd.args.postTypingCommand);
        } else if (cmd.action === 'showElementById' && cmd.args && !Array.isArray(cmd.args)) {
            fn(cmd.args.elementId);
        } else {
            const args = cmd.args ? (Array.isArray(cmd.args) ? cmd.args : [cmd.args]) : [];
            fn(...args);
        }
    });
});

// ------------------------------------------------------------------
// Eventos especificos do jogo
// ------------------------------------------------------------------

// Virada 1999: fade out da trilha ao iniciar a cinematica
document.body.addEventListener('iniciar_fade_1999', () => {
    fadeOutMusic('trilha-sonora-1999', 2000);
});

// Animacao do terminal concluida: notifica o backend
document.body.addEventListener('animacao_terminal_concluida', (evt) => {
    // Garante que #ui-jogo exista antes do swap
    if (!document.getElementById('ui-jogo')) {
        const novo = document.createElement('div');
        novo.id = 'ui-jogo';
        novo.className = 'game-container ' + (document.body.dataset.tema || 'tema-a');
        const audio = document.getElementById('trilha-sonora-1999');
        (audio ? audio : document.body).insertAdjacentElement('afterend', novo);
    }

    htmx.ajax('POST', '/api/animacao-concluida', {
        values: { animacao: 'terminal_shutdown', auto_avancar: evt.detail.auto_avancar },
        target: '#ui-jogo',
        swap: 'innerHTML'
    });
});

// Som de clique em qualquer requisicao HTMX iniciada pelo usuario
document.body.addEventListener('htmx:beforeRequest', (evt) => {
    if (evt.detail.elt === document.body) return;
    tocarClick();
});

// Destrava o autoplay do browser na primeira interacao real
['click', 'keydown', 'submit'].forEach(ev =>
    document.body.addEventListener(ev, destravarAudioGlobal, { once: true })
);

// ------------------------------------------------------------------
// Input de nome na intro: som de tecla
// ------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    const inputNome = document.getElementById('nome-jogador');
    if (inputNome) {
        import('./audio_utils.js').then(({ tocarSomDeTecla }) => {
            inputNome.addEventListener('input', tocarSomDeTecla);
        });
    }
});

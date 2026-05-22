// static/js/motor_shell.js
// Orquestrador HTMX: recebe ui_commands do backend via header HX-Trigger
// e despacha para os modulos de audio (audio_utils.js) e efeitos (ui_effects.js).
//
// Protocolo HX-Trigger:
//   Backend envia: HX-Trigger: { "ui_commands": [ { action, args }, ... ] }
//   Cada action mapeia para uma funcao exportada em uiActionMap.
//
// Funcoes expostas no window (para hx-on:click nos templates):
//   window.fadeOutMusic, window.skipCurrentTyping

import {
    tocarClick, destravarAudioGlobal, playAudio, fadeOutMusic
} from './audio_utils.js';

import {
    typeText, skipCurrentTyping, animacaoTerminal,
    loopAutomatico, esperarVideo, playVideo, showElementById,
    setUiActionMap
} from './ui_effects.js';

// ---------------------------------------------------------------------------
// Mapa de acoes: action string → funcao
// ---------------------------------------------------------------------------

const uiActionMap = {
    playAudio, fadeOutMusic,
    typeText, animacaoTerminal, loopAutomatico,
    esperarVideo, playVideo, showElementById,
};

// Injeta referencia reversa em ui_effects para postTypingCommand
setUiActionMap(uiActionMap);

// Expoe no escopo global para uso em hx-on:click dos templates HTML
// (ES modules nao expõem imports automaticamente ao window)
window.fadeOutMusic      = fadeOutMusic;
window.skipCurrentTyping = skipCurrentTyping;

// ---------------------------------------------------------------------------
// Dispatcher central de HX-Trigger
// ---------------------------------------------------------------------------

document.body.addEventListener('htmx:afterSwap', (evt) => {
    // Retorna ao topo da caixa de dialogo apos cada swap de conteudo
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

        // typeText e showElementById recebem args como objeto nomeado
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

// ---------------------------------------------------------------------------
// Eventos do ciclo narrativo
// ---------------------------------------------------------------------------

// Virada 1999: fade out da trilha antes da cinematica de countdown
document.body.addEventListener('iniciar_fade_1999', () => {
    fadeOutMusic('trilha-sonora-1999', 2000);
});

// Animacao de terminal concluida: notifica o backend para avancar o estado
document.body.addEventListener('animacao_terminal_concluida', (evt) => {
    // Garante que #ui-jogo exista caso tenha sido destruido por algum swap anterior
    if (!document.getElementById('ui-jogo')) {
        const div = document.createElement('div');
        div.id        = 'ui-jogo';
        div.className = 'game-container ' + (document.body.dataset.tema || 'tema-a');
        const audio = document.getElementById('trilha-sonora-1999');
        (audio ?? document.body).insertAdjacentElement('afterend', div);
    }

    htmx.ajax('POST', '/api/animacao-concluida', {
        values: { animacao: 'terminal_shutdown', auto_avancar: evt.detail.auto_avancar },
        target: '#ui-jogo',
        swap:   'innerHTML'
    });
});

// ---------------------------------------------------------------------------
// Utilitarios globais
// ---------------------------------------------------------------------------

// Som de clique em qualquer requisicao HTMX disparada pelo usuario
document.body.addEventListener('htmx:beforeRequest', (evt) => {
    if (evt.detail.elt !== document.body) tocarClick();
});

// Desbloqueia autoplay do browser na primeira interacao real do usuario
['click', 'keydown', 'submit'].forEach(ev =>
    document.body.addEventListener(ev, destravarAudioGlobal, { once: true })
);

// Som de teclado no input de nome da intro
document.addEventListener('DOMContentLoaded', () => {
    const inputNome = document.getElementById('nome-jogador');
    if (inputNome) {
        import('./audio_utils.js').then(({ tocarSomDeTecla }) => {
            inputNome.addEventListener('input', tocarSomDeTecla);
        });
    }
});

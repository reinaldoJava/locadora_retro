// static/js/ui_effects.js
// Efeitos de DOM: digitacao, animacao terminal, controles de video/loop.
// Importado por motor_shell.js.

import { tocarSomDeTecla, stopAllTypingSounds } from './audio_utils.js';

// --- Estado da digitacao ativa ---
let _typingInterval = null;
let _typingFullText  = "";
let _typingElementId = "";

// Referencia ao mapa de acoes (injetado pelo motor_shell para evitar dependencia circular)
let _uiActionMap = null;
export function setUiActionMap(map) { _uiActionMap = map; }

// ----------------------------------------
// typeText — efeito de maquina de escrever
// ----------------------------------------
export function typeText(elementId, fullText, speed = 60, playTypingSounds = true, postTypingCommand = null) {
    if (_typingInterval) {
        clearInterval(_typingInterval);
        _typingInterval = null;
    }

    const el = document.getElementById(elementId);
    if (!el) return;

    el.innerHTML = "";
    let i = 0;
    _typingFullText  = fullText;
    _typingElementId = elementId;

    _typingInterval = setInterval(() => {
        if (i < fullText.length) {
            const letra = fullText.charAt(i);
            el.innerHTML += letra;
            if (playTypingSounds && letra !== ' ' && letra !== '\n') {
                tocarSomDeTecla();
            }
            i++;
        } else {
            clearInterval(_typingInterval);
            _typingInterval = null;
            _typingFullText  = "";
            _typingElementId = "";

            if (postTypingCommand && _uiActionMap && _uiActionMap[postTypingCommand.action]) {
                const args = postTypingCommand.args
                    ? (Array.isArray(postTypingCommand.args)
                        ? postTypingCommand.args
                        : Object.values(postTypingCommand.args))
                    : [];
                _uiActionMap[postTypingCommand.action](...args);
            }
        }
    }, speed);
}

// ----------------------------------------
// skipCurrentTyping — pula para o texto final
// ----------------------------------------
export function skipCurrentTyping() {
    if (!_typingInterval) return;
    clearInterval(_typingInterval);
    _typingInterval = null;
    const el = document.getElementById(_typingElementId);
    if (el && _typingFullText) el.innerHTML = _typingFullText;
    _typingFullText  = "";
    _typingElementId = "";
    stopAllTypingSounds();
}

// ----------------------------------------
// animacaoTerminal — overlay GIF + evento
// ----------------------------------------
export function animacaoTerminal(config) {
    let tempo_ms   = 0;
    let auto_avancar = false;

    if (typeof config === 'number') {
        tempo_ms = config;
        auto_avancar = true;
    } else if (config && typeof config === 'object') {
        tempo_ms     = config.tempo_ms    || 0;
        auto_avancar = config.auto_avancar || false;
    }

    const dispatch = () => document.body.dispatchEvent(
        new CustomEvent('animacao_terminal_concluida', {
            detail: { animacao: 'terminal_shutdown', auto_avancar }
        })
    );

    const overlay = document.getElementById('terminal-overlay');
    const gif     = document.getElementById('terminal-gif');

    if (overlay && gif) {
        overlay.classList.remove('layout-oculto');
        const src = gif.src;
        gif.src = ''; gif.src = src;          // reinicia o GIF
        setTimeout(() => {
            overlay.classList.add('layout-oculto');
            dispatch();
        }, tempo_ms);
    } else {
        dispatch();  // sem overlay: avanca mesmo assim
    }
}

// ----------------------------------------
// Utilitarios de video e loop
// ----------------------------------------
export function loopAutomatico(config) {
    if (!config || !config.tempo_ms) return;
    setTimeout(() => {
        htmx.ajax('POST', '/api/interagir', {
            values: { choice: null },
            target: '#ui-jogo',
            swap: 'innerHTML'
        });
    }, config.tempo_ms);
}

export function esperarVideo() {
    const video = document.getElementById('video-shutdown');
    if (!video) return;

    function avancar() {
        htmx.ajax('POST', '/api/interagir', {
            values: { choice: null },
            target: '#ui-jogo',
            swap: 'innerHTML'
        });
    }

    // Fallback: se o vídeo não terminar em 10s (mobile sem autoplay), avança mesmo assim
    const fallback = setTimeout(avancar, 10000);

    video.onended = () => { clearTimeout(fallback); avancar(); };
    video.onerror = () => { clearTimeout(fallback); avancar(); };
}

export function playVideo(config) {
    if (config?.id === 'video-shutdown') {
        document.getElementById('video-shutdown')?.play().catch(() => {});
    }
}

export function showElementById(elementId) {
    const el = document.getElementById(elementId);
    if (el) el.style.display = 'block';
}

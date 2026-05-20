// ==========================================
// ORQUESTRADOR DE EVENTOS HTMX / BACKEND
// ==========================================

// Importa as funções e variáveis de áudio do novo módulo
import {
    tocarClick,
    tocarSomDeTecla,
    playAudio,
    destravarAudioGlobal,
    audioContextUnmuted, // Importa a variável para o listener
    stopAllTypingSounds, // Adicionar esta função que será criada em audio_utils.js
    fadeOutMusic // Adicionar esta função que será criada em audio_utils.js
} from './audio_utils.js';

let currentTypingInterval = null; // Variável global para armazenar o intervalo de digitação atual
let currentTypingFullText = ""; // Armazena o texto completo do efeito de digitação atual
let currentTypingElementId = ""; // Armazena o ID do elemento onde a digitação está ocorrendo

// ==========================================
// EFEITOS VISUAIS ESPECÍFICOS
// ==========================================
function animacaoTerminal(configAnimacao) {
    console.log("animacaoTerminal: FUNÇÃO CHAMADA.");
    const overlay = document.getElementById('terminal-overlay');
    const gif = document.getElementById('terminal-gif');

    console.log("animacaoTerminal: Tentando encontrar overlay e gif.");
    console.log("animacaoTerminal: overlay =", overlay);
    console.log("animacaoTerminal: gif =", gif);
    console.log("animacaoTerminal: configAnimacao (raw) =", configAnimacao); // Log para ver o objeto completo

    let tempo_ms = 0;
    let auto_avancar = false;

    // Adaptação para aceitar configAnimacao como número ou objeto
    if (typeof configAnimacao === 'number') {
        tempo_ms = configAnimacao;
        auto_avancar = true; // Assumir auto_avancar se for apenas um número
    } else if (typeof configAnimacao === 'object' && configAnimacao !== null) {
        tempo_ms = configAnimacao.tempo_ms || 0;
        auto_avancar = configAnimacao.auto_avancar || false;
    }

    console.log("animacaoTerminal: tempo_ms processado =", tempo_ms);
    console.log("animacaoTerminal: auto_avancar processado =", auto_avancar);

    if (overlay && gif) {
        overlay.classList.remove('layout-oculto');
        const srcOriginal = gif.src;
        gif.src = ''; // Reseta o GIF para garantir que ele toque desde o início
        gif.src = srcOriginal;

        console.log("animacaoTerminal: Tempo de animação (tempo_ms) =", tempo_ms);

        setTimeout(() => {
            console.log("animacaoTerminal: setTimeout callback EXECUTADO AGORA. DISPATCHING EVENT FROM CALLBACK.");
            overlay.classList.add('layout-oculto');
            const event = new CustomEvent('animacao_terminal_concluida', {
                detail: {
                    animacao: 'terminal_shutdown',
                    auto_avancar: auto_avancar
                }
            });
            document.body.dispatchEvent(event);
        }, tempo_ms); // Usar o tempo_ms processado
    } else {
        console.warn("animacaoTerminal: Elementos #terminal-overlay ou #terminal-gif não encontrados. DISPATCHING EVENT FROM ELSE BLOCK.");
        const event = new CustomEvent('animacao_terminal_concluida', {
            detail: {
                animacao: 'terminal_shutdown',
                auto_avancar: auto_avancar
            }
        });
        document.body.dispatchEvent(event);
    }
}

// MODIFIED: Função genérica para efeito de digitação, chamada pelo orquestrador
// Adicionado o parâmetro postTypingCommand
function typeText(elementId, fullText, speed = 60, playTypingSounds = true, postTypingCommand = null) {
    console.log(`typeText: Tentando digitar em #${elementId} com texto: "${fullText.substring(0, Math.min(fullText.length, 50))}..." na velocidade: ${speed}ms, tocar sons: ${playTypingSounds}, comando pós-digitação: ${postTypingCommand ? postTypingCommand.action : 'nenhum'}`);

    if (currentTypingInterval) {
        clearInterval(currentTypingInterval);
        currentTypingInterval = null;
        console.log("typeText: Intervalo de digitação anterior limpo.");
    }

    const elementoTexto = document.getElementById(elementId);
    if (!elementoTexto) {
        console.error(`typeText: Elemento #${elementId} não encontrado!`);
        return;
    }
    console.log(`typeText: Elemento #${elementId} encontrado.`);

    elementoTexto.innerHTML = ""; // Limpa o texto antes de digitar
    let i = 0;
    currentTypingFullText = fullText; // Armazena o texto completo
    currentTypingElementId = elementId; // Armazena o ID do elemento
    currentTypingInterval = setInterval(() => {
        if (i < fullText.length) {
            const letraAtual = fullText.charAt(i);
            elementoTexto.innerHTML += letraAtual;

            if (playTypingSounds && letraAtual !== ' ' && letraAtual !== '\n') { // Conditional check
                tocarSomDeTecla();
            }
            i++;
        } else {
            clearInterval(currentTypingInterval);
            currentTypingInterval = null;
            currentTypingFullText = ""; // Limpa após a digitação
            currentTypingElementId = ""; // Limpa o ID do elemento
            console.log("typeText: Digitação finalizada e intervalo limpo.");

            // NOVO: Executa o comando pós-digitação, se houver
            if (postTypingCommand && uiActionMap[postTypingCommand.action]) {
                console.log(`Executando comando pós-digitação: ${postTypingCommand.action} com args:`, postTypingCommand.args);
                const argsArray = postTypingCommand.args ? (Array.isArray(postTypingCommand.args) ? command.args : Object.values(postTypingCommand.args)) : [];
                uiActionMap[postTypingCommand.action](...argsArray);
            }
        }
    }, speed);
}

// NOVA FUNÇÃO: Para a digitação atual e preenche o texto
function skipCurrentTyping() {
    if (currentTypingInterval) {
        clearInterval(currentTypingInterval);
        currentTypingInterval = null;
        const elementoTexto = document.getElementById(currentTypingElementId);
        if (elementoTexto && currentTypingFullText) {
            elementoTexto.innerHTML = currentTypingFullText;
            console.log("Digitação interrompida e texto preenchido.");
        }
        currentTypingFullText = ""; // Limpa o texto completo
        currentTypingElementId = ""; // Limpa o ID do elemento
        stopAllTypingSounds(); // Para todos os sons de tecla que estiverem tocando
    }
}

// Funções utilitárias para comandos de vídeo e loop automático
function loopAutomatico(config) {
    if (config && config.tempo_ms) {
        console.log("Interação iniciada")
        setTimeout(() => {
            htmx.ajax('POST', '/api/interagir', {
                values: { choice: null },
                target: '#ui-jogo',
                swap: 'innerHTML'
            }).catch(error => console.error("Erro no loop automático HTMX:", error));
        }, config.tempo_ms);
    }
}

function esperarVideo() {
    const video = document.getElementById("video-shutdown");
    if (video) {
        video.onended = () => {
            htmx.ajax('POST', '/api/interagir', {
                values: { choice: null },
                target: '#ui-jogo',
                swap: 'innerHTML'
            }).catch(error => console.error("Erro ao avançar após vídeo:", error));
        };
    }
}

function playVideo(config) {
    if (config && config.id === 'video-shutdown') {
        const video = document.getElementById("video-shutdown");
        if (video) {
            video.play().catch(e => console.warn("Erro ao reproduzir vídeo:", e));
        }
    }
}

// NEW: Function to show an element by its ID
function showElementById(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'block';
        console.log(`Elemento #${elementId} exibido.`);
    } else {
        console.warn(`showElementById: Elemento #${elementId} não encontrado.`);
    }
}

// Mapeamento de ações do backend para funções JavaScript
const uiActionMap = {
    "playAudio": playAudio,
    "fadeOutMusic": fadeOutMusic,
    "typeText": typeText,
    "animacaoTerminal": animacaoTerminal,
    "loopAutomatico": loopAutomatico,
    "esperarVideo": esperarVideo,
    "playVideo": playVideo,
    "showElementById": showElementById,
};

// Evento disparado pelo backend no exato momento em que a virada 1999→2000 começa
// Mesmo padrão que fadeOutMusic('trilha-sonora-intro') na intro
document.body.addEventListener('iniciar_fade_1999', () => {
    console.log("Evento iniciar_fade_1999 recebido. Iniciando fade da trilha de 1999.");
    fadeOutMusic('trilha-sonora-1999', 2000);
});

document.addEventListener('DOMContentLoaded', () => {
    const inputNome = document.getElementById("nome-jogador");
    if (inputNome) {
        inputNome.addEventListener("input", tocarSomDeTecla);
    }

    const btnStart = document.getElementById("btn-start-game");
    if (btnStart) {
        btnStart.onclick = async () => {
            tocarClick(); // Chama tocarClick para o som do botão

            // Lógica de skip da digitação e fade out da música
            skipCurrentTyping();
            fadeOutMusic('Game_1999', 2000); // Fade out da música Game_1999 em 2 segundos

            const startOverlay = document.getElementById("start-overlay");
            if (startOverlay) startOverlay.style.display = "none";

            // Carrega a transição dentro do game container (preserva o <audio> no body)
            htmx.ajax('POST', '/api/iniciar-game-transition', {
                target: '#ui-jogo',
                swap: 'innerHTML'
            }).catch(error => console.error("Erro ao iniciar transição do game:", error));
        };
    }
});

// NEW: Delegated event listener for the "iniciar sistema" button
document.body.addEventListener('click', async (event) => {
    const target = event.target.closest('#btn-iniciar-sistema'); // Assuming the button has id="btn-iniciar-sistema"
    if (target) {
        event.preventDefault(); // Prevent default form submission or navigation

        console.log("Botão 'Iniciar Sistema' clicado.");

        // 1. Desligar a música de forma suave (se alguma estiver tocando)
        // MODIFIED: Corrected audio ID for intro music fade out
        fadeOutMusic('trilha-sonora-intro', 2000); // Fade out over 2 seconds

        // 2. Carrega a animação do terminal dentro do game container (preserva o <audio> no body)
        htmx.ajax('POST', '/api/transicao-para-game-1999', {
            target: '#ui-jogo',
            swap: 'innerHTML'
        }).catch(error => console.error("Erro ao iniciar transição para o game 1999:", error));
    }
});


document.body.addEventListener('htmx:beforeRequest', (evt) => {
    if (evt.detail.elt === document.body) return; // requisições programáticas (loopAutomatico)
    if (evt.detail.elt.closest('[hx-preserve]')) return;
    if (evt.detail.elt.hasAttribute('hx-trigger') && evt.detail.elt.getAttribute('hx-trigger').includes('every')) return;
    tocarClick();
});

// CIRÚRGICO: Escuta ativa multievento para garantir liberação do Autoplay na primeira ação real
// Usa a função importada de audio_utils.js
document.body.addEventListener('click', destravarAudioGlobal, { once: true });
document.body.addEventListener('keydown', destravarAudioGlobal, { once: true });
document.body.addEventListener('submit', destravarAudioGlobal, { once: true });

// MODIFIED: Processador central de comandos de UI via HX-Trigger
document.body.addEventListener('htmx:afterSwap', (evt) => {
    const scrollBox = document.getElementById("scroll-box");
    if (scrollBox) {
        scrollBox.scrollTop = scrollBox.scrollHeight;
    }

    const hxTriggerHeader = evt.detail.xhr.getResponseHeader('HX-Trigger');
    if (hxTriggerHeader) {
        try {
            const triggers = JSON.parse(hxTriggerHeader);
            console.log("HX-Trigger recebido:", triggers);

            if (triggers.ui_commands && Array.isArray(triggers.ui_commands)) {
                triggers.ui_commands.forEach(command => {
                    if (uiActionMap[command.action]) {
                        console.log(`Executando comando UI: ${command.action} com args:`, command.args);
                        if (command.action === "typeText" && command.args && typeof command.args === 'object' && !Array.isArray(command.args)) {
                            // For typeText, map named args to positional args, including postTypingCommand
                            uiActionMap[command.action](
                                command.args.elementId,
                                command.args.fullText,
                                command.args.speed,
                                command.args.playTypingSounds,
                                command.args.postTypingCommand // Pass the new parameter
                            );
                        }
                        else if (command.action === "showElementById" && command.args && typeof command.args === 'object' && !Array.isArray(command.args)) {
                            uiActionMap[command.action](command.args.elementId);
                        }
                        else {
                            const argsArray = command.args ? (Array.isArray(command.args) ? command.args : [command.args]) : [];
                            uiActionMap[command.action](...argsArray);
                        }
                    } else {
                        console.warn(`Ação UI desconhecida: ${command.action}`);
                    }
                });
            } else {
                console.log("Nenhum 'ui_commands' encontrado no HX-Trigger ou formato inválido.");
            }
        } catch (e) {
            console.error("Erro ao parsear HX-Trigger JSON:", e, hxTriggerHeader);
        }
    }
});

// NOVO: Listener para o CustomEvent 'animacao_terminal_concluida'
document.body.addEventListener('animacao_terminal_concluida', (evt) => {
    console.log("Evento 'animacao_terminal_concluida' recebido no frontend.", evt.detail);

    // Garante que #ui-jogo existe antes do swap (pode ser destruído por swap intermediário)
    if (!document.getElementById('ui-jogo')) {
        console.warn("animacao_terminal_concluida: #ui-jogo não encontrado. Recriando sem destruir o body.");
        const novo = document.createElement('div');
        novo.id = 'ui-jogo';
        novo.className = 'game-container';
        // Insere após o audio para manter a estrutura original do body
        const audio = document.getElementById('trilha-sonora-1999');
        if (audio) {
            audio.insertAdjacentElement('afterend', novo);
        } else {
            document.body.appendChild(novo);
        }
    }

    htmx.ajax('POST', '/api/animacao-concluida', {
        values: {
            animacao: 'terminal_shutdown',
            auto_avancar: evt.detail.auto_avancar
        },
        target: '#ui-jogo',
        swap: 'innerHTML'
    }).catch(error => console.error("Erro ao enviar confirmação de animação concluída:", error));
});
// static/js/audio_utils.js

// ==========================================
// EFEITOS SONOROS
// ==========================================
export const sonsTeclado = [
    new Audio('/static/audio/tecla_1.mp3'),
    new Audio('/static/audio/tecla_2.mp3'),
    new Audio('/static/audio/tecla_3.mp3'),
    new Audio('/static/audio/tecla_4.mp3')
];

export const somClick = new Audio('/static/audio/click.mp3');

// NOVO: Array para armazenar referências aos sons de tecla ativos
let activeTypingSounds = [];

export function tocarClick() {
    const clone = somClick.cloneNode();
    clone.volume = 0.5;
    clone.play().catch(() => {});
}

let lastTypingSoundTime = 0;
const TYPING_SOUND_DEBOUNCE_MS = 70;

export function tocarSomDeTecla() {
    const now = Date.now();
    if (now - lastTypingSoundTime < TYPING_SOUND_DEBOUNCE_MS) {
        return;
    }
    lastTypingSoundTime = now;

    const indexAleatorio = Math.floor(Math.random() * sonsTeclado.length);
    const somClone = sonsTeclado[indexAleatorio].cloneNode();
    somClone.volume = 0.4;
    somClone.play().catch(e => console.error("Erro ao tocar som de tecla:", e));

    // NOVO: Adiciona o som ativo à lista e remove quando terminar
    activeTypingSounds.push(somClone);
    somClone.onended = () => {
        activeTypingSounds = activeTypingSounds.filter(s => s !== somClone);
    };
}

// NOVO: Função para parar todos os sons de tecla ativos
export function stopAllTypingSounds() {
    activeTypingSounds.forEach(som => {
        som.pause();
        som.currentTime = 0; // Reseta o tempo para o início
    });
    activeTypingSounds = []; // Limpa a lista
    console.log("Todos os sons de tecla ativos foram parados.");
}


export function transicaoDeVolume(audioElement, volumeAlvo, tempoEmMs) {
    return new Promise((resolve) => {
        const passos = 20;
        const intervalo = tempoEmMs / passos;
        const diferencaVolume = (volumeAlvo - audioElement.volume) / passos;

        const timer = setInterval(() => {
            let novoVolume = audioElement.volume + diferencaVolume;
            if (novoVolume > 1) novoVolume = 1;
            if (novoVolume < 0) novoVolume = 0;

            audioElement.volume = novoVolume;

            if ((diferencaVolume > 0 && audioElement.volume >= volumeAlvo) ||
                (diferencaVolume < 0 && audioElement.volume <= volumeAlvo)) {
                audioElement.volume = volumeAlvo;
                clearInterval(timer);
                resolve();
            }
        }, intervalo);
    });
}

// Registro de players ativos por ID (para acessar mesmo quando fora do DOM)
const _audioPlayers = {};

// Função genérica para gerenciar áudio, chamada pelo orquestrador
export function playAudio(config) {
    let player = document.getElementById(config.id);
    if (player) {
        _audioPlayers[config.id] = player; // mantém referência atualizada
    } else {
        if (!_audioPlayers[config.id]) {
            _audioPlayers[config.id] = new Audio();
        }
        player = _audioPlayers[config.id];
    }

    if (config.acao === "play_efeito") {
        const som = new Audio(config.src);
        som.play().catch(e => console.warn("Erro ao reproduzir efeito de áudio:", e));
    }
    else if (config.acao === "fade_out") {
        transicaoDeVolume(player, 0, config.tempo).then(() => {
            player.pause();
            player.currentTime = 0;
        });
    }
    else if (config.acao === "trocar_trilha") {
        player.src = config.src;
        player.volume = config.volume || 0.3;
        player.loop = config.loop !== undefined ? config.loop : true; // Trilha sonora geralmente faz loop
        player.play().catch(e => console.warn("Erro ao reproduzir trilha sonora:", e));
    }
    else if (config.acao === "play") {
        player.play().catch(e => console.warn("Erro ao reproduzir áudio:", e));
    }
    else if (config.acao === "pause") {
        player.pause();
    }
}

// NOVO: Função para fazer fade out de uma música específica
export async function fadeOutMusic(audioId, duration) {
    const audioPlayer = document.getElementById(audioId) || _audioPlayers[audioId];
    if (audioPlayer) {
        console.log(`Iniciando fade out para ${audioId} com duração de ${duration}ms.`);
        await transicaoDeVolume(audioPlayer, 0, duration);
        audioPlayer.pause();
        audioPlayer.currentTime = 0; // Opcional: reseta a música para o início
        console.log(`Fade out de ${audioId} concluído e música pausada.`);
    } else {
        console.warn(`fadeOutMusic: Elemento de áudio com ID '${audioId}' não encontrado.`);
    }
}


export let audioContextUnmuted = false; // Exportar para que possa ser acessado

export function destravarAudioGlobal() {
    if (!audioContextUnmuted) {
        console.log("destravarAudioGlobal chamada.");
        const allAudioElements = document.querySelectorAll('audio');
        allAudioElements.forEach(audio => {
            audio.muted = false;
            audio.play().then(() => {
                console.log("DOM audio reproduzido com sucesso:", audio.id || audio.src);
            }).catch(e => {
                console.error("Autoplay bloqueado para DOM audio:", audio.id || audio.src, e);
            });
        });

        sonsTeclado.forEach((audio, index) => {
            audio.muted = false;
            audio.play().then(() => {
                console.log(`sonsTeclado[${index}] reproduzido com sucesso:`, audio.src);
            }).catch(e => {
                console.error(`Autoplay bloqueado para sonsTeclado[${index}]:`, audio.src, e);
            });
        });

        audioContextUnmuted = true;
        console.log("Contexto de audio liberado pelo usuário.");
    }
}
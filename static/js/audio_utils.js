// static/js/audio_utils.js
// Gerenciamento de audio: efeitos de teclado, musica de fundo e fade.
//
// Arquitetura:
//   - sonsTeclado / somClick  — Audio objects pre-carregados (evitam latencia)
//   - _audioPlayers           — registro de players pelo id HTML; sobrevive a swaps HTMX
//   - destravarAudioGlobal()  — chamada uma vez na primeira interacao do usuario
//                               (politica de autoplay do browser exige gesto do usuario)
//   - playAudio(config)       — ponto unico acionado pelo dispatcher HX-Trigger do backend

export const sonsTeclado = [
    new Audio('/static/audio/tecla_1.ogg'),
    new Audio('/static/audio/tecla_2.ogg'),
    new Audio('/static/audio/tecla_3.ogg'),
    new Audio('/static/audio/tecla_4.ogg')
];

export const somClick = new Audio('/static/audio/click.ogg');

// -----------------------------------------------------------------------
// Efeitos de teclado
// -----------------------------------------------------------------------

let activeTypingSounds = [];
let lastTypingSoundTime = 0;
const TYPING_SOUND_DEBOUNCE_MS = 70;

export function tocarClick() {
    if (window.gameMuted) return;
    const clone = somClick.cloneNode();
    clone.volume = 0.5;
    clone.play().catch(() => {});
}

export function tocarSomDeTecla(volume = 0.4) {
    if (window.gameMuted) return;
    const now = Date.now();
    if (now - lastTypingSoundTime < TYPING_SOUND_DEBOUNCE_MS) return;
    lastTypingSoundTime = now;

    const somClone = sonsTeclado[Math.floor(Math.random() * sonsTeclado.length)].cloneNode();
    somClone.volume = Math.max(0, Math.min(1, volume));
    somClone.play().catch(e => console.error("Erro ao tocar som de tecla:", e));

    activeTypingSounds.push(somClone);
    somClone.onended = () => {
        activeTypingSounds = activeTypingSounds.filter(s => s !== somClone);
    };
}

export function stopAllTypingSounds() {
    activeTypingSounds.forEach(som => { som.pause(); som.currentTime = 0; });
    activeTypingSounds = [];
}

// -----------------------------------------------------------------------
// Controle de volume (fade suave em N passos)
// -----------------------------------------------------------------------

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

// -----------------------------------------------------------------------
// Player generico — acionado pelos ui_commands do HX-Trigger backend
// -----------------------------------------------------------------------

// Registro de players pelo id HTML; permite acesso mesmo apos swaps de innerHTML
const _audioPlayers = {};

export function playAudio(config) {
    let player = document.getElementById(config.id);
    if (player) {
        _audioPlayers[config.id] = player;
    } else {
        if (!_audioPlayers[config.id]) _audioPlayers[config.id] = new Audio();
        player = _audioPlayers[config.id];
    }

    if (config.acao === 'play_efeito') {
        if (!window.gameMuted) {
            const efeito = new Audio(config.src);
            efeito.play().catch(e => console.warn("Erro ao reproduzir efeito de áudio:", e));
        }
    } else if (config.acao === 'fade_out') {
        transicaoDeVolume(player, 0, config.tempo).then(() => {
            player.pause(); player.currentTime = 0;
        });
    } else if (config.acao === 'trocar_trilha') {
        player.src    = config.src;
        player.volume = config.volume ?? 0.3;
        player.loop   = config.loop   ?? true;
        player.muted  = !!window.gameMuted;
        player.play().catch(e => console.warn("Erro ao reproduzir trilha sonora:", e));
    } else if (config.acao === 'play') {
        player.muted = !!window.gameMuted;
        player.play().catch(e => console.warn("Erro ao reproduzir áudio:", e));
    } else if (config.acao === 'pause') {
        player.pause();
    }
}

// Muta/desmuta todos os players registrados no cache (fora do DOM)
export function muteAllPlayers(state) {
    Object.values(_audioPlayers).forEach(p => { p.muted = state; });
}

// -----------------------------------------------------------------------
// Fade out por id — exportado ao window por motor_shell para hx-on:click
// -----------------------------------------------------------------------

export async function fadeOutMusic(audioId, duration) {
    const player = document.getElementById(audioId) || _audioPlayers[audioId];
    if (!player) {
        console.warn(`fadeOutMusic: elemento '${audioId}' nao encontrado.`);
        return;
    }
    await transicaoDeVolume(player, 0, duration);
    player.pause();
    player.currentTime = 0;
}

// -----------------------------------------------------------------------
// Desbloqueio de autoplay (executado uma unica vez na primeira interacao)
// -----------------------------------------------------------------------

export let audioContextUnmuted = false;

export function destravarAudioGlobal() {
    if (audioContextUnmuted) return;
    // Respeita preferência de mute ativa antes da primeira interação
    const mutado = !!window.gameMuted;
    document.querySelectorAll('audio').forEach(a => {
        a.muted = mutado;
        if (!mutado) a.play().catch(() => {});
    });
    sonsTeclado.forEach(a => {
        a.muted = mutado;
        if (!mutado) a.play().catch(() => {});
    });
    audioContextUnmuted = true;
}

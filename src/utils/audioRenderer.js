const SOUND_FILES = [
    "harp_pling.wav",
    "game_start_countdown_01.wav",
    "game_start_countdown_02.wav",
    "game_start_countdown_03.wav",
    "game_start_countdown_final.wav"
];

const TUNING = [1, 1.0595, 1.1225, 1.1892, 1.26, 1.3348, 1.4142, 1.4983, 1.5874, 1.6818, 1.7818, 1.8877];
const OCTAVE_OFFSETS = [9, 4, 16, 16, -4];
const VOLUMES = [1, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55, 0.5, 0.45, 0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1, 0.05];

const TICKS_PER_SEC = 20;

const bufferCache = {};

const loadBuffer = async (ctx, filename) => {
    if (bufferCache[filename]) return bufferCache[filename];

    try {
        const response = await fetch(`/${filename}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const arrayBuffer = await response.arrayBuffer();
        const audioBuffer = await ctx.decodeAudioData(arrayBuffer);
        bufferCache[filename] = audioBuffer;
        return audioBuffer;
    } catch (e) {
        console.error(`Failed to load sound: ${filename}`, e);
        return null;
    }
};

export const renderBloxdAudio = async (gameEvents) => {
    if (!gameEvents || gameEvents.length === 0) return null;

    const tempCtx = new (window.AudioContext || window.webkitAudioContext)();

    await Promise.all(SOUND_FILES.map(f => loadBuffer(tempCtx, f)));

    const lastTick = gameEvents[gameEvents.length - 1].tick;
    const totalDuration = (lastTick / TICKS_PER_SEC) + 3.0; // +3s tail

    const offlineCtx = new OfflineAudioContext(2, 44100 * totalDuration, 44100);

    const compressor = offlineCtx.createDynamicsCompressor();
    compressor.threshold.value = -10;
    compressor.knee.value = 40;
    compressor.ratio.value = 12;
    compressor.attack.value = 0;
    compressor.release.value = 0.25;
    compressor.connect(offlineCtx.destination);

    gameEvents.forEach(event => {
        const soundFile = SOUND_FILES[event.sound_index];
        const buffer = bufferCache[soundFile];

        if (buffer) {
            const source = offlineCtx.createBufferSource();
            source.buffer = buffer;

            const n = event.note_index;
            const sndIdx = event.sound_index;

            let x = n + OCTAVE_OFFSETS[sndIdx];
            if (x < 0) x = 0;

            const semitoneMultiplier = TUNING[x % 12];
            const octaveMultiplier = Math.pow(2, Math.floor(x / 12));
            const playbackRate = semitoneMultiplier * octaveMultiplier * 0.0625;

            source.playbackRate.value = playbackRate;

            const gainNode = offlineCtx.createGain();
            const vol = VOLUMES[event.volume_index] || 0.5;
            gainNode.gain.value = vol;

            const startTime = event.tick / TICKS_PER_SEC;

            source.connect(gainNode);
            gainNode.connect(compressor);

            source.start(startTime);
        }
    });

    const renderedBuffer = await offlineCtx.startRendering();

    return bufferToWave(renderedBuffer, totalDuration * 44100);
};

function bufferToWave(abuffer, len) {
    let numOfChan = abuffer.numberOfChannels,
        length = len * numOfChan * 2 + 44,
        buffer = new ArrayBuffer(length),
        view = new DataView(buffer),
        channels = [],
        i, sample,
        offset = 0,
        pos = 0;

    setUint32(0x46464952); setUint32(length - 8); setUint32(0x45564157);
    setUint32(0x20746d66); setUint32(16); setUint16(1); setUint16(numOfChan);
    setUint32(abuffer.sampleRate); setUint32(abuffer.sampleRate * 2 * numOfChan);
    setUint16(numOfChan * 2); setUint16(16);
    setUint32(0x61746164); setUint32(length - pos - 4);

    for (i = 0; i < abuffer.numberOfChannels; i++) channels.push(abuffer.getChannelData(i));

    while (pos < length) {
        for (i = 0; i < numOfChan; i++) {
            sample = Math.max(-1, Math.min(1, channels[i][offset]));
            sample = (0.5 + sample < 0 ? sample * 32768 : sample * 32767) | 0;
            view.setInt16(pos, sample, true);
            pos += 2;
        }
        offset++;
    }

    return URL.createObjectURL(new Blob([buffer], { type: "audio/wav" }));

    function setUint16(data) { view.setUint16(pos, data, true); pos += 2; }
    function setUint32(data) { view.setUint32(pos, data, true); pos += 4; }
}
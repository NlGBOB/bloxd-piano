import { Midi } from '@tonejs/midi';
import { CHARSET, BASE, MAX_DELAY } from '../constants';

const PIANO_HZ = [
    27.50, 29.14, 30.87, 32.70, 34.65, 36.71, 38.89, 41.20, 43.65, 46.25, 49.00, 51.91,
    55.00, 58.27, 61.74, 65.41, 69.30, 73.42, 77.78, 82.41, 87.31, 92.50, 98.00, 103.83,
    110.00, 116.54, 123.47, 130.81, 138.59, 146.83, 155.56, 164.81, 174.61, 185.00, 196.00,
    207.65, 220.00, 233.08, 246.94, 261.63, 277.18, 293.66, 311.13, 329.63, 349.23, 369.99,
    392.00, 415.30, 440.00, 466.16, 493.88, 523.25, 554.37, 587.33, 622.25, 659.26, 698.46,
    739.99, 783.99, 830.61, 880.00, 932.33, 987.77, 1046.50, 1108.73, 1174.66, 1244.51,
    1318.51, 1396.91, 1479.98, 1567.98, 1661.22, 1760.00, 1864.66, 1975.53, 2093.00, 2217.46,
    2349.32, 2489.02, 2637.02, 2793.83, 2959.96, 3135.96, 3322.44, 3520.00, 3729.31, 3951.07, 4186.01
];

const TICKS_PER_SECOND = 20;
const PRIMARY_SOUND_NAME = "harp_pling";

const PIANO_SOUND_DATA = [
    { filename: "harp_pling", base_pitch_hz: 260.79, base_duration_sec: 0.84 },
    { filename: "game_start_countdown_01", base_pitch_hz: 329.75, base_duration_sec: 1.0 },
    { filename: "game_start_countdown_02", base_pitch_hz: 164.84, base_duration_sec: 0.99 },
    { filename: "game_start_countdown_03", base_pitch_hz: 164.87, base_duration_sec: 1.0 },
    { filename: "game_start_countdown_final", base_pitch_hz: 658.83, base_duration_sec: 1.58 },
];

const GAME_SOUND_PALETTE = PIANO_SOUND_DATA.map(s => s.filename);

const midiToHz = (note) => 440.0 * Math.pow(2, (note - 69) / 12.0);

const hzToClosestPianoNoteIndex = (targetHz) => {
    let closestIndex = 0;
    let minDiff = Infinity;
    PIANO_HZ.forEach((hz, index) => {
        const diff = Math.abs(hz - targetHz);
        if (diff < minDiff) {
            minDiff = diff;
            closestIndex = index;
        }
    });
    return closestIndex;
};

const findPianoSoundsForNote = (targetNote, availableSounds, config) => {
    const maxLayers = config?.layering?.max_layers || 2;
    const candidates = [];

    for (const soundData of availableSounds) {
        const rate = targetNote.pitch_hz / soundData.base_pitch_hz;
        const pitchedDuration = soundData.base_duration_sec / rate;
        const durationDiff = Math.abs(targetNote.duration_sec - pitchedDuration);
        const isPrimary = soundData.filename === PRIMARY_SOUND_NAME;

        if (isPrimary || (pitchedDuration <= targetNote.duration_sec)) {
            candidates.push({
                filename: soundData.filename,
                rate: rate,
                duration_diff: durationDiff
            });
        }
    }

    if (candidates.length === 0) return [];
    candidates.sort((a, b) => a.duration_diff - b.duration_diff);

    if (maxLayers <= 1) return [candidates[0]];

    const chosenSounds = [];
    const harpPling = candidates.find(c => c.filename === PRIMARY_SOUND_NAME);
    if (harpPling) chosenSounds.push(harpPling);

    const layerSoundNames = PIANO_SOUND_DATA
        .filter(s => s.filename !== PRIMARY_SOUND_NAME)
        .map(s => s.filename);

    const layerCandidates = candidates.filter(c => layerSoundNames.includes(c.filename));
    const numLayersToAdd = harpPling ? maxLayers - 1 : maxLayers;
    chosenSounds.push(...layerCandidates.slice(0, numLayersToAdd));

    return chosenSounds;
};

const encodeEvent = (soundIdx, volumeIdx, noteIdx, delay) => {
    const mD = 300;
    const mN = 88;
    const mV = 6;

    let val = delay + (noteIdx * mD) + (volumeIdx * mD * mN) + (soundIdx * mD * mN * mV);

    let chars = "";
    for (let i = 0; i < 4; i++) {
        const remainder = val % BASE;
        chars = CHARSET[remainder] + chars;
        val = Math.floor(val / BASE);
    }

    return chars;
};

export const processMidiBuffer = (arrayBuffer, config = {}) => {
    const midi = new Midi(arrayBuffer);
    const parsedNotes = [];

    midi.tracks.forEach(track => {
        track.notes.forEach(note => {
            parsedNotes.push({
                start_time: note.time,
                pitch_hz: midiToHz(note.midi),
                duration_sec: note.duration,
                velocity: note.velocity
            });
        });
    });

    parsedNotes.sort((a, b) => a.start_time - b.start_time);

    const gameEvents = [];
    let lastTick = 0;
    const soundToIndex = {};
    GAME_SOUND_PALETTE.forEach((name, idx) => soundToIndex[name] = idx);

    for (const note of parsedNotes) {
        const chosenSounds = findPianoSoundsForNote(note, PIANO_SOUND_DATA, config);
        if (!chosenSounds.length) continue;

        const noteIndex = hzToClosestPianoNoteIndex(note.pitch_hz);
        const layerSounds = chosenSounds.filter(s => s.filename !== PRIMARY_SOUND_NAME);
        const numLayers = layerSounds.length;

        const currentTick = Math.round(note.start_time * TICKS_PER_SECOND);
        let delay = currentTick - lastTick;
        if (delay < 0) delay = 0;

        for (const sound of chosenSounds) {
            let volumeIndex = (sound.filename === PRIMARY_SOUND_NAME) ? 0 : numLayers;
            if (volumeIndex > 5) volumeIndex = 5;

            gameEvents.push({
                sound_index: soundToIndex[sound.filename],
                note_index: noteIndex,
                delay: delay,
                tick: currentTick,
                volume_index: volumeIndex
            });
            delay = 0;
        }
        lastTick = currentTick;
    }

    gameEvents.sort((a, b) => a.tick - b.tick);

    let encodedString = "";
    lastTick = 0;

    for (const event of gameEvents) {
        let rawDelay = event.tick - lastTick;
        while (rawDelay >= MAX_DELAY) {
            encodedString += encodeEvent(0, 5, 0, MAX_DELAY - 1);
            rawDelay -= (MAX_DELAY - 1);
        }
        encodedString += encodeEvent(
            event.sound_index,
            event.volume_index,
            event.note_index,
            rawDelay
        );
        lastTick = event.tick;
    }

    return {
        encodedString: encodedString,
        stats: {
            total_notes: parsedNotes.length,
            mapped_events: gameEvents.length
        }
    };
};
import { Midi } from '@tonejs/midi';
import { DATA_CHARSET, PADDING_CHAR, BASE, MAX_DELAY } from '../constants';

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

const VOL_LEVELS = [
    1.00, 0.95, 0.90, 0.85, 0.80, 0.75, 0.70, 0.65, 0.60, 0.55,
    0.50, 0.45, 0.40, 0.35, 0.30, 0.25, 0.20, 0.15, 0.10, 0.05
];

const BLOCK_SIZE = 16000;
const HEADER_SIZE = 4;
const MAX_DATA_PER_BLOCK = BLOCK_SIZE - HEADER_SIZE;

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

const getClosestVolumeIndex = (targetVol) => {
    let closestIdx = 19;
    let minDiff = Infinity;

    for (let i = 0; i < VOL_LEVELS.length; i++) {
        const diff = Math.abs(targetVol - VOL_LEVELS[i]);
        if (diff < minDiff) {
            minDiff = diff;
            closestIdx = i;
        }
    }
    return closestIdx;
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

    const chosenSounds = [];
    const harpPling = candidates.find(c => c.filename === PRIMARY_SOUND_NAME);
    if (harpPling) {
        chosenSounds.push(harpPling);
    } else if (candidates.length > 0) {
        chosenSounds.push(candidates[0]);
    }

    if (maxLayers > 1) {
        const layerSoundNames = PIANO_SOUND_DATA
            .filter(s => s.filename !== PRIMARY_SOUND_NAME)
            .map(s => s.filename);

        const layerCandidates = candidates.filter(c => layerSoundNames.includes(c.filename));

        const slotsRemaining = maxLayers - chosenSounds.length;
        if (slotsRemaining > 0) {
            chosenSounds.push(...layerCandidates.slice(0, slotsRemaining));
        }
    }

    return chosenSounds;
};

const encodeLengthHeader = (length) => {
    let chars = "";
    let val = length;
    for (let i = 0; i < HEADER_SIZE; i++) {
        const remainder = val % BASE;
        chars = DATA_CHARSET[remainder] + chars;
        val = Math.floor(val / BASE);
    }
    return chars;
};

const encodeEvent = (soundIdx, volumeIdx, noteIdx, delay) => {
    const mD = MAX_DELAY;
    const mN = 88;
    const mV = 20;

    let val = delay + (noteIdx * mD) + (volumeIdx * mD * mN) + (soundIdx * mD * mN * mV);

    let chars = "";
    for (let i = 0; i < 4; i++) {
        const remainder = val % BASE;
        chars = DATA_CHARSET[remainder] + chars;
        val = Math.floor(val / BASE);
    }

    return chars;
};

const generateSimulationMidi = (gameEvents) => {
    const TICKS_PER_QUARTER = 480;
    const MIDI_TICKS_PER_GAME_TICK = 48; // 20 game ticks/sec

    const tracks = [
        [
            0, 255, 81, 3, 0x07, 0xA1, 0x20,
            0, 255, 47, 0
        ],
        []
    ];

    const noteEvents = [];

    gameEvents.forEach(evt => {
        const startMidiTick = evt.tick * MIDI_TICKS_PER_GAME_TICK;
        const midiNote = evt.note_index + 21;

        const velocity = 1;

        const soundInfo = PIANO_SOUND_DATA[evt.sound_index];
        const targetHz = PIANO_HZ[evt.note_index];
        const rate = targetHz / soundInfo.base_pitch_hz;
        const durationSec = soundInfo.base_duration_sec / rate;

        const displayDuration = Math.max(0.1, Math.min(durationSec, 0.5));

        const durationMidiTicks = Math.max(1, Math.round((displayDuration / 0.05) * MIDI_TICKS_PER_GAME_TICK));

        noteEvents.push({
            type: 0x90, // Note On
            time: startMidiTick,
            note: midiNote,
            velocity: velocity
        });

        noteEvents.push({
            type: 0x80, // Note Off
            time: startMidiTick + durationMidiTicks,
            note: midiNote,
            velocity: 0
        });
    });

    noteEvents.sort((a, b) => a.time - b.time);

    let lastTime = 0;
    const track1 = tracks[1];

    noteEvents.forEach(evt => {
        let delta = evt.time - lastTime;
        if (delta < 0) delta = 0;
        lastTime = evt.time;

        let val = delta;
        const buffer = [];
        do {
            let byte = val & 0x7F;
            val >>= 7;
            if (buffer.length > 0) byte |= 0x80;
            buffer.unshift(byte);
        } while (val > 0);

        if (buffer.length === 0) buffer.push(0);

        track1.push(...buffer);
        track1.push(evt.type, evt.note, evt.velocity);
    });

    track1.push(0, 255, 47, 0);

    const fileBytes = [
        0x4D, 0x54, 0x68, 0x64, // MThd
        0, 0, 0, 6,             // Length 6
        0, 1,                   // Format 1
        0, 2,                   // 2 Tracks
        (TICKS_PER_QUARTER >> 8) & 0xFF, TICKS_PER_QUARTER & 0xFF
    ];

    tracks.forEach(trk => {
        fileBytes.push(0x4D, 0x54, 0x72, 0x6B);
        const len = trk.length;
        fileBytes.push(
            (len >> 24) & 0xFF,
            (len >> 16) & 0xFF,
            (len >> 8) & 0xFF,
            len & 0xFF
        );
        fileBytes.push(...trk);
    });

    return new Uint8Array(fileBytes);
};


export const processMidiBuffer = (arrayBuffer, config = {}) => {
    const midi = new Midi(arrayBuffer);
    const parsedNotes = [];

    let maxVelocityFound = 1;

    midi.tracks.forEach(track => {
        track.notes.forEach(note => {
            if (note.velocity > maxVelocityFound) {
                maxVelocityFound = note.velocity;
            }
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
        const currentTick = Math.round(note.start_time * TICKS_PER_SECOND);

        const baseVolume = note.velocity / maxVelocityFound;

        let delay = currentTick - lastTick;
        if (delay < 0) delay = 0;

        for (const sound of chosenSounds) {
            gameEvents.push({
                sound_index: soundToIndex[sound.filename],
                note_index: noteIndex,
                delay: delay,
                tick: currentTick,
                temp_volume: baseVolume,
                volume_index: 0
            });
            delay = 0;
        }
        lastTick = currentTick;
    }

    gameEvents.sort((a, b) => a.tick - b.tick);

    let i = 0;

    while (i < gameEvents.length) {
        let j = i;
        while (j < gameEvents.length && gameEvents[j].tick === gameEvents[i].tick) {
            j++;
        }

        const count = j - i;

        const densityMultiplier = count > 0 ? (1.0 / Math.sqrt(count)) : 1.0;

        for (let k = i; k < j; k++) {
            const finalVol = gameEvents[k].temp_volume * densityMultiplier;
            gameEvents[k].volume_index = getClosestVolumeIndex(finalVol);
        }

        i = j;
    }

    let fullEncodedString = "";
    lastTick = 0;

    for (const event of gameEvents) {
        let rawDelay = event.tick - lastTick;

        while (rawDelay >= MAX_DELAY) {
            fullEncodedString += encodeEvent(0, 19, 0, MAX_DELAY - 1);
            rawDelay -= (MAX_DELAY - 1);
        }

        fullEncodedString += encodeEvent(
            event.sound_index,
            event.volume_index,
            event.note_index,
            rawDelay
        );
        lastTick = event.tick;
    }

    const finalBlocks = [];

    for (let i = 0; i < fullEncodedString.length; i += MAX_DATA_PER_BLOCK) {
        const chunk = fullEncodedString.slice(i, i + MAX_DATA_PER_BLOCK);
        const header = encodeLengthHeader(chunk.length);
        let block = header + chunk;

        while (block.length < BLOCK_SIZE) {
            block += PADDING_CHAR;
        }

        finalBlocks.push(block);
    }

    const simulationMidiBytes = generateSimulationMidi(gameEvents);

    return {
        encodedString: finalBlocks.join(""),
        gameEvents: gameEvents,
        simulationMidiBytes: simulationMidiBytes,
        stats: {
            total_notes: parsedNotes.length,
            mapped_events: gameEvents.length
        }
    };
};
this.S = {
    batchExecutors: [],
    currentTick: 0,
    tasks: {},

    reset: function () {
        this.currentTick = 0;
        this.tasks = {};
    },
    init: function (maxTasksPerTick = 50) {
        for (let i = 1; i <= maxTasksPerTick; i++)
            this.batchExecutors[i - 1] = new Function("t", Array.from({ length: i }, (_, j) => `t[${j}]();`).join(''));
        this.reset()
    },
    setTimeout: function (j, delay = 1) {
        const physicalTargetTick = this.currentTick + delay;
        if (!this.tasks[physicalTargetTick]) this.tasks[physicalTargetTick] = [];
        this.tasks[physicalTargetTick][this.tasks[physicalTargetTick].length] = j
        return { tickId: physicalTargetTick, taskId: this.tasks[physicalTargetTick].length - 1 };
    },
};
S.init();

tick = () => {
    const tasksForCurrentTick = S.tasks[S.currentTick];
    if (tasksForCurrentTick) {
        const len = tasksForCurrentTick.length;
        const tasksNum = 50 ^ ((len ^ 50) & -(len < 50));
        S.batchExecutors[tasksNum - 1](tasksForCurrentTick)
        delete S.tasks[S.currentTick];
    }
    S.currentTick++;
};

class MusicPlayer {
    constructor() {
        this.soundData = [
            { name: "harp_pling", hz: 260.79 },
            { name: "game_start_countdown_01", hz: 329.75 },
            { name: "game_start_countdown_02", hz: 164.84 },
            { name: "game_start_countdown_03", hz: 164.87 },
            { name: "game_start_countdown_final", hz: 658.83 }
        ];

        const charMap = "⁰¹²³⁴⁵⁶⁷⁸⁹ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐᶰⁿᵒᵖʳˢᵗᵘᵛʷˣʸᶻʱʴʵʶ₀₁₂₃₄₅₆₇₈₉ₐₑₒₓₔₕᵢⱼᵣᵤᵥₖₗₘₙₚₛₜ​‌‍⁠⁡⁢⁣⁤⁧⁩⁨⁪⁫⁬⁭⁮⁯﻿︀︁︂︃︄︅︆︇︈︉︊︋︌︍"
        this.charToIndexMap = {};
        let i = 0;
        new Function("_", "_();".repeat(charMap.length))(() => { this.charToIndexMap[charMap[i]] = i++ });

        this.SEMITONE_RATIO = 2 ** (1 / 12);
        this.volumeLevels = [1.0, 0.8 / 1, 0.8 / 2, 0.8 / 3, 0.8 / 4];
        this.CHUNK_SIZE_IN_NOTES = 100;
    }

    playSong(sounds, delays, notes, volumes) {
        if (!sounds || !delays || !notes || !volumes) {
            api.log("MusicPlayer Error: Missing song data.");
            return;
        }
        S.reset();
        this._scheduleChunk(sounds, delays, notes, volumes, 0);
    }

    _scheduleChunk(sounds, delays, notes, volumes, startIndex) {
        let relativeTicksInChunk = 0;

        const a = startIndex + this.CHUNK_SIZE_IN_NOTES;
        const b = sounds.length;
        const endIndex = b ^ ((a ^ b) & -((a - b) >>> 31));

        const iterations = endIndex - startIndex;
        let i = startIndex;
        new Function("_", "_();".repeat(iterations))(() => {
            const soundIndex = +sounds[i];
            const delayChar = delays[i];
            const noteChar = notes[i];
            const volumeIndex = +volumes[i];
            const soundInfo = this.soundData[soundIndex];
            const delaySinceLastNote = this.charToIndexMap[delayChar];
            const volume = this.volumeLevels[volumeIndex];
            const noteIndex = this.charToIndexMap[noteChar];
            const targetHz = 440.0 * (2 ** ((noteIndex - 48) / 12));
            const hz = soundInfo.hz;
            const rate = targetHz / hz;
            relativeTicksInChunk += delaySinceLastNote;
            const playNoteTask = () => api.broadcastSound(soundInfo.name, volume, rate);
            S.setTimeout(playNoteTask, relativeTicksInChunk);
            i++;
        });

        if (endIndex < sounds.length) {
            const scheduleNextChunkTask = () => this._scheduleChunk(sounds, delays, notes, volumes, endIndex);
            S.setTimeout(scheduleNextChunkTask, relativeTicksInChunk);
        }
    }
}

globalThis.MusicPlayer = new MusicPlayer(); 
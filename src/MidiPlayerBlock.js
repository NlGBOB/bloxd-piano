import React, { useEffect, useRef } from 'react';

const MidiPlayerBlock = ({ src, generatedAudioSrc, generatedMidiSrc }) => {
    const playerRef = useRef(null);
    const visualizerRef = useRef(null);

    const simPlayerRef = useRef(null);
    const simVisualizerRef = useRef(null);
    const audioRef = useRef(null);

    useEffect(() => {
        const player = playerRef.current;
        const visualizer = visualizerRef.current;
        if (player && visualizer) {
            player.addVisualizer(visualizer);
            visualizer.config = { noteHeight: 3, pixelsPerTimeStep: 40 };
        }
    }, [src]);

    useEffect(() => {
        const simPlayer = simPlayerRef.current;
        const simVisualizer = simVisualizerRef.current;
        const audio = audioRef.current;

        const SYNC_THRESHOLD = 0.04;
        const SEEK_THRESHOLD = 0.5;

        if (simPlayer && simVisualizer && audio) {
            simPlayer.addVisualizer(simVisualizer);
            simVisualizer.config = { noteHeight: 3, pixelsPerTimeStep: 40 };

            const ensureMuted = () => {
                if (simPlayer.player?.output?.gain) {
                    try {
                        simPlayer.player.output.gain.value = 0;
                    } catch (e) { }
                }
            };

            const stopEverything = () => {
                audio.pause();
                audio.currentTime = 0;
                if (simPlayer.playing) simPlayer.stop();
            };

            simPlayer.addEventListener('end', stopEverything);
            ensureMuted();

            let syncFrame;

            const tick = () => {
                if (!simPlayer || !audio) return;
                ensureMuted();

                if (!simPlayer.playing) {
                    if (!audio.paused) {
                        audio.pause();
                        audio.playbackRate = 1.0;
                    }
                    syncFrame = requestAnimationFrame(tick);
                    return;
                }

                if (simPlayer.currentTime === 0) {
                    syncFrame = requestAnimationFrame(tick);
                    return;
                }

                if (audio.paused) {
                    audio.currentTime = simPlayer.currentTime;
                    audio.play().catch(e => { });
                }

                const drift = simPlayer.currentTime - audio.currentTime;
                const absDrift = Math.abs(drift);

                if (absDrift > SEEK_THRESHOLD) {
                    audio.currentTime = simPlayer.currentTime;
                    audio.playbackRate = 1.0;
                } else if (absDrift > SYNC_THRESHOLD) {
                    const correction = Math.max(Math.min(drift, 0.1), -0.1);
                    audio.playbackRate = 1.0 + correction;
                } else {
                    audio.playbackRate = 1.0;
                }

                syncFrame = requestAnimationFrame(tick);
            };

            syncFrame = requestAnimationFrame(tick);

            return () => {
                cancelAnimationFrame(syncFrame);
                simPlayer.removeEventListener('end', stopEverything);
                stopEverything();
            };
        }
    }, [generatedMidiSrc, generatedAudioSrc]);
    return (
        <div className="step-block" style={{ borderColor: 'var(--accent-primary)' }}>
            <h2 className="step-title">
                <span className="step-count">PREVIEW</span>
                Listen & Verify
            </h2>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>

                <div style={{ minWidth: 0 }}>
                    <h3 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Original MIDI</h3>
                    <midi-player
                        ref={playerRef}
                        src={src}
                        sound-font=""
                        style={{ width: '100%' }}
                    >
                    </midi-player>

                    <div className="visualizer-container">
                        <midi-visualizer
                            ref={visualizerRef}
                            type="piano-roll"
                            src={src}
                        >
                        </midi-visualizer>
                    </div>
                </div>

                <div style={{ minWidth: 0 }}>
                    <h3 style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                        In-Game Simulation
                        {!generatedAudioSrc && <span style={{ fontSize: '0.7em', marginLeft: '0.5rem', opacity: 0.7 }}>(Processing...)</span>}
                    </h3>

                    {generatedMidiSrc ? (
                        <>
                            <audio
                                ref={audioRef}
                                src={generatedAudioSrc}
                                style={{ display: 'none' }}
                                preload="auto"
                            />

                            <midi-player
                                ref={simPlayerRef}
                                src={generatedMidiSrc}
                                sound-font=""
                                style={{ width: '100%' }}
                            >
                            </midi-player>

                            <div className="visualizer-container">
                                <midi-visualizer
                                    ref={simVisualizerRef}
                                    type="piano-roll"
                                    src={generatedMidiSrc}
                                >
                                </midi-visualizer>
                            </div>
                            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                                * Uses actual in-game sounds
                            </p>
                        </>
                    ) : (
                        <div style={{ height: '40px', background: 'rgba(255,255,255,0.05)', borderRadius: '20px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.8rem', color: '#666' }}>
                            Waiting for conversion...
                        </div>
                    )}
                </div>

            </div>
        </div>
    );
};

export default MidiPlayerBlock;
import React, { useState, useEffect } from 'react';
import './App.css';
import { processMidiBuffer } from './utils/midiProcessor';
import { SCHEDULER_CODE, MUSIC_ENGINE_CODE, TICK_WRAPPER, TICK_CORE, COORDINATE_HELPER } from './constants';
import MatrixBackground from './MatrixBackground';

function App() {
    const [file, setFile] = useState(null);
    const [config, setConfig] = useState({ maxLayers: 2 });
    const [hasTick, setHasTick] = useState(false);
    const [results, setResults] = useState(null);
    const [chunks, setChunks] = useState([]);
    const [coords, setCoords] = useState([]);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (file) processFile(file);
    }, [config.maxLayers]);

    const handleFileChange = (e) => {
        const selected = e.target.files[0];
        if (selected) {
            setFile(selected);
            processFile(selected);
        }
    };

    const processFile = async (fileToProcess) => {
        setLoading(true);
        setError(null);
        setResults(null);
        setChunks([]);
        setCoords([]);

        try {
            const arrayBuffer = await fileToProcess.arrayBuffer();
            const data = processMidiBuffer(arrayBuffer, { layering: { max_layers: config.maxLayers } });

            const chunkList = [];
            for (let i = 0; i < data.encodedString.length; i += 16000) {
                chunkList.push(data.encodedString.slice(i, i + 16000));
            }

            setChunks(chunkList);
            setCoords(chunkList.map(() => ({ x: '', y: '', z: '' })));
            setResults(data);
        } catch (err) {
            console.error(err);
            setError("Failed to parse MIDI.");
        } finally {
            setLoading(false);
        }
    };

    const handleCoordChange = (index, field, value) => {
        const newCoords = [...coords];
        newCoords[index] = { ...newCoords[index], [field]: value };
        setCoords(newCoords);
    };

    const copyToClipboard = (text, btnId) => {
        navigator.clipboard.writeText(text);
        const btn = document.getElementById(btnId);
        if (btn) {
            const original = btn.innerText;
            btn.innerText = "COPIED!";
            setTimeout(() => btn.innerText = original, 1500);
        }
    };

    const getSetupCode = () => {
        let code = SCHEDULER_CODE + "\n";
        if (!hasTick) {
            code += TICK_WRAPPER + "\n";
        }
        code += MUSIC_ENGINE_CODE + "\n";
        code += COORDINATE_HELPER;
        return code;
    };

    const getRunnerCode = () => {
        let dataFetch = "";
        let varNames = [];

        coords.forEach((c, i) => {
            const x = c.x || 0;
            const y = c.y || 0;
            const z = c.z || 0;
            dataFetch += `let p${i} = api.getBlockData(${x}, ${y}, ${z}).persisted.shared.text;\n`;
            varNames.push(`p${i}`);
        });

        const joinedVars = varNames.join("+");
        return `// --- Run Song ---\n${dataFetch}S.run(() => Music.play(${joinedVars}));`;
    };

    return (
        <div className="App">
            <MatrixBackground />
            <header>
                <h1>Bloxd Piano</h1>
                <p className="subtitle">Play custom piano MIDI in Bloxd</p>
            </header>

            <main>
                <div className="controls">
                    <div className="control-section">
                        <h2>1. Source File</h2>
                        <div className="drop-zone">
                            <input type="file" id="midiInput" accept=".mid,.midi" onChange={handleFileChange} style={{ display: 'none' }} />
                            <label htmlFor="midiInput">
                                {file ? (
                                    <div className="upload-placeholder">
                                        <span className="icon">🎵</span>
                                        <span className="file-info">{file.name}</span>
                                    </div>
                                ) : (
                                    <div className="upload-placeholder">
                                        <span className="icon">📂</span>
                                        <strong>Upload MIDI</strong>
                                    </div>
                                )}
                            </label>
                        </div>
                    </div>

                    <div className="control-section">
                        <h2>2. Configuration</h2>
                        <div className="control-item">
                            <div className="label-row">
                                <label>Max Layers</label>
                                <span className="value-badge">{config.maxLayers}</span>
                            </div>
                            <input type="range" min="1" max="5" step="1" value={config.maxLayers} onChange={(e) => setConfig({ ...config, maxLayers: parseInt(e.target.value) })} />
                        </div>
                        <div className="control-item">
                            <div className="label-row">
                                <label style={{ fontSize: '0.8rem', lineHeight: '1.2' }}>
                                    Do you already have a<br />tick function?
                                </label>
                                <label className="switch">
                                    <input type="checkbox" checked={hasTick} onChange={(e) => setHasTick(e.target.checked)} />
                                    <span className="slider"></span>
                                </label>
                            </div>
                        </div>
                    </div>

                    {loading && <div className="status-bar" style={{ borderColor: '#fbbf24', color: '#fbbf24' }}>Processing...</div>}
                </div>

                <div className="results">
                    {error && <div className="error-bar">{error}</div>}

                    {results && !loading && (
                        <div className="steps-container">
                            <div className="status-bar">
                                Success! {results.stats.mapped_events} events encoded.
                            </div>

                            {/* STEP 1 */}
                            <div className="step-block">
                                <h2 className="step-title"><span className="step-count">STEP 1/5</span> World Setup</h2>
                                <p className="step-desc">Paste this at the <strong>TOP</strong> of your World Code. (It includes a helper to find coordinates).</p>

                                <ResultCard
                                    title="WORLD CODE"
                                    content={getSetupCode()}
                                    id="btn-setup"
                                    onCopy={() => copyToClipboard(getSetupCode(), "btn-setup")}
                                />

                                {hasTick && (
                                    <div className="warning-box">
                                        <div className="warning-header">⚠️ IMPORTANT ACTION REQUIRED</div>
                                        <p>Since you already have a tick function, you must paste this line at the <strong>start</strong> of it:</p>
                                        <div className="mini-code-row">
                                            <code>{TICK_CORE}</code>
                                            <button id="btn-tick-line" onClick={() => copyToClipboard(TICK_CORE, "btn-tick-line")}>COPY</button>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* STEP 2 & 3 */}
                            <div className="step-block">
                                <h2 className="step-title"><span className="step-count">STEPS 2 & 3 / 5</span> Place Data Blocks</h2>
                                <p className="step-desc">
                                    1. Go in-game. Place <strong>{chunks.length}</strong> Code Block{chunks.length > 1 ? 's' : ''}.<br />
                                    2. Look at the chat to see the coordinates (X, Y, Z).<br />
                                    3. Paste the data below into the block(s) and enter the coordinates here.
                                </p>

                                {chunks.map((chunk, idx) => (
                                    <div key={idx} className="chunk-group">
                                        <ResultCard
                                            title={`DATA BLOCK ${idx + 1}`}
                                            content={chunk}
                                            id={`btn-chunk-${idx}`}
                                            onCopy={() => copyToClipboard(chunk, `btn-chunk-${idx}`)}
                                        />
                                        <div className="coord-inputs">
                                            <span>Enter Coordinates for Block {idx + 1}:</span>
                                            <input type="number" placeholder="X" value={coords[idx]?.x} onChange={(e) => handleCoordChange(idx, 'x', e.target.value)} />
                                            <input type="number" placeholder="Y" value={coords[idx]?.y} onChange={(e) => handleCoordChange(idx, 'y', e.target.value)} />
                                            <input type="number" placeholder="Z" value={coords[idx]?.z} onChange={(e) => handleCoordChange(idx, 'z', e.target.value)} />
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* STEP 4 */}
                            <div className="step-block">
                                <h2 className="step-title"><span className="step-count">STEP 4/5</span> Play Music</h2>
                                <p className="step-desc">
                                    Paste this code into a code block or world code to play your song.
                                </p>
                                <ResultCard
                                    title="RUNNER CODE"
                                    content={getRunnerCode()}
                                    id="btn-runner"
                                    onCopy={() => copyToClipboard(getRunnerCode(), "btn-runner")}
                                />
                            </div>

                            {/* STEP 5 (Cleanup) */}
                            <div className="step-block cleanup-block">
                                <h2 className="step-title"><span className="step-count">STEP 5/5</span> Cleanup</h2>
                                <p className="step-desc">
                                    Once you have verified the music plays correctly, go back to your World Code and <strong>remove</strong> the <code>onPlayerChangeBlock</code> function from the bottom.
                                </p>
                            </div>

                        </div>
                    )}

                    {!results && !loading && !error && (
                        <div style={{ textAlign: 'center', color: 'var(--text-secondary)', marginTop: '4rem', border: '2px dashed var(--border-color)', padding: '4rem', background: 'rgba(24, 27, 33, 0.8)' }}>
                            WAITING FOR INPUT...
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}

const ResultCard = ({ title, content, onCopy, id }) => (
    <div className="result-card">
        <div className="card-header">
            <h3>{title}</h3>
            <button id={id} onClick={onCopy} className="copy-btn">COPY</button>
        </div>
        <textarea readOnly value={content} spellCheck="false" />
    </div>
);

export default App;
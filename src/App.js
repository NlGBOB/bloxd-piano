import React, { useState, useEffect } from 'react';
import './App.css';
import { processMidiBuffer } from './utils/midiProcessor';
import { SETUP_CODE } from './constants';

function App() {
    const [file, setFile] = useState(null);
    const [config, setConfig] = useState({ maxLayers: 2 });
    const [results, setResults] = useState(null);
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

        try {
            const arrayBuffer = await fileToProcess.arrayBuffer();
            const data = processMidiBuffer(arrayBuffer, { layering: { max_layers: config.maxLayers } });
            setResults(data);
        } catch (err) {
            console.error(err);
            setError("Failed to parse MIDI.");
        } finally {
            setLoading(false);
        }
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

    const getChunks = (str) => {
        const chunkSize = 16000;
        const chunks = [];
        for (let i = 0; i < str.length; i += chunkSize) {
            chunks.push(str.slice(i, i + chunkSize));
        }
        return chunks;
    };

    return (
        <div className="App">
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
                    </div>

                    {loading && <div className="status-bar" style={{ borderColor: '#fbbf24', color: '#fbbf24' }}>Processing...</div>}
                </div>

                <div className="results">
                    {error && <div className="error-bar">{error}</div>}

                    {results && !loading && (
                        <>
                            <div className="status-bar">
                                Success! {results.stats.mapped_events} events encoded.
                            </div>

                            <div className="results-grid" style={{ gridTemplateColumns: '1fr' }}>
                                <ResultCard
                                    title="1. WORLD CODE (Setup)"
                                    content={SETUP_CODE}
                                    id="btn-setup"
                                    onCopy={() => copyToClipboard(SETUP_CODE, "btn-setup")}
                                />

                                {getChunks(results.encodedString).map((chunk, idx) => (
                                    <ResultCard
                                        key={idx}
                                        title={`2.${idx + 1} MUSIC DATA ${idx > 0 ? '(Cont.)' : ''}`}
                                        content={`Music.play("${chunk}")`}
                                        id={`btn-chunk-${idx}`}
                                        onCopy={() => copyToClipboard(`Music.play("${chunk}")`, `btn-chunk-${idx}`)}
                                    />
                                ))}

                                <ResultCard
                                    title="3. STOP BUTTON CODE"
                                    content="Music.stop()"
                                    id="btn-stop"
                                    onCopy={() => copyToClipboard("Music.stop()", "btn-stop")}
                                />
                            </div>
                        </>
                    )}

                    {!results && !loading && !error && (
                        <div style={{ textAlign: 'center', color: 'var(--text-secondary)', marginTop: '4rem', border: '2px dashed var(--border-color)', padding: '4rem' }}>
                            WAITING FOR INPUT...
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}

const ResultCard = ({ title, content, onCopy, id }) => (
    <div className="result-card" style={{ height: 'auto', minHeight: '150px' }}>
        <div className="card-header">
            <h3>{title}</h3>
            <button id={id} onClick={onCopy} className="copy-btn">COPY</button>
        </div>
        <textarea readOnly value={content} spellCheck="false" style={{ height: '120px' }} />
    </div>
);

export default App;
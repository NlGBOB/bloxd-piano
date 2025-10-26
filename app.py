import streamlit as st
import os
import json
import shutil
import tempfile
from io import StringIO
import sys
from processor import run_processing

st.set_page_config(page_title="MIDI to Bloxd Converter", layout="wide", initial_sidebar_state="auto")

def inject_css():
    st.markdown("""
        <style>
            /* --- Root Variables for Easy Theming --- */
            :root {
                --bg-color-main: #0E1117;
                --bg-color-secondary: #1C2026;
                --bg-color-tertiary: #262730;
                --text-color-primary: #FAFAFA;
                --text-color-secondary: #A0AEC0;
                --accent-color: #38BDF8; /* A nice, vibrant blue */
                --border-color: #333742;
            }

            html, body, [class*="st-"] {
                background-color: var(--bg-color-main);
                color: var(--text-color-primary);
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                font-size: 16px;
            }
            h1 { font-size: 3rem; font-weight: 700; }
            h3 { font-size: 1.75rem; font-weight: 600; }
            h4 { font-size: 1.25rem; font-weight: 500; }

            #MainMenu, footer { visibility: hidden; }
            header[data-testid="stHeader"] { display: none; }

            .main-content-wrapper {
                max-width: 1200px;
                margin: auto;
                padding: 1rem;
                text-align: center;
            }
            .made-by {
                width: 100%;
                text-align: right;
                color: var(--text-color-secondary);
                font-size: 0.9rem;
                padding: 0.5rem 1rem 0 0;
            }
            
            .upload-container {
                background-color: var(--bg-color-secondary);
                border: 1px dashed var(--border-color);
                border-radius: 0.75rem;
                padding: 4rem 2rem;
                margin-top: 2rem;
                transition: all 0.2s ease-in-out;
            }
            .upload-container:hover {
                border-color: var(--accent-color);
                box-shadow: 0 0 15px rgba(56, 189, 248, 0.1);
            }
            .stFileUploader > div > div > button {
                background-color: var(--accent-color);
                color: var(--bg-color-main);
                border: none;
                font-weight: 600;
            }
            
            [data-testid="stSidebar"] {
                background-color: var(--bg-color-secondary);
                border-right: 1px solid var(--border-color);
            }
            [data-testid="stSidebar"] h2 { font-size: 1.5rem; }
            [data-testid="stSidebar"] .stButton button {
                background-color: var(--accent-color);
                color: var(--bg-color-main);
                border: none;
                font-weight: 600;
            }
            [data-testid="stSidebar"] .stButton button.secondary {
                background-color: var(--bg-color-tertiary);
                color: var(--text-color-primary);
            }

            .results-header a { color: var(--accent-color); text-decoration: none; }
            .results-header a:hover { text-decoration: underline; }

            .stCodeBlock {
                background-color: var(--bg-color-secondary);
                border: 1px solid var(--border-color);
                border-radius: 0.5rem;
            }
        </style>
    """, unsafe_allow_html=True)

def initialize_state():
    if 'step' not in st.session_state: st.session_state.step = 'upload'
    if 'results' not in st.session_state: st.session_state.results = None
    if 'midi_data' not in st.session_state: st.session_state.midi_data = None
    if 'midi_filename' not in st.session_state: st.session_state.midi_filename = None

def process_and_store_results(midi_data, midi_filename, config_data):
    with st.spinner("Processing your MIDI file..."):
        with tempfile.TemporaryDirectory() as temp_dir:
            midi_path = os.path.join(temp_dir, midi_filename)
            with open(midi_path, "wb") as f: f.write(midi_data)

            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()

            output_dir = run_processing(
                midi_file_path=midi_path, config_data=config_data,
                render_preview_flag=True, sound_folder_path="sounds"
            )
            
            sys.stdout = old_stdout
            results = {"log": captured_output.getvalue()}
            if output_dir:
                base_name = os.path.splitext(midi_filename)[0]
                file_map = {
                    "sounds": f"1_{base_name}_sounds.txt", "delays": f"2_{base_name}_delays.txt",
                    "notes": f"3_{base_name}_notes.txt", "volumes": f"4_{base_name}_volumes.txt",
                    "preview": f"8_{base_name}_preview.wav"
                }
                for key, fname in file_map.items():
                    fpath = os.path.join(output_dir, fname)
                    if os.path.exists(fpath):
                        with open(fpath, "rb") as f: results[key] = f.read()
            st.session_state.results = results
            st.session_state.step = 'results'

def upload_view():
    st.markdown("<div class='made-by'>Made by chmod</div>", unsafe_allow_html=True)
    st.markdown("<div class='main-content-wrapper'>", unsafe_allow_html=True)
    st.title("MIDI to Bloxd Music Converter")
    st.markdown("A simple and secure tool to convert your MIDI files into game-ready music data.", unsafe_allow_html=True)
    
    st.markdown("<div class='upload-container'>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Drag and drop file here", type=['mid', 'midi'], label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)
    
    if uploaded_file:
        st.session_state.midi_data = uploaded_file.getvalue()
        st.session_state.midi_filename = uploaded_file.name
        st.session_state.step = 'processing'
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def results_view():
    results = st.session_state.results
    
    with st.sidebar:
        st.header("Configuration")
        st.caption(f"Editing for: **{st.session_state.midi_filename}**")
        
        default_config = {
            "palette": ["harp_pling", "game_start_countdown_01", "game_start_countdown_02", "game_start_countdown_03", "game_start_countdown_final"],
            "layering": {"comment": "Max sounds per note. 1 = no layering.", "max_layers": 2}
        }
        config_text = st.text_area(
            "Config JSON", value=json.dumps(default_config, indent=2),
            height=250, key="config_json"
        )
        if st.button("Process Again", use_container_width=True):
            try:
                json.loads(st.session_state.config_json)
                st.session_state.step = 'processing'
                st.rerun()
            except json.JSONDecodeError:
                st.error("Invalid JSON format.")

        st.divider()
        if st.button("Convert Another File", use_container_width=True, type="secondary"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

    st.markdown("<div class='made-by'>Made by chmod</div>", unsafe_allow_html=True)
    st.markdown("<div class='main-content-wrapper results-header'>", unsafe_allow_html=True)
    st.markdown("<h3>Conversion Successful!</h3>", unsafe_allow_html=True)
    st.markdown("Confused what to do now? Read the <a href='https://github.com/NlGBOB/bloxd-piano' target='_blank'>documentation</a>.", unsafe_allow_html=True)
    
    if results.get("preview"):
        st.markdown("<p style='text-align: center; color: var(--text-color-secondary); margin-top:1rem;'>This is approximately how your MIDI will sound in-game:</p>", unsafe_allow_html=True)
        st.audio(results["preview"], format='audio/wav')
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='main-content-wrapper'>", unsafe_allow_html=True)
    cols = st.columns(4, gap="large")
    file_info = [("1. Sounds", "sounds"), ("2. Delays", "delays"), ("3. Notes", "notes"), ("4. Volumes", "volumes")]

    for i, col in enumerate(cols):
        with col:
            title, key = file_info[i]
            st.markdown(f"<h4>{title}</h4>", unsafe_allow_html=True)
            content = results.get(key, b"").decode('utf-8', errors='ignore')
            st.code(content, language=None)
    st.markdown("</div>", unsafe_allow_html=True)

inject_css()
initialize_state()

if st.session_state.step == 'upload':
    upload_view()
elif st.session_state.step == 'processing':
    config_str = st.session_state.get("config_json", '{}')
    try:
        config_data = json.loads(config_str)
    except json.JSONDecodeError:
        config_data = {}
        
    process_and_store_results(st.session_state.midi_data, st.session_state.midi_filename, config_data)
    st.rerun()
elif st.session_state.step == 'results':
    results_view()
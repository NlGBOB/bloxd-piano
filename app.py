import streamlit as st
import os
import json
import shutil
import tempfile
from io import StringIO
import sys
import base64
from processor import run_processing

st.set_page_config(page_title="MIDI to Bloxd Converter", layout="wide", initial_sidebar_state="auto")

def inject_css():
    st.markdown("""
        <style>
            html, body, [class*="st-"] {
                background-color: #0E1117;
                color: #FAFAFA;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                font-size: 16px;
            }
            h1 { font-size: 2.5rem; }
            h3 { font-size: 1.5rem; }
            
            #MainMenu, footer { visibility: hidden; }
            header[data-testid="stHeader"] { display: none; }
            
            .main-content-wrapper {
                max-width: 1100px;
                margin: auto;
                padding: 1rem 0;
                text-align: center;
            }
            .made-by {
                width: 100%;
                text-align: right;
                color: #777;
                font-size: 0.9rem;
                padding: 0.5rem 1rem 0 0;
            }
            
            .stFileUploader {
                border: 1px solid #262730;
                background-color: #1C2026;
                border-radius: 0.5rem;
                padding: 1rem;
            }
            .stFileUploader > div > div > button {
                background-color: #333742;
                color: #FAFAFA;
                border: 1px solid #4A4F5A;
            }
            
            .results-header a { color: #4B8BFF; text-decoration: none; }
            .results-header a:hover { text-decoration: underline; }

            .result-column .stTextArea textarea {
                font-family: monospace;
                background-color: #0E1117;
                border: 1px solid #262730;
                height: 300px !important;
                color: #FAFAFA;
                resize: none; /* Disable resizing */
            }
            .result-title-container {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                margin-bottom: 1rem;
            }
            .copy-icon {
                cursor: pointer;
                opacity: 0.6;
                transition: opacity 0.2s ease;
            }
            .copy-icon:hover {
                opacity: 1.0;
            }
            
        </style>
    """, unsafe_allow_html=True)

def initialize_state():
    if 'step' not in st.session_state:
        st.session_state.step = 'upload'
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'midi_data' not in st.session_state:
        st.session_state.midi_data = None
    if 'midi_filename' not in st.session_state:
        st.session_state.midi_filename = None

def get_copy_button_html(content_to_copy, button_id):
    b64_content = base64.b64encode(content_to_copy.encode()).decode()
    copy_icon_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>"""
    
    onclick_js = f"""
        const textToCopy = atob('{b64_content}');
        navigator.clipboard.writeText(textToCopy).then(() => {{
            const iconElement = document.getElementById('{button_id}');
            const originalColor = iconElement.style.stroke;
            iconElement.style.stroke = '#4CAF50'; // Green color on success
            setTimeout(() => {{ iconElement.style.stroke = originalColor; }}, 1500);
        }});
    """
    return f"<span id='{button_id}' class='copy-icon' onclick=\"{onclick_js}\" title='Copy to clipboard'>{copy_icon_svg}</span>"

def process_and_store_results(midi_data, midi_filename, config_data):
    with st.spinner("Processing your MIDI file..."):
        with tempfile.TemporaryDirectory() as temp_dir:
            midi_path = os.path.join(temp_dir, midi_filename)
            with open(midi_path, "wb") as f:
                f.write(midi_data)

            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()

            output_dir = run_processing(
                midi_file_path=midi_path,
                config_data=config_data,
                render_preview_flag=True,
                sound_folder_path="sounds"
            )
            
            sys.stdout = old_stdout

            results = {"log": captured_output.getvalue()}
            if output_dir:
                base_name = os.path.splitext(midi_filename)[0]
                file_map = {
                    "sounds": f"1_{base_name}_sounds.txt",
                    "delays": f"2_{base_name}_delays.txt",
                    "notes": f"3_{base_name}_notes.txt",
                    "volumes": f"4_{base_name}_volumes.txt",
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
    st.markdown("A simple and secure tool to convert your MIDI files into game-ready music data.")
    st.markdown("<br>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Drag and drop file here", type=['mid', 'midi'], label_visibility="collapsed")
    
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
            "Config JSON",
            value=json.dumps(default_config, indent=2),
            height=200,
            key="config_json"
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
        st.markdown("<p style='text-align: center; color: #AAA; margin-top:1rem;'>This is approximately how your MIDI will sound in-game:</p>", unsafe_allow_html=True)
        st.audio(results["preview"], format='audio/wav')
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='main-content-wrapper'>", unsafe_allow_html=True)
    cols = st.columns(4, gap="medium")
    file_info = [("1. Sounds", "sounds"), ("2. Delays", "delays"), ("3. Notes", "notes"), ("4. Volumes", "volumes")]

    for i, col in enumerate(cols):
        with col:
            title, key = file_info[i]
            content = results.get(key, b"").decode('utf-8', errors='ignore')
            copy_html = get_copy_button_html(content, f"copy-btn-{key}")
            
            st.markdown(f"<div class='result-title-container'><h4>{title}</h4>{copy_html}</div>", unsafe_allow_html=True)
            st.text_area("Content", value=content, disabled=True, label_visibility="collapsed", key=f"text_{key}")
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
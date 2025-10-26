import streamlit as st
import os
import json
import shutil
import tempfile
from io import StringIO
import sys
import base64
from processor import run_processing

st.set_page_config(page_title="MIDI to Bloxd Converter", layout="wide", initial_sidebar_state="collapsed")

def inject_css():
    st.markdown("""
        <style>
            html, body, [class*="st-"] {
                background-color: #0E1117;
                color: #FAFAFA;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
            }
            /* Hide the default Streamlit header and footer */
            #MainMenu, footer { visibility: hidden; }
            header[data-testid="stHeader"] { display: none; }
            
            .main-content-wrapper {
                max-width: 900px;
                margin: auto;
                padding-top: 2rem;
                text-align: center;
            }
            .made-by {
                width: 100%;
                text-align: right;
                color: #777;
                font-size: 0.9rem;
                padding-right: 1rem;
            }
            
            .stFileUploader {
                border: 1px solid #262730;
                background-color: #1C2026;
                border-radius: 0.5rem;
                padding: 1rem;
                width: 100%;
            }
            .stFileUploader > div > div > button {
                background-color: #333742;
                color: #FAFAFA;
                border: 1px solid #4A4F5A;
                border-radius: 0.5rem;
            }
            .stFileUploader > div > div > button:hover {
                background-color: #4A4F5A;
                color: #FAFAFA;
                border-color: #5C626F;
            }

            .results-header a {
                color: #4B8BFF;
                text-decoration: none;
            }
            .results-header a:hover {
                text-decoration: underline;
            }
            .result-column {
                background-color: #1C2026;
                border: 1px solid #262730;
                border-radius: 0.5rem;
                padding: 1rem;
                text-align: center;
            }
            .result-column .stTextArea textarea {
                font-family: monospace;
                background-color: #0E1117;
                border: 1px solid #262730;
                height: 300px !important;
                color: #FAFAFA;
            }
            .copy-button {
                background-color: #333742;
                color: #FAFAFA;
                border: 1px solid #4A4F5A;
                border-radius: 0.5rem;
                padding: 0.3rem 0.8rem;
                cursor: pointer;
                transition: background-color 0.2s ease;
                margin-bottom: 1rem;
            }
            .copy-button:hover {
                background-color: #4A4F5A;
            }
            .copy-button:active {
                background-color: #5C626F;
            }
            
        </style>
    """, unsafe_allow_html=True)

def initialize_state():
    if 'step' not in st.session_state:
        st.session_state.step = 'upload'
    if 'results' not in st.session_state:
        st.session_state.results = None

def get_copy_button_html(content_to_copy, button_id):
    b64_content = base64.b64encode(content_to_copy.encode()).decode()
    onclick_js = f"""
        const text = atob('{b64_content}');
        navigator.clipboard.writeText(text).then(() => {{
            const button = document.getElementById('{button_id}');
            const originalText = button.innerText;
            button.innerText = 'Copied!';
            setTimeout(() => {{ button.innerText = originalText; }}, 1500);
        }}, () => {{
            alert('Failed to copy to clipboard.');
        }});
    """
    return f"<button id='{button_id}' class='copy-button' onclick=\"{onclick_js}\">Copy</button>"

def process_and_store_results(midi_data, midi_filename):
    with st.spinner("Processing your MIDI file..."):
        with tempfile.TemporaryDirectory() as temp_dir:
            midi_path = os.path.join(temp_dir, midi_filename)
            with open(midi_path, "wb") as f:
                f.write(midi_data)

            config = {
                "palette": ["harp_pling", "game_start_countdown_01", "game_start_countdown_02", "game_start_countdown_03", "game_start_countdown_final"],
                "layering": {"comment": "Max sounds per note. 1 = no layering.", "max_layers": 2}
            }

            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()

            output_dir = run_processing(
                midi_file_path=midi_path,
                config_data=config,
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
                        with open(fpath, "rb") as f:
                            results[key] = f.read()
            st.session_state.results = results
            st.session_state.step = 'results'

def upload_view():
    st.markdown("<div class='made-by'>Made by chmod</div>", unsafe_allow_html=True)
    st.markdown("<div class='main-content-wrapper'>", unsafe_allow_html=True)
    st.title("MIDI to Bloxd Music Converter")
    st.markdown("A simple and secure tool to convert your MIDI files into game-ready music data.", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Drag and drop file here",
        type=['mid', 'midi'],
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        process_and_store_results(uploaded_file.getvalue(), uploaded_file.name)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def results_view():
    results = st.session_state.results
    
    st.markdown("<div class='made-by'>Made by chmod</div>", unsafe_allow_html=True)
    st.markdown("<div class='main-content-wrapper results-header'>", unsafe_allow_html=True)
    st.markdown("""
        <h3>Conversion Successful!</h3>
        <p>Confused what to do now? Read the <a href="https://github.com/NlGBOB/bloxd-piano" target="_blank">documentation</a>.</p>
        <p style='color:#AAA; margin-top: -10px;'>Your goal is to copy the contents of the 4 boxes below into 4 separate code blocks in the game.</p>
    """, unsafe_allow_html=True)

    if results.get("preview"):
        st.markdown("<p style='text-align: center; color: #AAA;'>This is approximately how your MIDI will sound in-game:</p>", unsafe_allow_html=True)
        st.audio(results["preview"], format='audio/wav')
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    cols = st.columns(4, gap="medium")
    file_info = [
        ("1. Sounds", "sounds", "copy-btn-1"),
        ("2. Delays", "delays", "copy-btn-2"),
        ("3. Notes", "notes", "copy-btn-3"),
        ("4. Volumes", "volumes", "copy-btn-4")
    ]

    for i, col in enumerate(cols):
        with col:
            title, key, btn_id = file_info[i]
            st.markdown(f"<div class='result-column'>", unsafe_allow_html=True)
            st.subheader(title)
            content = results.get(key, b"").decode('utf-8', errors='ignore')
            st.markdown(get_copy_button_html(content, btn_id), unsafe_allow_html=True)
            st.text_area("Content", value=content, disabled=True, label_visibility="collapsed", key=f"text_{key}")
            st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div style='text-align:center; margin-top: 2rem;'>", unsafe_allow_html=True)
    if st.button("Convert Another File"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

inject_css()
initialize_state()

if st.session_state.step == 'upload':
    upload_view()
elif st.session_state.step == 'results':
    results_view()

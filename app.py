import streamlit as st
import os
import json
import shutil
import tempfile
from io import StringIO
import sys
from processor import run_processing

st.set_page_config(page_title="MIDI to Bloxd Converter", layout="wide")

def inject_css():
    st.markdown("""
        <style>
            /* Center the main content */
            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            .main-content-wrapper {
                max-width: 800px;
                margin: auto;
                text-align: center;
            }
            /* Style the file uploader */
            .stFileUploader > div > div {
                border: 2px dashed #cccccc;
                background-color: #f9f9f9;
                padding: 3rem;
                border-radius: 10px;
            }
            .stFileUploader > div > div:hover {
                background-color: #f0f0f0;
                border-color: #ff4b4b;
            }
            /* Style the results tabs */
            .stTabs [data-baseweb="tab-list"] {
                justify-content: center;
            }
            .stTextArea textarea {
                font-family: monospace;
                font-size: 0.9rem;
                height: 300px !important;
            }
            h1, h3 {
                text-align: center;
            }
        </style>
    """, unsafe_allow_html=True)

def initialize_state():
    if 'step' not in st.session_state:
        st.session_state.step = 'upload'
    if 'midi_data' not in st.session_state:
        st.session_state.midi_data = None
    if 'midi_filename' not in st.session_state:
        st.session_state.midi_filename = None
    if 'results' not in st.session_state:
        st.session_state.results = None

def process_and_store_results(midi_data, midi_filename, config_data, render_preview):
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
                render_preview_flag=render_preview,
                sound_folder_path="sounds"
            )
            
            sys.stdout = old_stdout
            log_output = captured_output.getvalue()

            results = {"log": log_output}
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
                
                zip_path_base = os.path.join(temp_dir, f"{base_name}_results")
                shutil.make_archive(zip_path_base, 'zip', output_dir)
                with open(f"{zip_path_base}.zip", "rb") as f:
                    results["zip"] = f.read()
            st.session_state.results = results
            st.session_state.step = 'results'

def upload_view():
    st.markdown("<div class='main-content-wrapper'>", unsafe_allow_html=True)
    st.title("MIDI to Bloxd Music Converter")
    st.markdown("A simple and secure tool to convert your MIDI files into game-ready music data.")
    
    uploaded_file = st.file_uploader(
        "Select MIDI file",
        type=['mid', 'midi'],
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        st.session_state.midi_data = uploaded_file.getvalue()
        st.session_state.midi_filename = uploaded_file.name
        st.session_state.step = 'processing'
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

def results_view():
    results = st.session_state.results
    
    with st.sidebar:
        st.subheader("Configuration")
        st.caption(f"Editing for: **{st.session_state.midi_filename}**")
        
        default_config = {
            "palette": ["harp_pling", "game_start_countdown_01", "game_start_countdown_02", "game_start_countdown_03", "game_start_countdown_final"],
            "layering": {"comment": "Max sounds per note. 1 = no layering.", "max_layers": 2}
        }
        config_text = st.text_area(
            "Config JSON",
            value=json.dumps(default_config, indent=4),
            height=250,
            key="config_json"
        )
        render_preview = st.checkbox("Render .wav audio preview", value=True, key="render_preview")

        if st.button("Process Again", use_container_width=True):
            try:
                new_config = json.loads(st.session_state.config_json)
                st.session_state.step = 'processing'
                st.rerun()
            except json.JSONDecodeError:
                st.error("Invalid JSON format.")

        st.divider()
        if results and "zip" in results:
            st.download_button(
                label="Download Full Package (.zip)",
                data=results["zip"],
                file_name=f"{os.path.splitext(st.session_state.midi_filename)[0]}_results.zip",
                mime="application/zip",
                use_container_width=True
            )
        
        if st.button("Start Over", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    st.header("Conversion Results")
    if results.get("preview"):
        st.audio(results["preview"], format='audio/wav')
    
    tab_titles = ["Sounds", "Delays", "Notes", "Volumes"]
    tab_keys = ["sounds", "delays", "notes", "volumes"]
    tabs = st.tabs(tab_titles)

    for i, tab in enumerate(tabs):
        with tab:
            content = results.get(tab_keys[i], b"").decode('utf-8', errors='ignore')
            st.text_area(f"Content for {tab_titles[i]}", value=content, height=300, disabled=True, label_visibility="collapsed")

    with st.expander("Show Processing Diagnostics"):
        st.code(results.get("log", "No log available."), language="bash")

inject_css()
initialize_state()

if st.session_state.step == 'upload':
    upload_view()
elif st.session_state.step == 'processing':
    config_data = json.loads(st.session_state.get("config_json", json.dumps({})))
    render_flag = st.session_state.get("render_preview", True)
    process_and_store_results(st.session_state.midi_data, st.session_state.midi_filename, config_data, render_flag)
    st.rerun()
elif st.session_state.step == 'results':
    results_view()
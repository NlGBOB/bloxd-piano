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

def inject_tailwind():
    st.markdown("""
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            #MainMenu, footer { visibility: hidden; }
            header[data-testid="stHeader"] { display: none; }
            .stFileUploader > div > div {
                border: none;
                background: transparent;
                padding: 0;
            }
            .stFileUploader > div > div > button {
                background-color: #3b82f6; /* A nice blue */
                color: white;
                border: none;
                border-radius: 0.375rem;
                font-weight: 500;
            }
            .stFileUploader > div > div > button:hover {
                background-color: #2563eb;
            }
            [data-testid="stSidebar"] {
                background-color: #f9fafb; /* Light gray bg */
                border-right: 1px solid #e5e7eb;
            }
            .stCodeBlock div[data-testid="stCopyButton"] > button {
                background-color: rgba(255, 255, 255, 0.5);
                border: 1px solid #d1d5db;
            }
            .stCodeBlock div[data-testid="stCopyButton"] > button:hover {
                 background-color: rgba(255, 255, 255, 0.8);
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
    st.markdown("<div class='text-right text-sm text-gray-500 pr-4 pt-2'>Made by chmod</div>", unsafe_allow_html=True)
    st.markdown("<div class='max-w-4xl mx-auto text-center py-12 px-4'>", unsafe_allow_html=True)
    st.markdown("<h1 class='text-5xl font-bold text-gray-800'>MIDI to Bloxd Music Converter</h1>", unsafe_allow_html=True)
    st.markdown("<p class='mt-4 text-lg text-gray-600'>A simple and secure tool to convert your MIDI files into game-ready music data.</p>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class='mt-10 border-2 border-dashed border-gray-300 rounded-xl p-8 bg-gray-50 hover:bg-gray-100 hover:border-blue-500 transition-all'>
    """, unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Drag and drop file here", 
        type=['mid', 'midi'], 
        label_visibility="collapsed"
    )
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

    st.markdown("<div class='text-right text-sm text-gray-500 pr-4 pt-2'>Made by chmod</div>", unsafe_allow_html=True)
    st.markdown("<div class='max-w-7xl mx-auto py-8 px-4'>", unsafe_allow_html=True)
    st.markdown("<div class='text-center'>", unsafe_allow_html=True)
    st.markdown("<h3 class='text-4xl font-bold text-gray-800'>Conversion Successful!</h3>", unsafe_allow_html=True)
    st.markdown("<p class='mt-2 text-gray-600'>Confused what to do now? Read the <a href='https://github.com/NlGBOB/bloxd-piano' target='_blank' class='text-blue-600 hover:underline'>documentation</a>.</p>", unsafe_allow_html=True)
    
    if results.get("preview"):
        st.markdown("<p class='text-center text-gray-500 mt-6'>This is approximately how your MIDI will sound in-game:</p>", unsafe_allow_html=True)
        st.audio(results["preview"], format='audio/wav')
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='mt-10 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6'>", unsafe_allow_html=True)
    file_info = [("1. Sounds", "sounds"), ("2. Delays", "delays"), ("3. Notes", "notes"), ("4. Volumes", "volumes")]

    for title, key in file_info:
        st.markdown("<div class='bg-white rounded-xl shadow-sm border border-gray-200 p-4 flex flex-col'>", unsafe_allow_html=True)
        st.markdown(f"<h4 class='text-lg font-semibold text-gray-700 text-center mb-2'>{title}</h4>", unsafe_allow_html=True)
        content = results.get(key, b"").decode('utf-8', errors='ignore')
        st.code(content, language=None)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

inject_tailwind()
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
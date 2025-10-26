import streamlit as st
import os
import json
import shutil
import tempfile
from io import StringIO
import sys
import base64
from processor import run_processing

st.set_page_config(page_title="MIDI to Bloxd Converter", layout="centered", initial_sidebar_state="auto")

ACCENT_RED = "#E03A3C"
ACCENT_RED_HOVER = "#C53030"
ACCENT_RED_LIGHT = "#FEF2F2"

def inject_styles():
    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
            
            :root {{
                --ilovepdf-red: {ACCENT_RED};
                --ilovepdf-red-hover: {ACCENT_RED_HOVER};
                --ilovepdf-red-light: {ACCENT_RED_LIGHT};
            }}

            html, body, [data-testid="stAppViewContainer"] {{ 
                background-color: #F9FAFB; 
                font-family: 'Roboto', sans-serif;
            }}
            #MainMenu, footer {{ visibility: hidden; }}
            header[data-testid="stHeader"] {{ display: none; }}

            [data-testid="stSidebar"] {{
                background-color: #FFFFFF;
                border-right: 1px solid #E5E7EB;
                box-shadow: 2px 0 5px rgba(0,0,0,0.02);
            }}

            [data-testid="stFileUploaderDropzone"] {{
                border: 3px dashed #E5E7EB !important;
                background-color: #FFFFFF;
                padding: 4rem 2rem;
                border-radius: 1rem;
                transition: all 0.3s;
                text-align: center;
                margin-top: 2rem;
            }}
            [data-testid="stFileUploaderDropzone"]:hover {{
                border-color: var(--ilovepdf-red);
                background-color: var(--ilovepdf-red-light);
            }}
            .stFileUploader > div > div > button {{
                background-color: var(--ilovepdf-red) !important; 
                color: white !important; 
                border: none !important;
                border-radius: 0.5rem; 
                font-weight: 500;
                padding: 0.75rem 1.5rem;
                box-shadow: none;
                transition: background-color 0.2s;
            }}
            .stFileUploader > div > div > button:hover {{ 
                background-color: var(--ilovepdf-red-hover) !important; 
            }}
            .stFileUploader > div > div > small {{
                color: #6B7280;
                font-size: 0.9rem;
                display: block;
                margin-top: 10px;
            }}
            [data-testid="stFileUploaderDropzone"] > div:first-child {{ display: none; }}


            .stButton button {{
                background-color: var(--ilovepdf-red) !important;
                color: white !important;
                border: 1px solid var(--ilovepdf-red) !important;
                border-radius: 0.5rem;
                font-weight: 600;
                transition: all 0.2s;
                box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            }}
            .stButton button:hover {{
                background-color: var(--ilovepdf-red-hover) !important;
                border-color: var(--ilovepdf-red-hover) !important;
                box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
            }}

            .stButton button[kind="secondary"] {{
                background-color: white !important;
                color: var(--ilovepdf-red) !important;
                border: 1px solid var(--ilovepdf-red) !important;
                box-shadow: none;
            }}
            .stButton button[kind="secondary"]:hover {{
                background-color: var(--ilovepdf-red-light) !important;
            }}


            .clickable-code-block {{
                position: relative; cursor: pointer;
                background-color: #FFFFFF; /* White card look */
                color: #1F2937;
                border-radius: 0.5rem; 
                border: 1px solid #E5E7EB;
                padding: 1rem; 
                font-family: monospace;
                white-space: pre-wrap; 
                word-break: break-all;
                transition: all 0.2s ease-in-out;
                min-height: 4.5rem; /* Ensure blocks are visible even if content is tiny */
                overflow-x: auto;
            }}
            .clickable-code-block:hover {{
                border-color: var(--ilovepdf-red);
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            }}
            .copy-feedback {{
                position: absolute; top: 0.75rem; right: 0.75rem;
                background-color: #10B981; color: white;
                padding: 0.25rem 0.75rem; border-radius: 9999px;
                font-size: 0.75rem; /* Smaller font for feedback */
                font-weight: 500;
                opacity: 0; transition: opacity 0.3s ease;
                pointer-events: none;
            }}
        </style>
    """, unsafe_allow_html=True)

def get_clickable_code_block(title, content_str, block_id):
    """Generates a styled, copyable code block based on the iLovePDF card design."""
    
    # Limit content displayed to prevent massive scrolling, but copy the full string
    display_content = content_str[:400] + ('...' if len(content_str) > 400 else content_str)
    
    # Use base64 encoding to safely pass the potentially long string to JavaScript
    b64_content = base64.b64encode(content_str.encode('utf-8')).decode()
    
    onclick_js = f"""
        (function() {{
            const textToCopy = atob('{b64_content}');
            navigator.clipboard.writeText(textToCopy).then(() => {{
                const feedbackEl = document.getElementById('feedback-{block_id}');
                if (feedbackEl) {{
                    feedbackEl.style.opacity = '1';
                    setTimeout(() => {{ feedbackEl.style.opacity = '0'; }}, 2000);
                }}
            }});
        }})();
    """
    
    html = f"""
    <div class="mt-4">
        <h4 style="font-size: 1.125rem; font-weight: 600; color: #1F2937; margin-bottom: 0.5rem;">{title}</h4>
        <div onclick="{onclick_js}" class="clickable-code-block">
            {display_content}
            <div id="feedback-{block_id}" class="copy-feedback">Copied!</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def initialize_state():
    if 'step' not in st.session_state: st.session_state.step = 'upload'
    if 'results' not in st.session_state: st.session_state.results = None
    if 'midi_data' not in st.session_state: st.session_state.midi_data = None
    if 'midi_filename' not in st.session_state: st.session_state.midi_filename = None
    if 'config_json' not in st.session_state: 
        default_config = {
            "palette": ["harp_pling", "game_start_countdown_01", "game_start_countdown_02", "game_start_countdown_03", "game_start_countdown_final"],
            "layering": {"comment": "Max sounds per note. 1 = no layering.", "max_layers": 2}
        }
        st.session_state.config_json = json.dumps(default_config, indent=2)

def process_and_store_results(midi_data, midi_filename, config_data):
    """Handles the core processing and stores results in session state."""
    st.info("Conversion in progress. This may take a moment, especially for audio rendering.")
    with st.spinner("Processing MIDI and generating audio preview..."):
        with tempfile.TemporaryDirectory() as temp_dir:
            midi_path = os.path.join(temp_dir, midi_filename)
            with open(midi_path, "wb") as f: f.write(midi_data)

            old_stdout = sys.stdout
            captured_output = StringIO()
            sys.stdout = captured_output

            output_dir = run_processing(
                midi_file_path=midi_path, config_data=config_data,
                render_preview_flag=True, sound_folder_path="sounds"
            )
            
            sys.stdout = old_stdout
            log_output = captured_output.getvalue()

            results = {"log": log_output}
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
                        if key == "preview":
                            with open(fpath, "rb") as f: results[key] = f.read()
                        else:
                            with open(fpath, "r", encoding='utf-8') as f: results[key] = f.read()

            st.session_state.results = results
            st.session_state.step = 'results'
            st.rerun()
            

def upload_view():
    """Renders the centered, large input view (iLovePDF Step 1)."""
    st.markdown(f"<div style='text-align: center; max-width: 600px; margin: 40px auto;'>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='font-size: 3rem; font-weight: 700; color: #1F2937;'>MIDI to Bloxd Music Converter</h1>", unsafe_allow_html=True)
    st.markdown("<p style='margin-top: 1rem; font-size: 1.1rem; color: #4B5563;'>Convert MIDI files into the compressed strings required for the Bloxd Piano minigame.</p>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Select MIDI File", 
        type=['mid', 'midi'], 
        label_visibility="collapsed"
    )

    st.markdown(f"""
        <div style='text-align: center; margin-top: -2.5rem; color: #6B728D;'>
            <p>Drag and drop file here</p>
            <p style='font-size: 0.8rem; margin-top: 0.2rem;'>.mid or .midi files only</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if uploaded_file:
        st.session_state.midi_data = uploaded_file.getvalue()
        st.session_state.midi_filename = uploaded_file.name
        st.session_state.step = 'processing_redirect' # Use a redirect step to handle spinner
        st.rerun()

def processing_view():
    """Handles the redirection and calls the processing function."""
    config_str = st.session_state.get("config_json", '{}')
    try: 
        config_data = json.loads(config_str)
    except json.JSONDecodeError: 
        st.error("Invalid JSON configuration detected. Using default config.")
        config_data = {}
    
    process_and_store_results(st.session_state.midi_data, st.session_state.midi_filename, config_data)

def results_view():
    """Renders the results page with sidebar controls (iLovePDF Step 2)."""
    results = st.session_state.results
    
    with st.sidebar:
        st.header("Conversion Options")
        st.caption(f"File: **{st.session_state.midi_filename}**")
        st.divider()

        st.markdown("<p style='font-weight: 600; margin-bottom: 0.5rem;'>Layering & Palette Config (JSON)</p>", unsafe_allow_html=True)
        
        config_text = st.text_area(
            "Config JSON", 
            value=st.session_state.config_json, 
            height=200, 
            key="config_json_input", 
            label_visibility="collapsed"
        )
        
        st.markdown("<div style='margin-top: 20px; text-align: center;'>", unsafe_allow_html=True)
        if st.button("Rerun Conversion", use_container_width=True):
            try:
                st.session_state.config_json = config_text
                json.loads(st.session_state.config_json)
                st.session_state.step = 'processing_redirect'
                st.rerun()
            except json.JSONDecodeError: 
                st.error("Invalid JSON format in config.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.divider()
        if st.button("Convert New MIDI", use_container_width=True, type="secondary"):
            for key in list(st.session_state.keys()): 
                if key not in ['config_json']: # Keep config
                    del st.session_state[key]
            st.session_state.step = 'upload'
            st.rerun()


    st.markdown("<div style='max-width: 800px; margin: 0 auto; padding-top: 1rem;'>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='font-size: 2.5rem; font-weight: 700; color: #1F2937;'>Conversion Complete!</h3>", unsafe_allow_html=True)
    st.markdown("<p style='margin-top: 0.5rem; color: #4B5563;'>Click on any box below to copy the code string directly.</p>", unsafe_allow_html=True)
    
    if results.get("preview"):
        st.markdown("<div style='margin-top: 2rem;'>", unsafe_allow_html=True)
        st.markdown("<h4 style='font-size: 1.25rem; font-weight: 600; color: #1F2937; margin-bottom: 0.5rem;'>Preview Audio</h4>", unsafe_allow_html=True)
        st.audio(results["preview"], format='audio/wav')
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("Could not generate audio preview. Check the log for sound loading errors.")
        
    file_info = [
        ("1. Sounds Data (S index)", "sounds"), 
        ("2. Delays Data (D index)", "delays"), 
        ("3. Notes Data (P index)", "notes"), 
        ("4. Volumes Data (V index)", "volumes")
    ]
    
    col1, col2 = st.columns(2)
    
    for i, (title, key) in enumerate(file_info):
        content = results.get(key, "Error: Data not found.")
        target_col = col1 if i % 2 == 0 else col2
        with target_col:
            get_clickable_code_block(title, content, key)
            
    with st.expander("Show Conversion Log & Debug Output"):
        st.code(results.get("log", "No log output available."))
        
    st.markdown("</div>", unsafe_allow_html=True)



if __name__ == "__main__":
    inject_styles()
    initialize_state()

    if st.session_state.step == 'upload':
        upload_view()
    elif st.session_state.step == 'processing_redirect':
        processing_view()
    elif st.session_state.step == 'results':
        results_view()
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
AUTHOR_INFO = "<div class='text-right text-sm text-gray-500 pr-4 pt-2'>Made by chmod</div>"
DOCS_LINK = "https://github.com/NlGBOB/bloxd-piano"


def inject_styles():
    st.markdown("""
        <script src="https://cdn.tailwindcss.com"></script>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <style>
            /* Define Streamlit Overrides and Custom Variables */
            :root {{
                --accent-red: {ACCENT_RED};
            }}

            html, body, [data-testid="stAppViewContainer"] {{ 
                background-color: #F9FAFB; 
                font-family: ui-sans-serif, system-ui, sans-serif;
            }}
            #MainMenu, footer {{ visibility: hidden; }}
            header[data-testid="stHeader"] {{ display: none; }}
            
            /* Apply Tailwind-like classes globally */
            h1, h2, h3, h4 {{ font-family: ui-sans-serif, system-ui, sans-serif; }}
            
            
            [data-testid="stFileUploaderDropzone"] {{
                border: 2px dashed #D1D5DB !important; 
                background-color: #FFFFFF;
                border-radius: 0.5rem;
                margin-top: 1rem;
                padding: 0 !important; 
                min-height: 140px; 
                position: relative;
                transition: all 0.3s;
            }}
            [data-testid="stFileUploaderDropzone"]:hover {{
                border-color: #A0AEC0; 
                background-color: #FAFAFA;
            }}
            
            [data-testid="stFileUploaderDropzone"] > div:first-child {{ 
                display: none !important; 
            }}
            
            .stFileUploader > div > div {{
                position: absolute; 
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                display: flex;
                align-items: center;
                justify-content: flex-end; /* Only button alignment matters now */
                z-index: 10;
                padding: 0;
            }}

            .stFileUploader > div > div > button {{
                background-color: rgb(31 41 55) !important; /* Tailwind gray-800 */
                color: white !important; 
                border: none !important;
                border-radius: 0.375rem; 
                font-weight: 500;
                padding: 0.75rem 1.5rem;
                transition: background-color 0.2s;
                height: 44px;
                z-index: 20; 
                position: absolute;
                right: 20px;
                bottom: 20px;
            }}
            .stFileUploader > div > div > button:hover {{ 
                background-color: rgb(55 65 81) !important; /* Tailwind gray-700 */
            }}
            .stFileUploader > div > div > small {{ display: none; }}

            .clickable-code-block-container {{
                position: relative; 
                cursor: pointer;
                overflow: hidden; 
            }}
            .copy-feedback {{
                position: absolute; top: 0.75rem; right: 0.75rem;
                background-color: #10B981; color: white;
                padding: 0.25rem 0.75rem; border-radius: 9999px;
                font-size: 0.75rem; 
                font-weight: 500;
                opacity: 0; transition: opacity 0.3s ease;
                pointer-events: none;
            }}
            .stButton button {{
                background-color: var(--accent-red) !important;
                color: white !important;
                border: 1px solid var(--accent-red) !important;
            }}
            .stButton button:hover {{
                background-color: {ACCENT_RED_HOVER} !important; 
                border-color: {ACCENT_RED_HOVER} !important;
            }}

        </style>
    """, unsafe_allow_html=True)

def get_clickable_code_block(title, content_str, block_id):
    
    full_content = content_str.strip()
    
    b64_content = base64.b64encode(full_content.encode('utf-8')).decode()
    
    onclick_js = f"""
        const textToCopy = atob('{b64_content}');
        navigator.clipboard.writeText(textToCopy).then(() => {{
            const feedbackEl = document.getElementById('feedback-{block_id}');
            if (feedbackEl) {{
                feedbackEl.style.opacity = '1';
                setTimeout(() => {{ feedbackEl.style.opacity = '0'; }}, 2000);
            }}
        }}).catch(err => console.error('Failed to copy text: ', err));
    """
    
    html = f"""
    <div class="mt-4">
        <h4 class="text-lg font-semibold text-gray-800 mb-2">{title}</h4>
        
        <div onclick="{onclick_js}" id="block-{block_id}" 
             class="clickable-code-block-container 
             bg-white border border-gray-200 rounded-lg p-3 shadow-sm transition hover:shadow-lg">
            
            <pre class="
                font-mono text-sm text-gray-800 
                whitespace-nowrap overflow-hidden text-ellipsis 
                m-0 p-0 block
            ">
                {full_content}
            </pre>
            
            <div id="feedback-{block_id}" class="copy-feedback">Copied!</div>
            
            <div class="absolute top-1/2 right-4 transform -translate-y-1/2 
                        text-xs font-semibold text-gray-500 bg-white px-2 py-0.5 rounded shadow-lg border border-gray-100">
                Click to Copy
            </div>
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
                        with open(fpath, "rb") as f: 
                            results[key] = f.read()
                    else:
                        with open(fpath, "r", encoding='utf-8') as f: 
                            results[key] = f.read()

        st.session_state.results = results
        st.session_state.step = 'results'
        st.rerun()
            

def upload_view():
    
    st.markdown(AUTHOR_INFO, unsafe_allow_html=True)
    st.markdown(f"<div class='max-w-xl mx-auto mt-10'>", unsafe_allow_html=True)
    
    st.markdown(f"<h1 class='text-4xl font-extrabold text-gray-900 mb-2'>MIDI to Bloxd Music Converter</h1>", unsafe_allow_html=True)
    
    st.markdown("<p class='mt-2 text-lg text-gray-500'>Convert MIDI files into the compressed strings required for Bloxd.</p>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class="relative mt-8">
            <div class="absolute inset-0 flex flex-col items-center justify-center p-4 pointer-events-none z-10">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-10 h-10 text-gray-400">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                </svg>
                <p class="mt-2 text-base font-medium text-gray-700">Drag and drop file here</p>
                <p class="text-sm text-gray-500">.mid or .midi files only (Max 200MB)</p>
            </div>
""", unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Select MIDI File", 
        type=['mid', 'midi'], 
        label_visibility="collapsed"
    )

    st.markdown("</div>", unsafe_allow_html=True) 

    if uploaded_file:
        st.session_state.midi_data = uploaded_file.getvalue()
        st.session_state.midi_filename = uploaded_file.name
        st.session_state.step = 'processing_redirect' 
        st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)


def processing_view():
    
    st.markdown(f"<div class='text-center max-w-xl mx-auto mt-32'>", unsafe_allow_html=True)
    st.markdown(f"<h3 class='text-3xl font-bold text-gray-800'>Processing file: {st.session_state.midi_filename}</h3>", unsafe_allow_html=True)
    
    with st.spinner("Analyzing MIDI, mapping sounds, and generating audio preview. Please wait..."):
        config_str = st.session_state.get("config_json", '{}')
        try: 
            config_data = json.loads(config_str)
        except json.JSONDecodeError: 
            st.error("Invalid JSON configuration detected in session state. Cannot proceed.")
            st.session_state.step = 'results' 
            return 
        
        process_and_store_results(st.session_state.midi_data, st.session_state.midi_filename, config_data)
        
    st.markdown("</div>", unsafe_allow_html=True)


def results_view():
    results = st.session_state.results
    
    with st.sidebar:
        st.header("Conversion Options")
        st.caption(f"File: **{st.session_state.midi_filename}**")
        st.divider()

        st.markdown("<p class='font-semibold mb-2'>Layering & Palette Config (JSON)</p>", unsafe_allow_html=True)
        
        config_text = st.text_area(
            "Config JSON", 
            value=st.session_state.config_json, 
            height=200, 
            key="config_json_input_sidebar",
            label_visibility="collapsed"
        )
        
        st.markdown("<div class='mt-5'>", unsafe_allow_html=True)
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
            keys_to_keep = ['config_json', 'config_json_input_sidebar'] 
            for key in list(st.session_state.keys()): 
                if key not in keys_to_keep:
                    del st.session_state[key]
            st.session_state.step = 'upload'
            st.rerun()


    st.markdown(AUTHOR_INFO, unsafe_allow_html=True)
    st.markdown("<div class='max-w-3xl mx-auto pt-4'>", unsafe_allow_html=True)
    st.markdown(f"<h3 class='text-4xl font-extrabold text-gray-900'>Conversion Complete!</h3>", unsafe_allow_html=True)
    
    st.markdown(f"<p class='mt-2 text-gray-600'>Read the <a href='{DOCS_LINK}' target='_blank' class='text-red-600 font-semibold no-underline hover:underline'>documentation</a> if you are confused. Click on any box below to copy the **full** code string.</p>", unsafe_allow_html=True)
    
    if results.get("preview"):
        st.markdown("<div class='mt-6'>", unsafe_allow_html=True)
        st.markdown("<h4 class='text-xl font-semibold text-gray-800 mb-2'>Preview Audio</h4>", unsafe_allow_html=True)
        st.markdown("<p class='text-sm text-gray-500'>This simulation uses sampled sounds to estimate how the track will sound in-game.</p>", unsafe_allow_html=True)
        st.audio(results["preview"], format='audio/wav')
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("Could not generate audio preview. Check the log below for sound loading errors.")
        
    file_info = [
        ("1. Sounds Data", "sounds"), 
        ("2. Delays Data", "delays"), 
        ("3. Notes Data", "notes"), 
        ("4. Volumes Data", "volumes")
    ]
    
    for title, key in file_info:
        content = results.get(key, "Error: Data not found.")
        get_clickable_code_block(title, content, key)
            
    with st.expander("Show Conversion Log & Debug Output", expanded=False):
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
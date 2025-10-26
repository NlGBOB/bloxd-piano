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
AUTHOR_INFO = "<div class='text-end text-muted small pe-3 pt-2'>Made by chmod</div>"
DOCS_LINK = "https://github.com/NlGBOB/bloxd-piano"


def inject_styles():
    st.markdown("""
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-sRIl4kxILFvY47J16cr9ZwB07vP4J8+LH7qKQnuqkuIAvNWLzeN8tE5YBujZqJLB" crossorigin="anonymous">
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js" integrity="sha384-FKyoEForCGlyvwx9Hj09JcYn3nv7wiPVlz7YYwJrWVcXK/BmnVDxM+D2scQbITxI" crossorigin="anonymous"></script>
    """, unsafe_allow_html=True)

    
    st.markdown(f"""
        <style>
            :root {{
                --bs-red-custom: {ACCENT_RED};
                --bs-red-hover: {ACCENT_RED_HOVER};
            }}

            html, body, [data-testid="stAppViewContainer"] {{ 
                background-color: #F8F9FA; 
                font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
            }}
            #MainMenu, footer {{ visibility: hidden; }}
            header[data-testid="stHeader"] {{ display: none; }}
            
            
            [data-testid="stFileUploaderDropzone"] {{
                /* Apply dashed border and clean up padding */
                border: 2px dashed #D1D5DB !important; 
                background-color: #FFFFFF;
                border-radius: 0.5rem;
                margin-top: 1rem;
                padding: 0 !important; 
                min-height: 140px; 
                position: relative;
                transition: all 0.3s;
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
                justify-content: flex-end; 
                z-index: 10;
                padding: 0;
            }}

            .stFileUploader > div > div > button {{
                background-color: var(--bs-dark) !important; 
                color: white !important; 
                border: none !important;
                border-radius: 0.375rem; 
                font-weight: 500;
                padding: 0.75rem 1.5rem;
                height: 44px;
                z-index: 20; 
                position: absolute;
                right: 20px;
                bottom: 20px;
                /* Ensure button text is centered */
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .stFileUploader > div > div > button > div {{
                color: white !important; /* Ensure text remains white */
            }}
            .stFileUploader > div > div > button:hover {{ 
                background-color: #495057 !important; /* dark hover */
            }}
            .stFileUploader > div > div > small {{ display: none; }}


            .clickable-code-block-container {{
                position: relative; 
                cursor: pointer;
                overflow: hidden; 
                transition: box-shadow 0.2s;
            }}
            .clickable-code-block-container:hover {{
                box-shadow: 0 .5rem 1rem rgba(0,0,0,.15)!important;
            }}

            .copy-feedback {{
                position: absolute; top: 0.75rem; right: 0.75rem;
                background-color: #10B981; color: white;
                padding: 0.25rem 0.75rem; border-radius: 50rem;
                font-size: 0.75rem; 
                font-weight: 500;
                opacity: 0; transition: opacity 0.3s ease;
                pointer-events: none;
                z-index: 30;
            }}
            
            /* Ensure single line display for code blocks */
            .code-single-line {{
                white-space: nowrap; 
                overflow-x: hidden;
                text-overflow: ellipsis; 
            }}
            
            /* Primary button styling */
            .stButton button {{
                background-color: var(--bs-red-custom) !important;
                color: white !important;
                border: 1px solid var(--bs-red-custom) !important;
            }}
            .stButton button:hover {{
                background-color: var(--bs-red-hover) !important; 
                border-color: var(--bs-red-hover) !important;
            }}

        </style>
    """, unsafe_allow_html=True)

def get_clickable_code_block(title, content_str, block_id):
    """
    Generates a Bootstrap card, single-line display, with full string copy functionality.
    
    NOTE: The previous error where the JS code was displayed was likely due to how
    Streamlit handled the complex HTML string injection. Simplifying the JS display
    and ensuring the structure is rendered correctly is key.
    """
    
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
        <h4 class="h5 fw-semibold text-dark mb-2">{title}</h4>
        
        <div onclick="{onclick_js}" id="block-{block_id}" 
             class="clickable-code-block-container card shadow-sm">
            
            <div class="card-body p-3 d-flex align-items-center bg-light">
                <pre class="
                    font-monospace text-sm text-dark 
                    code-single-line flex-grow-1 m-0 p-0 
                ">
                    {full_content}
                </pre>
                
                <span class="badge bg-dark ms-3 shadow-sm" style="font-size: 0.7rem;">Click to Copy</span>
                
            </div>
            
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
    """Renders the Bootstrap-styled upload view with fixed component structure."""
    
    st.markdown(AUTHOR_INFO, unsafe_allow_html=True)
    st.markdown(f"<div class='container' style='max-width: 600px; margin-top: 2rem;'>", unsafe_allow_html=True)
    
    st.markdown(f"<h1 class='display-6 fw-bold text-dark'>MIDI to Bloxd Music Converter</h1>", unsafe_allow_html=True)
    
    st.markdown("<p class='lead text-muted mb-3'>Convert MIDI files into the compressed strings required for Bloxd.</p>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class="mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="text-primary mb-1" style="width: 3rem; height: 3rem;">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 19.5v-15m0 0l-6.75 6.75M12 4.5l6.75 6.75" />
            </svg>
            <p class="mb-0 fw-medium text-dark">Drag and drop file here</p>
            <p class="small text-muted mb-0">.mid or .midi files only (Max 200MB)</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="position-relative">
            <!-- This visual placeholder sits inside the dashed border -->
            <div class="position-absolute w-100 h-100 d-flex flex-column justify-content-center align-items-center p-4 pointer-events-none z-10" style="color: #E5E7EB;">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width: 32px; height: 32px;" class="mb-1">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                </svg>
                <p class="mb-0 fw-medium">Drag and drop file here</p>
                <p class="small mb-0">Limit 200MB per file - MID, MIDI</p>
            </div>

            <!-- The functional Streamlit uploader is placed here, styled via CSS to only show the button -->
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
    """Handles the redirection and calls the processing function with a spinner."""
    
    st.markdown(f"<div class='container text-center' style='max-width: 600px; margin-top: 8rem;'>", unsafe_allow_html=True)
    st.markdown(f"<h3 class='h2 fw-bold text-dark'>Processing file: {st.session_state.midi_filename}</h3>", unsafe_allow_html=True)
    
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
    """Renders the results page with sidebar controls."""
    results = st.session_state.results
    
    with st.sidebar:
        st.header("Conversion Options")
        st.caption(f"File: **{st.session_state.midi_filename}**")
        st.divider()

        st.markdown("<p class='fw-semibold mb-2'>Layering & Palette Config (JSON)</p>", unsafe_allow_html=True)
        
        config_text = st.text_area(
            "Config JSON", 
            value=st.session_state.config_json, 
            height=200, 
            key="config_json_input_sidebar",
            label_visibility="collapsed"
        )
        
        st.markdown("<div class='mt-3'>", unsafe_allow_html=True)
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
    st.markdown("<div class='container' style='max-width: 800px; margin-top: 1rem;'>", unsafe_allow_html=True)
    st.markdown(f"<h3 class='display-6 fw-bold text-dark'>Conversion Complete!</h3>", unsafe_allow_html=True)
    
    st.markdown(f"<p class='text-secondary'>Click on any box below to copy the **full** code string. Read the <a href='{DOCS_LINK}' target='_blank' style='color: var(--bs-red-custom); font-weight: 500;'>documentation</a> if you are confused.</p>", unsafe_allow_html=True)
    
    if results.get("preview"):
        st.markdown("<div class='mt-4'>", unsafe_allow_html=True)
        st.markdown("<h4 class='h5 fw-semibold text-dark mb-2'>Preview Audio</h4>", unsafe_allow_html=True)
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
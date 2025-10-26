import streamlit as st
import json
import os
import tempfile
import base64
from processor import run_processing, strip_extension, PIANO_SOUND_DATA

st.set_page_config(
    page_title="MIDI to Bloxd Music Converter",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DEFAULT_CONFIG = {
    "palette": [strip_extension(s['filename']) for s in PIANO_SOUND_DATA],
    "layering": {
        "comment": "Max sounds per note. 1 = no layering. >1 = harp_pling + layers. max layer = 5",
        "max_layers": 2
    }
}

if 'config_text' not in st.session_state:
    st.session_state.config_text = json.dumps(DEFAULT_CONFIG, indent=4)
if 'output_data' not in st.session_state:
    st.session_state.output_data = None
if 'error_message' not in st.session_state:
    st.session_state.error_message = None

st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz" crossorigin="anonymous"></script>
    <style>
        /* Minimalist Light Theme Adjustments */
        .stApp {
            background-color: #f8f9fa; /* Light grey background */
        }
        .stButton>button {
            width: 100%;
            border-radius: 0.375rem; /* Match Bootstrap's border-radius */
        }
        .card {
            background-color: #ffffff; /* White cards */
            border: 1px solid #dee2e6; /* Softer border */
        }
        .card-header {
            background-color: #f8f9fa;
            font-weight: 500;
        }
        textarea.form-control {
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.9rem;
            color: #495057;
            background-color: #fff !important; /* Override Streamlit's default textarea background */
        }
        footer {
            visibility: hidden;
        }
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #f8f9fa;
            color: #6c757d;
            text-align: right;
            padding: 10px;
            border-top: 1px solid #dee2e6;
        }
    </style>
    """, unsafe_allow_html=True)

st.components.v1.html("""
    <script>
    function copyToClipboard(elementId, buttonId) {
        var copyText = document.getElementById(elementId);
        copyText.select();
        copyText.setSelectionRange(0, 99999); /* For mobile devices */
        document.execCommand("copy");
        
        // Provide user feedback
        var button = document.getElementById(buttonId);
        var originalText = button.innerHTML;
        button.innerHTML = "Copied!";
        setTimeout(function(){
            button.innerHTML = originalText;
        }, 1500);
    }
    </script>
""", height=0)


def create_copyable_card(title, content, content_id):
    button_id = f"button_{content_id}"
    html = f"""
    <div class="card h-100">
        <div class="card-header">
            {title}
        </div>
        <div class="card-body d-flex flex-column">
            <textarea id="{content_id}" class="form-control flex-grow-1" readonly>{content}</textarea>
            <button id="{button_id}" class="btn btn-outline-secondary mt-2" onclick="copyToClipboard('{content_id}', '{button_id}')">
                Copy
            </button>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


st.markdown('<div class="container-fluid mt-4">', unsafe_allow_html=True)

st.markdown('<h1 class="display-4 text-center mb-4">MIDI to Bloxd Music Converter</h1>', unsafe_allow_html=True)
st.markdown('<p class="text-center text-muted">Convert your MIDI files into a format compatible with Bloxd.io\'s music system.</p>', unsafe_allow_html=True)

st.markdown('<div class="card shadow-sm mb-4"><div class="card-body">', unsafe_allow_html=True)
st.markdown('<h5 class="card-title">1. Inputs & Configuration</h5>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Upload Files")
    uploaded_midi = st.file_uploader("Upload your MIDI file (.mid, .midi)", type=["mid", "midi"])
    
    sound_folder_path = st.text_input(
        "Path to your 'sounds' folder", 
        value="./sounds",
        help="This folder must contain the required .wav files (e.g., harp_pling.wav). Place it in the same directory as this app for it to work."
    )

with col2:
    st.subheader("Settings")
    render_preview = st.checkbox("Generate Audio Preview", value=True, help="Creates a .wav file to simulate how the song will sound in-game.")
    
    st.markdown("<br>", unsafe_allow_html=True) # Spacer
    process_button = st.button("Convert MIDI", type="primary", use_container_width=True)

st.subheader("JSON Configuration")
st.session_state.config_text = st.text_area(
    "Edit the sound palette and layering options below. Then, press 'Convert MIDI' again.", 
    value=st.session_state.config_text, 
    height=250
)

st.markdown('</div></div>', unsafe_allow_html=True) # Close main card

if process_button:
    st.session_state.output_data = None
    st.session_state.error_message = None

    if uploaded_midi is None:
        st.session_state.error_message = "Please upload a MIDI file."
    elif not os.path.isdir(sound_folder_path):
        st.session_state.error_message = f"Sound folder not found at '{sound_folder_path}'. Please check the path."
    else:
        try:
            config_data = json.loads(st.session_state.config_text)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mid") as tmp_midi:
                tmp_midi.write(uploaded_midi.getvalue())
                midi_path = tmp_midi.name

            with st.spinner('Processing your MIDI... This may take a moment.'):
                output_dir = run_processing(midi_path, config_data, render_preview, sound_folder_path)
            
            os.unlink(midi_path) # Clean up temporary file

            if output_dir:
                st.session_state.output_data = {}
                base_name = os.path.basename(output_dir)
                file_map = {
                    "sounds": ("Sounds Data", f"1_{base_name}_sounds.txt"),
                    "delays": ("Delays Data", f"2_{base_name}_delays.txt"),
                    "notes": ("Notes Data", f"3_{base_name}_notes.txt"),
                    "volumes": ("Volumes Data", f"4_{base_name}_volumes.txt"),
                    "preview": ("Audio Preview", f"8_{base_name}_preview.wav")
                }
                for key, (title, filename) in file_map.items():
                    path = os.path.join(output_dir, filename)
                    if os.path.exists(path):
                        if key == "preview":
                            st.session_state.output_data['preview_path'] = path
                        else:
                            with open(path, 'r', encoding='utf-8') as f:
                                st.session_state.output_data[key] = f.read()
            else:
                st.session_state.error_message = "Processing completed, but no valid notes were mapped. No output files generated."

        except json.JSONDecodeError:
            st.session_state.error_message = "Invalid JSON in configuration. Please check for syntax errors (e.g., missing commas)."
        except Exception as e:
            st.session_state.error_message = f"An unexpected error occurred: {e}"

if st.session_state.error_message:
    st.error(st.session_state.error_message, icon="🚨")

if st.session_state.output_data:
    st.success("Conversion successful! Your song data is ready below.", icon="✅")
    
    st.markdown('<div class="card shadow-sm mb-4"><div class="card-body">', unsafe_allow_html=True)
    st.markdown('<h5 class="card-title">2. Output Data</h5>', unsafe_allow_html=True)
    st.markdown('<p class="card-text">Copy the content from each box and paste it into the corresponding music block in Bloxd.</p>', unsafe_allow_html=True)

    # Display copyable cards in two columns
    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        create_copyable_card("Sounds Data", st.session_state.output_data.get("sounds", ""), "sounds_content")
    with row1_col2:
        create_copyable_card("Delays Data", st.session_state.output_data.get("delays", ""), "delays_content")
    
    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        create_copyable_card("Notes Data", st.session_state.output_data.get("notes", ""), "notes_content")
    with row2_col2:
        create_copyable_card("Volumes Data", st.session_state.output_data.get("volumes", ""), "volumes_content")
    
    st.markdown('</div></div>', unsafe_allow_html=True) # Close results card

    if 'preview_path' in st.session_state.output_data:
        st.markdown('<div class="card shadow-sm"><div class="card-body">', unsafe_allow_html=True)
        st.markdown('<h5 class="card-title">3. Audio Preview</h5>', unsafe_allow_html=True)
        st.info("This is close to how your song will sound in game.", icon="🎵")
        
        try:
            with open(st.session_state.output_data['preview_path'], 'rb') as audio_file:
                st.audio(audio_file.read(), format='audio/wav')
        except FileNotFoundError:
             st.warning("Could not find the audio preview file. It may have been moved or deleted.")

        st.markdown('</div></div>', unsafe_allow_html=True)


st.markdown("""
    <div class="footer">
        <p class="text-secondary" style="margin: 0; padding-right: 15px;">Made by chmod</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True) # Close container
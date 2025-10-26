import streamlit as st
import json
import os
import tempfile
from processor import run_processing, strip_extension, PIANO_SOUND_DATA

# --- Page Configuration ---
st.set_page_config(
    page_title="MIDI to Bloxd Music Converter",
    layout="centered",  # Use a centered layout
    initial_sidebar_state="collapsed"
)

# --- Default Configuration ---
DEFAULT_CONFIG = {
    "palette": [strip_extension(s['filename']) for s in PIANO_SOUND_DATA],
    "layering": {
        "comment": "Max sounds per note. 1 = no layering. >1 = harp_pling + layers. max layer = 5",
        "max_layers": 2
    }
}

# --- State Management ---
if 'config_text' not in st.session_state:
    st.session_state.config_text = json.dumps(DEFAULT_CONFIG, indent=4)
if 'output_data' not in st.session_state:
    st.session_state.output_data = None
if 'error_message' not in st.session_state:
    st.session_state.error_message = None

# --- Custom CSS for a cleaner look ---
st.markdown("""
    <style>
        /* Center the title and subtitle */
        .main-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        /* Style for the cards/containers */
        .results-container, .main-container {
            padding: 1.5rem;
            border: 1px solid #e6e6e6;
            border-radius: 0.5rem;
            background-color: #ffffff;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            margin-bottom: 2rem;
        }
        /* Style for dark mode */
        body[data-theme="dark"] .results-container,
        body[data-theme="dark"] .main-container {
            background-color: #1E1E1E;
            border-color: #333;
        }
        /* Ensure text areas are a reasonable height */
        .stTextArea textarea {
            height: 150px;
        }
        /* Footer styling */
        .footer {
            text-align: right;
            color: grey;
            font-size: 0.9em;
            padding-top: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

# --- Main Application Layout ---

# Header
st.markdown('<div class="main-header"><h1>MIDI to Bloxd Music Converter</h1><p>Convert your MIDI files into a format compatible with Bloxd.io\'s music system.</p></div>', unsafe_allow_html=True)

# Main container for inputs
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# --- Inputs ---
st.subheader("1. Upload your MIDI File")
uploaded_midi = st.file_uploader(
    "Drag and drop or browse to upload your MIDI file.",
    type=["mid", "midi"],
    label_visibility="collapsed"
)

st.subheader("2. Configure Settings")
render_preview = st.checkbox("Generate Audio Preview", value=True, help="Creates a .wav file to simulate how the song will sound in-game. Uncheck for faster processing.")

with st.expander("Advanced Configuration (JSON)"):
    st.session_state.config_text = st.text_area(
        "Edit the sound palette and layering options below. Then, press 'Convert MIDI' again.",
        value=st.session_state.config_text,
        height=250
    )

st.markdown("<br>", unsafe_allow_html=True)

# --- Process Button ---
process_button = st.button("Convert MIDI", type="primary", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True) # Close main container

# --- Processing Logic ---
if process_button:
    st.session_state.output_data = None
    st.session_state.error_message = None
    sound_folder_path = "./sounds"  # Hardcoded as requested

    if uploaded_midi is None:
        st.session_state.error_message = "Please upload a MIDI file."
    elif not os.path.isdir(sound_folder_path):
        st.session_state.error_message = f"Sound folder not found at './sounds'. Please create it and add the required .wav files."
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

# --- Display Results or Errors ---
if st.session_state.error_message:
    st.error(st.session_state.error_message, icon="🚨")

if st.session_state.output_data:
    st.success("Conversion successful! Your song data is ready below.", icon="✅")

    st.markdown('<div class="results-container">', unsafe_allow_html=True)
    st.subheader("3. Copy Output to Bloxd")
    st.caption("Click inside each box and press Ctrl+C (or Cmd+C on Mac) to copy the text.")

    col1, col2 = st.columns(2)
    with col1:
        st.text_area("Sounds Data", value=st.session_state.output_data.get("sounds", ""), key="sounds_output", help="Paste into the 'Sounds' music block.")
        st.text_area("Notes Data", value=st.session_state.output_data.get("notes", ""), key="notes_output", help="Paste into the 'Notes' music block.")
    with col2:
        st.text_area("Delays Data", value=st.session_state.output_data.get("delays", ""), key="delays_output", help="Paste into the 'Delays' music block.")
        st.text_area("Volumes Data", value=st.session_state.output_data.get("volumes", ""), key="volumes_output", help="Paste into the 'Volumes' music block.")
    
    # Display Audio Preview if it exists
    if 'preview_path' in st.session_state.output_data:
        st.markdown("---")
        st.subheader("Audio Preview")
        st.info("This is close to how your song will sound in game.", icon="🎵")

        try:
            with open(st.session_state.output_data['preview_path'], 'rb') as audio_file:
                st.audio(audio_file.read(), format='audio/wav')
        except FileNotFoundError:
             st.warning("Could not find the audio preview file. It may have been moved or deleted.")

    st.markdown('</div>', unsafe_allow_html=True)

# --- Footer ---
st.markdown('<div class="footer">Made by chmod</div>', unsafe_allow_html=True)
import streamlit as st
import json
import os
import tempfile
from processor import run_processing, strip_extension, PIANO_SOUND_DATA

# --- Page Configuration ---
st.set_page_config(
    page_title="MIDI to Bloxd Music Converter",
    layout="centered",
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

# --- Custom CSS for a clean, modern UI ---
st.markdown("""
<style>
    /* Base variables for theming */
    :root {
        --primary-color: #007bff;
        --border-radius: 0.5rem;
    }
    
    /* Main app styling */
    .stApp {
        background-color: #f0f2f6;
    }
    body[data-theme="dark"] .stApp {
        background-color: #0e1117;
    }

    /* Main button styling */
    .stButton > button {
        background-color: var(--primary-color);
        color: white;
        border-radius: var(--border-radius);
        border: none;
        height: 3rem;
        font-weight: 500;
        transition: all 0.2s ease-in-out;
    }
    .stButton > button:hover {
        background-color: #0056b3;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Expander styling */
    div[data-testid="stExpander"] {
        border: 1px solid #e6e6e6;
        border-radius: var(--border-radius);
        background-color: white;
    }
    body[data-theme="dark"] div[data-testid="stExpander"] {
        border-color: #333;
        background-color: #262730;
    }

    /* Customize st.code blocks to look more like plain text boxes */
    .stCode {
        font-family: 'Courier New', Courier, monospace !important;
    }
    div[data-testid="stCodeBlock"] > div {
        border-radius: var(--border-radius);
    }

    /* Footer */
    .footer {
        text-align: right;
        color: grey;
        font-size: 0.9em;
        padding-top: 3rem;
        opacity: 0.8;
    }
</style>
""", unsafe_allow_html=True)

# --- Main Application Layout ---
st.title("MIDI to Bloxd Music Converter")
st.caption("Convert your MIDI files into a format compatible with Bloxd.io's music system.")
st.markdown("---")

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
process_button = st.button("Convert MIDI", use_container_width=True)
st.markdown("---")


# --- Processing Logic ---
if process_button:
    st.session_state.output_data = None
    st.session_state.error_message = None
    sound_folder_path = "./sounds"

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

            with st.spinner('Processing your MIDI...'):
                output_dir = run_processing(midi_path, config_data, render_preview, sound_folder_path)
            os.unlink(midi_path)

            if output_dir:
                st.success("Conversion successful! Your song data is ready below.", icon="✅")
                st.session_state.output_data = {}
                base_name = os.path.basename(output_dir)
                file_map = {
                    "sounds": f"1_{base_name}_sounds.txt",
                    "delays": f"2_{base_name}_delays.txt",
                    "notes": f"3_{base_name}_notes.txt",
                    "volumes": f"4_{base_name}_volumes.txt",
                    "preview": f"8_{base_name}_preview.wav"
                }
                for key, filename in file_map.items():
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
            st.session_state.error_message = "Invalid JSON in configuration."
        except Exception as e:
            st.session_state.error_message = f"An error occurred: {e}"

# --- Display Results ---
if st.session_state.error_message:
    st.error(st.session_state.error_message, icon="🚨")

if st.session_state.output_data:
    st.subheader("3. Copy Output to Bloxd")
    st.caption("Hover over the text blocks below to see the copy button on the right.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Sounds Data**")
        st.code(st.session_state.output_data.get("sounds", ""), language="text")
        st.markdown("**Notes Data**")
        st.code(st.session_state.output_data.get("notes", ""), language="text")
    with col2:
        st.markdown("**Delays Data**")
        st.code(st.session_state.output_data.get("delays", ""), language="text")
        st.markdown("**Volumes Data**")
        st.code(st.session_state.output_data.get("volumes", ""), language="text")
    
    if 'preview_path' in st.session_state.output_data:
        st.markdown("---")
        st.subheader("Audio Preview")
        st.info("This is a close approximation of how your song will sound in-game.", icon="🎵")
        try:
            with open(st.session_state.output_data['preview_path'], 'rb') as audio_file:
                st.audio(audio_file.read(), format='audio/wav')
        except FileNotFoundError:
             st.warning("Could not find the audio preview file.")

# --- Footer ---
st.markdown('<div class="footer">Made by chmod</div>', unsafe_allow_html=True)
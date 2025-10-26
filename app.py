# app.py

import streamlit as st
import json
import os
import tempfile
from processor import run_processing, strip_extension, PIANO_SOUND_DATA

# --- Page Configuration ---
# This is set first and is now complemented by the config.toml file
st.set_page_config(
    page_title="MIDI to Bloxd Music Converter",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- Default Configuration & State Management ---
if 'config_text' not in st.session_state:
    DEFAULT_CONFIG = {
        "palette": [strip_extension(s['filename']) for s in PIANO_SOUND_DATA],
        "layering": {
            "comment": "Max sounds per note. 1 = no layering. >1 = harp_pling + layers. max layer = 5",
            "max_layers": 2
        }
    }
    st.session_state.config_text = json.dumps(DEFAULT_CONFIG, indent=4)

if 'output_data' not in st.session_state:
    st.session_state.output_data = None

# --- Minimal CSS for Layout and Polish ---
# The config.toml handles the colors, this CSS handles the spacing and look.
st.markdown("""
<style>
    /* Center the main content block for a cleaner look */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Make headers lighter and more spaced out */
    h1 {
        font-weight: 300;
        color: #e1e1e1;
        text-align: center;
    }
    h3 {
        font-weight: 400;
        color: #c1c1c1;
        margin-top: 2rem;
    }
    
    /* Style the main "Convert" button to be more prominent */
    .stButton>button {
        height: 3rem;
        font-size: 1.1rem;
        font-weight: bold;
    }

    /* Style the footer */
    .footer {
        text-align: center;
        color: #6c757d;
        font-size: 0.9em;
        margin-top: 4rem;
    }
</style>
""", unsafe_allow_html=True)


# --- Main Application Layout ---
st.title("MIDI to Bloxd Music Converter")
st.caption("Convert your MIDI files into a format compatible with Bloxd.io's music system.")

# --- Inputs ---
st.markdown("<h3>1. Upload MIDI</h3>", unsafe_allow_html=True)
uploaded_midi = st.file_uploader(
    "Upload your .mid or .midi file",
    type=["mid", "midi"],
    label_visibility="collapsed"
)

st.markdown("<h3>2. Settings</h3>", unsafe_allow_html=True)
render_preview = st.checkbox("Generate Audio Preview", value=True, help="Creates a .wav file to simulate how the song will sound in-game.")

with st.expander("Advanced Configuration (JSON)"):
    st.session_state.config_text = st.text_area(
        "Configuration JSON",
        value=st.session_state.config_text,
        height=250,
        label_visibility="collapsed"
    )

st.markdown("<br>", unsafe_allow_html=True)
process_button = st.button("Convert MIDI", type="primary", use_container_width=True)

# --- Processing & Results ---
if process_button:
    st.session_state.output_data = None
    
    if uploaded_midi is None:
        st.error("Please upload a MIDI file first.", icon="🚨")
    else:
        sound_folder_path = "./sounds"
        if not os.path.isdir(sound_folder_path):
            st.error(f"Sound folder missing! Please create a folder named 'sounds' next to this app.", icon="🚨")
        else:
            try:
                config_data = json.loads(st.session_state.config_text)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mid") as tmp_midi:
                    tmp_midi.write(uploaded_midi.getvalue())
                    midi_path = tmp_midi.name

                with st.spinner('Processing... please wait.'):
                    output_dir = run_processing(midi_path, config_data, render_preview, sound_folder_path)
                os.unlink(midi_path)

                if output_dir:
                    st.success("Conversion successful! Your song data is ready below.", icon="✅")
                    output_data = {}
                    base_name = os.path.basename(output_dir)
                    
                    def read_output(key, filename):
                        path = os.path.join(output_dir, filename)
                        if os.path.exists(path):
                            with open(path, 'r', encoding='utf-8') as f: output_data[key] = f.read()
                    
                    read_output("sounds", f"1_{base_name}_sounds.txt")
                    read_output("delays", f"2_{base_name}_delays.txt")
                    read_output("notes", f"3_{base_name}_notes.txt")
                    read_output("volumes", f"4_{base_name}_volumes.txt")
                    
                    preview_path = os.path.join(output_dir, f"8_{base_name}_preview.wav")
                    if os.path.exists(preview_path): output_data['preview_path'] = preview_path
                    st.session_state.output_data = output_data
                else:
                    st.error("Processing finished, but no notes could be mapped.", icon="⚠️")

            except json.JSONDecodeError:
                st.error("Invalid JSON configuration. Please check for errors.", icon="❌")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}", icon="🔥")


if st.session_state.output_data:
    st.markdown("---")
    st.markdown("<h3>3. Results</h3>", unsafe_allow_html=True)
    st.info("Hover over a code block and click the icon in the top-right to copy.", icon="ℹ️")

    col1, col2 = st.columns(2)
    with col1:
        st.write("**Sounds**"); st.code(st.session_state.output_data.get("sounds", ""), language="text")
        st.write("**Notes**"); st.code(st.session_state.output_data.get("notes", ""), language="text")
    with col2:
        st.write("**Delays**"); st.code(st.session_state.output_data.get("delays", ""), language="text")
        st.write("**Volumes**"); st.code(st.session_state.output_data.get("volumes", ""), language="text")

    if 'preview_path' in st.session_state.output_data:
        st.markdown("---")
        st.markdown("<h3>Audio Preview</h3>", unsafe_allow_html=True)
        try:
            with open(st.session_state.output_data['preview_path'], 'rb') as audio_file:
                st.audio(audio_file.read(), format='audio/wav')
        except Exception as e:
            st.warning(f"Could not load audio preview: {e}")

# --- Footer ---
st.markdown('<div class="footer">Made by chmod</div>', unsafe_allow_html=True)
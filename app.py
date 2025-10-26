import streamlit as st
import os
import json
import shutil
import tempfile
from io import StringIO
import sys
import base64

from processor import run_processing

st.set_page_config(
    page_title="MIDI Maestro",
    page_icon="🎵",
    layout="wide"
)

def load_css():
    st.markdown("""
        <style>
            .main {
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            }
            
            .stButton>button {
                color: #ffffff;
                background-color: #ff4b4b;
                border-radius: 8px;
                border: none;
                padding: 10px 20px;
                font-weight: bold;
                transition: all 0.3s ease;
            }
            .stButton>button:hover {
                background-color: #ff6b6b;
                transform: scale(1.05);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }

            .stFileUploader {
                border: 2px dashed #ff4b4b;
                border-radius: 8px;
                padding: 20px;
                background-color: #fff0f0;
            }
            
            .st-emotion-cache-1r6slb0 {
                 border-left: 5px solid #ff4b4b;
                 padding-left: 15px;
            }
            
        </style>
    """, unsafe_allow_html=True)

load_css()

if 'results' not in st.session_state:
    st.session_state.results = None

st.title("🎵 MIDI Maestro: Game Format Converter")
st.markdown("Welcome! This tool converts your MIDI files into a game-ready format. Follow the simple steps below.")
st.divider()

with st.sidebar:
    st.header("⚙️ Advanced Configuration")
    
    render_preview = st.checkbox(
        "Render .wav audio preview",
        value=True,
        help="Creates an audio preview of the final result. Highly recommended."
    )

    st.subheader("Config JSON")
    default_config = {
        "palette": ["harp_pling", "game_start_countdown_01", "game_start_countdown_02", "game_start_countdown_03", "game_start_countdown_final"],
        "layering": {"comment": "Max sounds per note. 1 = no layering.", "max_layers": 2}
    }
    config_text = st.text_area(
        "You can edit the JSON configuration for advanced control over sound layering and palettes.",
        value=json.dumps(default_config, indent=4),
        height=300
    )

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.header("Step 1: Upload Your MIDI")
    st.markdown("""
    - Click the **'Browse files'** button or drag and drop your `.mid` file into the box.
    - Only one file can be processed at a time.
    """)
    midi_file = st.file_uploader(
        "Upload your MIDI file here",
        type=["mid", "midi"],
        label_visibility="collapsed"
    )

with col2:
    st.header("Step 2: Process It!")
    st.markdown("""
    - Once your file is uploaded, click the button below to start the conversion.
    - If you need to change settings, use the sidebar on the left.
    """)
    process_button = st.button("🚀 Convert My MIDI!", use_container_width=True)


if process_button:
    if not midi_file:
        st.warning("Please upload a MIDI file first!", icon="⚠️")
    else:
        try:
            user_config = json.loads(config_text)
            SOUND_FOLDER_PATH = "sounds"

            with tempfile.TemporaryDirectory() as temp_dir:
                midi_file_path = os.path.join(temp_dir, midi_file.name)
                with open(midi_file_path, "wb") as f:
                    f.write(midi_file.getbuffer())

                with st.spinner(f"Maestro at work... Converting '{midi_file.name}'..."):
                    old_stdout = sys.stdout
                    sys.stdout = captured_output = StringIO()

                    output_dir_path = run_processing(
                        midi_file_path=midi_file_path,
                        config_data=user_config,
                        render_preview_flag=render_preview,
                        sound_folder_path=SOUND_FOLDER_PATH
                    )
                    
                    sys.stdout = old_stdout
                    log_output = captured_output.getvalue()

                if output_dir_path and os.path.exists(output_dir_path):
                    st.success("Conversion complete! Your files are ready below.", icon="🎉")
                    
                    base_name = os.path.splitext(midi_file.name)[0]
                    zip_path_base = os.path.join(temp_dir, f"{base_name}_results")
                    shutil.make_archive(zip_path_base, 'zip', output_dir_path)
                    zip_file_path = f"{zip_path_base}.zip"

                    with open(zip_file_path, "rb") as f:
                        zip_data = f.read()

                    preview_data = None
                    if render_preview:
                        preview_filename = f"8_{base_name}_preview.wav"
                        preview_path = os.path.join(output_dir_path, preview_filename)
                        if os.path.exists(preview_path):
                            with open(preview_path, "rb") as f:
                                preview_data = f.read()

                    st.session_state.results = {
                        "zip_data": zip_data,
                        "zip_filename": f"{base_name}_results.zip",
                        "preview_data": preview_data,
                        "log": log_output
                    }
                else:
                    st.error("Processing failed. No output files were generated.")
                    st.session_state.results = {"log": log_output}

        except json.JSONDecodeError:
            st.error("Invalid JSON in the configuration. Please check the syntax.", icon="❌")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}", icon="🔥")

if st.session_state.results:
    st.divider()
    st.header("🎉 Your Results")

    results_data = st.session_state.results

    if results_data.get("preview_data"):
        st.subheader("Listen to the Preview")
        st.audio(results_data["preview_data"], format='audio/wav')

    if results_data.get("zip_data"):
        st.subheader("Download All Files")
        st.download_button(
            label="📥 Download Results (.zip)",
            data=results_data["zip_data"],
            file_name=results_data["zip_filename"],
            mime="application/zip",
            use_container_width=True
        )

    if results_data.get("log"):
        with st.expander("Show Processing Log"):
            st.code(results_data["log"], language="bash")
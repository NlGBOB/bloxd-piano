import streamlit as st
import os
import json
import shutil
import tempfile
from io import StringIO
import sys
from processor import run_processing

st.set_page_config(
    page_title="MIDI Processor",
    page_icon="🎵",
    layout="wide"
)

st.title("🎵 MIDI to Game Format Converter")
st.markdown("""
Upload your MIDI file. This tool will process it using a built-in sound palette 
and generate a set of data files for the game.
""")

with st.sidebar:
    st.header("⚙️ Configuration")
    midi_file = st.file_uploader(
        "1. Upload your MIDI file",
        type=["mid", "midi"]
    )

    render_preview = st.checkbox(
        "Render .wav audio preview",
        value=True,
        help="If checked, an audio preview will be generated (takes longer)."
    )

    st.subheader("2. Edit Config (Optional)")
    default_config = {
        "palette": [
            "harp_pling",
            "game_start_countdown_01",
            "game_start_countdown_02",
            "game_start_countdown_03",
            "game_start_countdown_final"
        ],
        "layering": {
            "comment": "Max sounds per note. 1 = no layering. >1 = harp_pling + layers. max layer = 5",
            "max_layers": 2
        }
    }
    config_text = st.text_area(
        "Config JSON",
        value=json.dumps(default_config, indent=4),
        height=250
    )

if st.button("🚀 Process MIDI File"):
    if not midi_file:
        st.error("❌ Please upload a MIDI file.")
    else:
        try:
            user_config = json.loads(config_text)
            SOUND_FOLDER_PATH = "sounds"
            with tempfile.TemporaryDirectory() as temp_dir:
                midi_file_path = os.path.join(temp_dir, midi_file.name)
                with open(midi_file_path, "wb") as f:
                    f.write(midi_file.getbuffer())

                st.info(f"✅ MIDI file uploaded. Starting processing for '{midi_file.name}'...")
                with st.spinner("Processing... This may take a moment."):
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
                    st.success("🎉 Processing complete!")
                    st.subheader("📜 Processing Log")
                    st.code(log_output, language="bash")
                    zip_path_base = os.path.join(temp_dir, f"{os.path.basename(midi_file.name)}_results")
                    shutil.make_archive(zip_path_base, 'zip', output_dir_path)
                    
                    zip_file_path = f"{zip_path_base}.zip"
                    with open(zip_file_path, "rb") as fp:
                        st.download_button(
                            label="📥 Download All Results (.zip)",
                            data=fp,
                            file_name=f"{os.path.splitext(midi_file.name)[0]}_results.zip",
                            mime="application/zip",
                        )
                else:
                    st.error("Processing failed. No output files were generated.")
                    st.subheader("📜 Processing Log")
                    st.code(log_output, language="bash")

        except json.JSONDecodeError:
            st.error("❌ Invalid JSON in the configuration. Please check the syntax.")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
# MIDI to Bloxd Music Converter

This tool converts standard MIDI files (`.mid`) into a series of compact text strings that can be used with Code Blocks in [Bloxd.io](https://bloxd.io/) to play music. It allows for complex arrangements, sound layering, and even provides an audio preview to hear how your song will sound in-game before you set it up.

## Features

-   **MIDI Conversion**: Translates musical notes from a MIDI file into a format the game understands.
-   **Configurable Sound Palette**: Choose which in-game sounds you want to use for your song.
-   **Sound Layering**: Creates richer audio by playing multiple sounds for a single note.
-   **Audio Preview**: Generates a `.wav` file to simulate the in-game audio output, saving you time.
-   **Detailed Reporting**: Creates human-readable logs and JSON reports about which sounds were used and how often.
-   **Automated Output**: Organizes all generated files into a dedicated results folder.

## Requirements

-   Python 3.6 or newer.
-   The following Python libraries: `numpy`, `mido`, and `scipy`.

## ⚙️ How to Use

Follow these steps to get your MIDI music into Bloxd!

## 🚀Easiest Method: Use the Online Web App!

### **Go to the Bloxd Piano Web App**
https://bloxd-piano.streamlit.app/

The web app handles the conversion process for you. You can **completely skip Steps 1 through 5** below.

**How it works:**
1.  Visit the web app link above.
2.  Upload your `.mid`/`.midi` file.
3.  Configure the `palette` and `layering` options (if you want)
4.  Click "Convert", and wait until it generates 4 code blocks

Once you have your text files, **jump directly to Step 6: In-Game Setup**.

*(The original command-line instructions are kept below for advanced users or those who prefer to run the script locally.)*

### Step 1: Installation

1.  **Download the repo**: Use `git clone https://github.com/NlGBOB/bloxd-piano.git` in your command line to download the repository.
2.  **Install Dependencies**: In the terminal run the following command to install the required libraries:
    ```bash
    pip install numpy mido scipy
    ```

### Step 2: Get a Piano MIDI File

The script works best with MIDI files that are made for a **single piano track**. If your MIDI contains drums, bass, strings, and other instruments, the script will try to map them all to the available sounds, which can result in a chaotic and unpleasant sound.

**Where to find good MIDI files?**

-   **Musescore**: [musescore.com](https://musescore.com) is an excellent source for high-quality piano sheet music and MIDI files.
    > **Tip**: While Musescore has a subscription model, the open-source project [LibreScore](https://github.com/LibreScore/dl-librescore) can be helpful for accessing resources.
-   Search for "piano midi downloads" online. Always look for files that are specifically piano arrangements.

Place your downloaded `.mid` files into a convenient folder, for example, a new folder called `midis`.

### Step 3: Configure `config.json`

The `config.json` file controls how the script behaves. If you delete it, a default one will be created the next time you run the script.

Here’s a breakdown of the settings:

```json
{
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
```

-   `"palette"`: This is an array of the in-game sounds you want the script to use. Only sounds listed here will be included in the song. You can remove sounds you don't like from the list. The default five are a good starting point.
-   `"layering"`:
    -   `"max_layers"`: This defines how many sounds can be played for a single note.
        -   `1`: No layering. The script will pick the single best sound for each note.
        -   `2`: The script will use the primary sound (`harp_pling`) plus one additional "layer" sound for a richer, fuller tone.
        -   `3` or more: Adds even more layers, up to the maximum of 5. `2` or `3` is usually a good balance.

### Step 4: Run the Script

Open your terminal or command prompt, navigate to the folder containing the script, and run it.

**Basic Command:**

```bash
python3 midi_to_bloxd.py "path/to/your/song.mid"
```
*Example:*
```bash
python3 midi_to_bloxd.py midis/gadd.mid
```

**Recommended: Render an Audio Preview**

To hear what your song will sound like, use the `--render-preview` flag. This requires the original `.wav` sound files from the game.


Run the script with the flag:

```bash
python3 midi_to_bloxd.py midis/gadd.mid --render-preview
```

### Step 5: Understanding the Output

After running, the script creates a new directory: `results/<your_song_name>/`. Inside, you will find several files:

-   `1_..._sounds.txt`: A string of numbers (0-4) representing which sound from the palette to play.
-   `2_..._delays.txt`: A string of special characters representing the delay (in game ticks) before playing the sound.
-   `3_..._notes.txt`: A string of special characters representing the pitch of each note.
-   `4_..._volumes.txt`: A string of numbers representing the volume index.
-   `5_..._note_log.txt`: A detailed, human-readable log. Great for debugging or seeing exactly how the script mapped each note.
-   `6_..._sounds_used.json`: A simple list of all the unique sound names used in your song.
-   `7_..._mapping_report.json`: A breakdown of how many times each sound was used, sorted from most to least common.
-   `8_..._preview.wav`: The audio preview file (if you used `--render-preview`). **Listen to this to check the result!**

### Step 6: In-Game Setup

Now it's time to bring your music into Bloxd! You will need **five Code Blocks**.

1.  **Place Data Blocks**: Place four Code Blocks in a straight line.
2.  **Copy and Paste**:
    -   Open `1_..._sounds.txt`, copy the entire string, and paste it into the **first** Code Block.
    -   Open `2_..._delays.txt`, copy its content, and paste it into the **second** Code Block.
    -   Open `3_..._notes.txt`, copy its content, and paste it into the **third** Code Block.
    -   Open `4_..._volumes.txt`, copy its content, and paste it into the **fourth** Code Block.

3.  **Create the Runner Block**: Place a fifth Code Block somewhere nearby. This will be your "play button". Paste the following code into it:

    ```javascript
    // --- Music Player Runner ---
    // Adjust the coordinates below to match where you placed your data blocks!
    
    // Coords for the 1st block (sounds)
    let sounds = api.getBlockData(1000, 2, 1002).persisted.shared.text
    
    // Coords for the 2nd block (delays)
    let delays = api.getBlockData(1000, 2, 1003).persisted.shared.text
    
    // Coords for the 3rd block (notes)
    let notes = api.getBlockData(1000, 2, 1004).persisted.shared.text
    
    // Coords for the 4th block (volumes)
    let volumes = api.getBlockData(1000, 2, 1005).persisted.shared.text
    
    globalThis.MusicPlayer.playSong(sounds, delays, notes, volumes)
    ```

    **IMPORTANT**: You **must** change the coordinates (`1000, 2, 1002`, etc.) in the runner code to match the exact in-game coordinates of your four data blocks.

4.  **Play Your Song!** Exit the code editor for the runner block and interact with it to play your music.

## ⚠️ Important Limitations & Context

Before you create your masterpiece, keep these in-game technical details in mind:

-   **Song Length Limit**: The game can only handle data strings up to **16,000 characters** long. This means your song is limited to 16,000 total sound events (notes + layers). While most songs will not reach this limit, extremely long or complex pieces might be cut short. You can check the character count of any of the generated `.txt` files to see how long your song is.
-   **Notes Per Tick Limit**: To ensure smooth performance, the game will play a maximum of **50 notes in a single tick**. This is very unlikely to be an issue unless you are using "black MIDI" files with an extreme density of notes.
-   **It's Part of a Scheduler!**: The `globalThis.MusicPlayer` is more than just a music tool; it's a small part of a larger, powerful scheduler system designed for building complex worlds and game logic in Bloxd. The music is designed to run in the background without interrupting your other creations. If you're an advanced creator interested in the full capabilities of the scheduler, feel free to reach out on Discord!


## 🔬 How It Works (A Brief Overview)

The process is split into two parts: the Python script that converts your MIDI, and the smart in-game player that performs the music efficiently.

**1. The Conversion Script (What this tool does):**

-   **Parse MIDI**: The script first reads your `.mid` file and extracts all musical notes, capturing their pitch, start time, and duration.
-   **Find Best Sound**: For each note, it analyzes your chosen `palette` of in-game sounds. It intelligently matches each note to the sound file that best fits its pitch and duration.
-   **Apply Layering**: If `max_layers` in your config is greater than 1, it adds extra, quieter sounds underneath the primary one (`harp_pling`) to create a richer, fuller tone.
-   **Quantize & Encode**: Finally, it snaps all timings to the game's 20-tick-per-second clock and encodes everything - sound choice, pitch, delay, and volume - into the compact text strings for the output files.

**2. The In-Game Player (How the music plays):**

The real magic for performance lies in how the in-game `MusicPlayer` handles this data.

-   **Efficient Chunk Scheduling**: Instead of trying to schedule thousands of notes at once (a common practice that causes lag and memory errors), the player works in small, manageable chunks. By default, it schedules the first **100 notes**.
-   **Seamless Playback**: As the song plays, once the player reaches the 99th note in the current chunk, it automatically schedules the *next* 100 notes. This process repeats seamlessly in the background until the song is finished.
-   **Reliability**: This "just-in-time" scheduling makes the system incredibly efficient and reliable, allowing complex music to play alongside your other world creations without interruption or performance hits.

Enjoy creating music in Bloxd!
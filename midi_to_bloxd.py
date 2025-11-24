import json
import numpy as np
import mido
import os
import argparse
from collections import Counter, defaultdict
from scipy.io import wavfile
from scipy import signal

PIANO_HZ = np.array([27.50, 29.14, 30.87, 32.70, 34.65, 36.71, 38.89, 41.20, 43.65, 46.25, 49.00, 51.91, 55.00, 58.27, 61.74, 65.41, 69.30, 73.42, 77.78, 82.41, 87.31, 92.50, 98.00, 103.83, 110.00, 116.54, 123.47, 130.81, 138.59, 146.83, 155.56, 164.81, 174.61, 185.00, 196.00, 207.65, 220.00, 233.08, 246.94, 261.63, 277.18, 293.66, 311.13, 329.63, 349.23, 369.99, 392.00, 415.30, 440.00, 466.16, 493.88, 523.25, 554.37, 587.33, 622.25, 659.26, 698.46, 739.99, 783.99, 830.61, 880.00, 932.33, 987.77, 1046.50, 1108.73, 1174.66, 1244.51, 1318.51, 1396.91, 1479.98, 1567.98, 1661.22, 1760.00, 1864.66, 1975.53, 2093.00, 2217.46, 2349.32, 2489.02, 2637.02, 2793.83, 2959.96, 3135.96, 3322.44, 3520.00, 3729.31, 3951.07, 4186.01])
NOTE_INDEX_TO_CHAR_MAP = "⁰¹²³⁴⁵⁶⁷⁸⁹ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐᶰⁿᵒᵖʳˢᵗᵘᵛʷˣʸᶻʱʴʵʶ₀₁₂₃₄₅₆₇₈₉ₐₑₒₓₔₕᵢⱼᵣᵤᵥₖₗₘₙₚₛₜ​‌‍⁠⁡⁢⁣⁤⁧⁩⁨⁪⁫⁬⁭⁮⁯﻿︀︁︂︃︄︅︆︇︈︉︊︋︌︍"

if len(PIANO_HZ) > len(NOTE_INDEX_TO_CHAR_MAP): raise ValueError("NOTE_INDEX_TO_CHAR_MAP is not long enough for 88 keys/delays.")

GAME_SOUND_PALETTE = ["harp_pling.wav", "game_start_countdown_01.wav", "game_start_countdown_02.wav", "game_start_countdown_03.wav", "game_start_countdown_final.wav"]
SOUND_TO_INDEX = {sound: i for i, sound in enumerate(GAME_SOUND_PALETTE)}
TICKS_PER_SECOND = 20
PIANO_SOUND_DATA = [
    {"filename": "harp_pling.wav", "base_pitch_hz": 260.79, "base_duration_sec": 0.84},
    {"filename": "game_start_countdown_01.wav", "base_pitch_hz": 329.75, "base_duration_sec": 1.0},
    {"filename": "game_start_countdown_02.wav", "base_pitch_hz": 164.84, "base_duration_sec": 0.99},
    {"filename": "game_start_countdown_03.wav", "base_pitch_hz": 164.87, "base_duration_sec": 1.0},
    {"filename": "game_start_countdown_final.wav", "base_pitch_hz": 658.83, "base_duration_sec": 1.58},
]
PRIMARY_SOUND_NAME = "harp_pling.wav"
LAYER_SOUND_NAMES = [s['filename'] for s in PIANO_SOUND_DATA if s['filename'] != PRIMARY_SOUND_NAME]


def hz_to_closest_piano_note_index(target_hz):
    return np.argmin(np.abs(PIANO_HZ - target_hz))

def strip_extension(name):
    return name[:-4] if isinstance(name, str) and name.lower().endswith('.wav') else name

def load_config(config_path):
    default_config = {
        "palette": [strip_extension(s['filename']) for s in PIANO_SOUND_DATA],
        "layering": {
            "comment": "Max sounds per note. 1 = no layering. >1 = harp_pling + layers. max layer = 5",
            "max_layers": 2
        }
    }
    if not os.path.exists(config_path):
        print(f"Config file not found. Creating a default '{config_path}'.")
        with open(config_path, 'w') as f: json.dump(default_config, f, indent=4)
        return default_config
    try:
        print(f"Loading settings from '{config_path}'.")
        with open(config_path, 'r') as f: user_config = json.load(f)
        for key, value in default_config.items():
            if key not in user_config: user_config[key] = value
        return user_config
    except json.JSONDecodeError:
        print(f"ERROR: Your '{config_path}' is corrupted. Please fix/delete it."); exit(1)

def find_piano_sounds_for_note(target_note, available_sounds, layering_config):
    max_layers = layering_config.get("max_layers", 1)
    candidates = []
    for sound_data in available_sounds:
        rate = target_note['pitch_hz'] / sound_data['base_pitch_hz']
        pitched_duration = sound_data['base_duration_sec'] / rate
        duration_diff = abs(target_note['duration_sec'] - pitched_duration)
        is_primary = sound_data['filename'] == PRIMARY_SOUND_NAME
        if is_primary or (pitched_duration <= target_note['duration_sec']):
            candidates.append({"filename": sound_data['filename'], "rate": rate, "duration_diff": duration_diff})
    if not candidates: return []
    candidates.sort(key=lambda x: x['duration_diff'])
    if max_layers <= 1: return [candidates[0]]
    chosen_sounds = []
    harp_pling_candidate = next((c for c in candidates if c['filename'] == PRIMARY_SOUND_NAME), None)
    if harp_pling_candidate: chosen_sounds.append(harp_pling_candidate)
    layer_candidates = [c for c in candidates if c['filename'] in LAYER_SOUND_NAMES]
    num_layers_to_add = max_layers - 1 if harp_pling_candidate else max_layers
    chosen_sounds.extend(layer_candidates[:num_layers_to_add])
    final_sounds = {sound['filename']: sound for sound in chosen_sounds}
    return list(final_sounds.values())

def midi_to_hz(note_number):           #nice
    return 440.0 * (2.0**((note_number - 69) / 12.0))

def render_simulation_from_events(game_events, sound_folder, output_filename, sample_rate=44100):
    if not game_events: return
    print(f"\n--- Rendering game simulation preview to '{output_filename}' ---")
    sound_data_cache = {}
    unique_sound_files = {GAME_SOUND_PALETTE[e['sound_index']] for e in game_events}
    sounds_loaded = 0
    for sound_file in unique_sound_files:
        try:
            path = os.path.join(sound_folder, sound_file)
            _, data_original = wavfile.read(path)
            data_float = (data_original.astype(np.float32) / 32767.0) if np.issubdtype(data_original.dtype, np.integer) else data_original.astype(np.float32)
            if data_float.ndim > 1: data_float = data_float.mean(axis=1)
            sound_data_cache[sound_file] = data_float
            sounds_loaded += 1
        except Exception as e: print(f"    -> Warning: Could not load sound '{sound_file}': {e}")

    if sounds_loaded == 0:
        print("    -> ERROR: No sound files were loaded. Cannot render preview. Please check the --sound-folder path.")
        return
        
    total_ticks = game_events[-1]['tick'] if game_events else 0
    total_duration_sec = (total_ticks / TICKS_PER_SECOND) + 3.0 # Add 3s for tail
    total_samples = int(total_duration_sec * sample_rate)
    master_track = np.zeros(total_samples, dtype=np.float32)
    print(f"Total song ticks: {total_ticks}. Rendering {total_duration_sec:.2f} seconds of audio...")

    for event in game_events:
        sound_index = event.get('sound_index')
        sound_file = GAME_SOUND_PALETTE[sound_index] if sound_index is not None and 0 <= sound_index < len(GAME_SOUND_PALETTE) else None
        if not sound_file or sound_file not in sound_data_cache: continue
        
        original_data = sound_data_cache[sound_file]
        pitch_rate, volume = event['pitch_rate'], event.get('volume', 1.0)
        
        if pitch_rate <= 0: continue
        
        num_samples_resampled = int(len(original_data) / pitch_rate)
        if num_samples_resampled == 0: continue
        
        resampled_data = signal.resample(original_data, num_samples_resampled) * volume
        start_sample = int((event['tick'] / TICKS_PER_SECOND) * sample_rate)
        
        if start_sample < len(master_track):
            len_to_mix = min(len(resampled_data), len(master_track) - start_sample)
            master_track[start_sample : start_sample + len_to_mix] += resampled_data[:len_to_mix]

    print("Performing final peak normalization and exporting...")
    max_amp = np.max(np.abs(master_track))
    if max_amp > 1.0:
        print(f"    WARNING: Clipping detected (max amplitude: {max_amp:.2f}). Normalizing audio.")
    
    if max_amp > 0.0:
        master_track /= max_amp
    else:
        print("    WARNING: Rendered audio is completely silent. This may happen if the MIDI is empty or sound files were not found.")

    wavfile.write(output_filename, sample_rate, (master_track * 32767).astype(np.int16))
    print(f"Successfully rendered simulation to '{output_filename}'!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Map a MIDI file to a game format using piano sounds.");
    parser.add_argument("midi_file", help="Path to the input MIDI file.");
    parser.add_argument("--config", default="config.json", help="Path to the settings JSON file.");
    parser.add_argument("--render-preview", action="store_true", help="Render a WAV preview simulating the game's output.")
    parser.add_argument("--sound-folder", default="sounds", help="Path to the folder containing the source WAV files for rendering.")
    args = parser.parse_args()
    config = load_config(args.config)

    palette_from_config = set(config.get('palette', []))
    available_sound_data = [s for s in PIANO_SOUND_DATA if strip_extension(s['filename']) in palette_from_config]
    print(f"\n--- Using a palette of {len(available_sound_data)} sounds from config ---")
    print(f"\n--- Pass 1: Parsing MIDI file '{args.midi_file}' ---")
    mid = mido.MidiFile(args.midi_file); parsed_notes = []; active_notes = {}; absolute_time_sec = 0.0
    for msg in mid:
        absolute_time_sec += msg.time
        if msg.type == 'note_on' and msg.velocity > 0: active_notes[(msg.channel, msg.note)] = (absolute_time_sec, msg.velocity)
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            key = (msg.channel, msg.note)
            if key in active_notes:
                start_time, velocity = active_notes.pop(key); duration = absolute_time_sec - start_time
                if duration > 0.01: parsed_notes.append({"start_time": start_time, "pitch_hz": midi_to_hz(msg.note), "duration_sec": duration, "velocity": velocity})
    parsed_notes.sort(key=lambda x: x['start_time'])
    print(f"Found and sorted {len(parsed_notes)} notes.")
    print(f"--- Pass 2: Mapping notes, quantizing data, and applying volume budget ---")
    game_events = []; last_tick = 0
    for note in parsed_notes:
        chosen_sounds = find_piano_sounds_for_note(note, available_sound_data, config['layering'])
        if not chosen_sounds: continue

        note_index = hz_to_closest_piano_note_index(note['pitch_hz'])
        note_char = NOTE_INDEX_TO_CHAR_MAP[note_index]

        layer_sounds = [s for s in chosen_sounds if s['filename'] != PRIMARY_SOUND_NAME]
        num_layers = len(layer_sounds)
        for sound in chosen_sounds:
            if sound['filename'] == PRIMARY_SOUND_NAME:
                sound['volume'] = 1.0
                sound['volume_index'] = 0
            else:
                sound['volume'] = 0.8 / num_layers if num_layers > 0 else 0
                sound['volume_index'] = num_layers
        current_tick = round(note['start_time'] * TICKS_PER_SECOND)
        delay = current_tick - last_tick
        if delay < 0: delay = 0
        for sound in chosen_sounds:
            game_events.append({
                'sound_index': SOUND_TO_INDEX[sound['filename']],
                'note_char': note_char,
                'delay': delay,
                'pitch_rate': sound['rate'],
                'sound_name': strip_extension(sound['filename']),
                'tick': current_tick,
                'volume': sound['volume'],
                'volume_index': sound['volume_index']
            })
            delay = 0
        last_tick = current_tick

    game_events.sort(key=lambda e: e['tick'])
    last_tick = 0
    for event in game_events:
        delay = event['tick'] - last_tick
        event['delay'] = min(delay, 87)
        last_tick = event['tick']

    if game_events:
        base_name = os.path.splitext(os.path.basename(args.midi_file))[0]
        output_dir = os.path.join("results", base_name)
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n--- Pass 3: Generating output files in '{output_dir}' ---")
        sounds_path = os.path.join(output_dir, f"1_{base_name}_sounds.txt")
        delays_path = os.path.join(output_dir, f"2_{base_name}_delays.txt")
        notes_path = os.path.join(output_dir, f"3_{base_name}_notes.txt")
        volumes_path = os.path.join(output_dir, f"4_{base_name}_volumes.txt")
        log_file_path = os.path.join(output_dir, f"5_{base_name}_note_log.txt")
        sounds_used_path = os.path.join(output_dir, f"6_{base_name}_sounds_used.json")
        mapping_report_path = os.path.join(output_dir, f"7_{base_name}_mapping_report.json")
        preview_path = os.path.join(output_dir, f"8_{base_name}_preview.wav")

        sounds_str = "".join([str(e['sound_index']) for e in game_events])
        notes_str = "".join([e['note_char'] for e in game_events])
        delays_str = "".join([NOTE_INDEX_TO_CHAR_MAP[e['delay']] for e in game_events])
        volumes_str = "".join([str(e['volume_index']) for e in game_events])

        with open(sounds_path, "w") as f: f.write(sounds_str)
        with open(delays_path, "w") as f: f.write(delays_str)
        with open(notes_path, "w") as f: f.write(notes_str)
        with open(volumes_path, "w") as f: f.write(volumes_str)
        
        sounds_used = sorted(list(set([e['sound_name'] for e in game_events])))
        with open(sounds_used_path, 'w') as f:
            json.dump(sounds_used, f, indent=4)

        mapping_report = dict(sorted(Counter([e['sound_name'] for e in game_events]).items(), key=lambda item: item[1], reverse=True))
        with open(mapping_report_path, 'w') as f:
            json.dump(mapping_report, f, indent=4)

        print(f"\nSuccessfully exported compact song data and reports to '{output_dir}':\n"
              f"  - 1. Sounds Data:   '{os.path.basename(sounds_path)}'\n"
              f"  - 2. Delays Data:   '{os.path.basename(delays_path)}'\n"
              f"  - 3. Notes Data:    '{os.path.basename(notes_path)}'\n"
              f"  - 4. Volumes Data:  '{os.path.basename(volumes_path)}'\n"
              f"  - 5. Note Log:      '{os.path.basename(log_file_path)}'\n"
              f"  - 6. Sounds Used:   '{os.path.basename(sounds_used_path)}'\n"
              f"  - 7. Mapping Rpt:   '{os.path.basename(mapping_report_path)}'")
        
        print(f"\n--- Generating clear note log to '{os.path.basename(log_file_path)}' ---")
        events_by_tick = defaultdict(list)
        for event in game_events: events_by_tick[event['tick']].append(event)
        
        with open(log_file_path, "w") as log_file:
            for tick in sorted(events_by_tick.keys()):
                time_sec = tick / TICKS_PER_SECOND
                events_at_this_tick = events_by_tick[tick]
                log_file.write(f"Tick: {tick:04d} ({time_sec:.2f}s)\n")
                for event in events_at_this_tick:
                    log_file.write(f"    - Sound: {event['sound_name']:<28} | Vol Idx: {event['volume_index']} | Note Char: {event['note_char']} | (Sim Vol: {event.get('volume', 1.0):.2f}, Sim Rate: {event['pitch_rate']:.2f})\n")
        print(f"Successfully generated note log!")
        if args.render_preview:
            render_simulation_from_events(game_events, args.sound_folder, preview_path)
    else:
        print("\nNo valid notes were mapped. No output files generated.")
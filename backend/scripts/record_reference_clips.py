#!/usr/bin/env python3
"""
Record wake word reference clips for training custom openWakeWord models.

This script helps you record positive (wake word) and negative (non-wake word) 
audio clips needed for training custom verifier models.

Usage:
    python record_reference_clips.py --executive axiom --output-dir data/positive/axiom --mode positive
    python record_reference_clips.py --executive axiom --output-dir data/negative/axiom --mode negative

Requirements:
- sounddevice
- numpy
- scipy (for WAV writing)
"""

import argparse
import os
import sys
import time
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd


EXECUTIVE_WAKE_WORDS = {
    "axiom": ["axiom on", "axiom", "hey axiom", "ok axiom"],
    "jenson": ["jenson", "hey jenson", "hey good jenson", "jensen"],
    "valta_prime": ["valta prime", "valta", "hey valta", "prime"],
    "yamako": ["yamako", "hey yamako", "hey good yamako"],
}

SAMPLE_RATE = 16000
CHANNELS = 1
DURATION = 2.0  # seconds per clip


def record_clip(duration: float = DURATION) -> np.ndarray:
    """Record a single audio clip."""
    print(f"Recording for {duration}s... Speak now!")
    
    # Record
    audio = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=np.int16,
    )
    sd.wait()
    
    return audio.flatten()


def save_clip(audio: np.ndarray, filepath: Path):
    """Save audio clip as WAV file."""
    with wave.open(str(filepath), 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())


def record_positive_clips(executive: str, output_dir: Path, num_clips: int = 10):
    """Record positive wake word clips."""
    wake_words = EXECUTIVE_WAKE_WORDS[executive]
    print(f"\n{'='*60}")
    print(f"Recording POSITIVE clips for {executive.upper()}")
    print(f"Wake words: {wake_words}")
    print(f"Output: {output_dir}")
    print(f"Clips per phrase: {num_clips}")
    print(f"{'='*60}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    clip_num = 0
    for phrase in wake_words:
        print(f"\n--- Phrase: '{phrase}' ---")
        for i in range(num_clips):
            input(f"\nPress Enter to record clip {i+1}/{num_clips} for '{phrase}'...")
            
            audio = record_clip()
            
            # Save with descriptive name
            filename = f"{executive}_{phrase.replace(' ', '_')}_{i+1:03d}.wav"
            filepath = output_dir / filename
            save_clip(audio, filepath)
            print(f"  Saved: {filename}")
            clip_num += 1
            
            # Quick playback for verification
            print("  Playback (press Enter to continue, 'r' to re-record)...")
            sd.play(audio.astype(np.float32) / 32767.0, SAMPLE_RATE)
            sd.wait()
            user_input = input()
            if user_input.lower() == 'r':
                print("  Re-recording...")
                audio = record_clip()
                save_clip(audio, filepath)
                print(f"  Re-saved: {filename}")
    
    print(f"\n✓ Recorded {clip_num} positive clips to {output_dir}")


def record_negative_clips(output_dir: Path, num_clips: int = 20):
    """Record negative (non-wake word) clips."""
    print(f"\n{'='*60}")
    print(f"Recording NEGATIVE clips (background/noise/other speech)")
    print(f"Output: {output_dir}")
    print(f"Target clips: {num_clips}")
    print(f"{'='*60}")
    print("\nRecord various sounds: background noise, random speech,")
    print("other words, silence, music, typing, etc.")
    print("Avoid saying any wake words!")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i in range(num_clips):
        input(f"\nPress Enter to record negative clip {i+1}/{num_clips}...")
        
        audio = record_clip(3.0)  # Longer for negative clips
        
        filename = f"negative_{i+1:03d}.wav"
        filepath = output_dir / filename
        save_clip(audio, filepath)
        print(f"  Saved: {filename}")
        
        # Quick playback
        print("  Playback...")
        sd.play(audio.astype(np.float32) / 32767.0, SAMPLE_RATE)
        sd.wait()
    
    print(f"\n✓ Recorded {num_clips} negative clips to {output_dir}")


def list_audio_devices():
    """List available audio input devices."""
    print("\nAvailable audio input devices:")
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        if d['max_input_channels'] > 0:
            print(f"  [{i}] {d['name']} (in: {d['max_input_channels']} ch)")
    print()


def main():
    parser = argparse.ArgumentParser(description="Record reference clips for wake word training")
    parser.add_argument("--executive", choices=list(EXECUTIVE_WAKE_WORDS.keys()),
                       required=True, help="Executive to record for")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--mode", choices=["positive", "negative"], required=True,
                       help="Recording mode: positive (wake words) or negative (other)")
    parser.add_argument("--num-clips", type=int, default=10,
                       help="Number of clips to record")
    parser.add_argument("--list-devices", action="store_true",
                       help="List audio devices and exit")
    parser.add_argument("--device", type=int, help="Audio device index to use")
    
    args = parser.parse_args()
    
    if args.list_devices:
        list_audio_devices()
        return 0
    
    if args.device is not None:
        sd.default.device = args.device
    
    output_dir = Path(args.output_dir)
    
    if args.mode == "positive":
        record_positive_clips(args.executive, output_dir, args.num_clips)
    else:
        record_negative_clips(output_dir, args.num_clips)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
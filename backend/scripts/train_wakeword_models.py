#!/usr/bin/env python3
"""
Train custom openWakeWord models for Axiom OS executives.

This script trains custom wake word verifier models for each executive:
- Axiom: "axiom on", "axiom", "hey axiom", "ok axiom"
- Jenson: "jenson", "hey jenson", "hey good jenson", "jensen"
- Valta Prime: "valta prime", "valta", "hey valta", "prime"
- Yamako: "yamako", "hey yamako", "hey good yamako"

Requirements:
- Positive reference clips: Directory of 16kHz 16-bit WAV files containing the wake word
- Negative reference clips: Directory of 16kHz 16-bit WAV files NOT containing the wake word
- Base model: Pre-trained openWakeWord model (e.g., 'hey_jarvis')

Usage:
1. Record positive clips for each wake word phrase (5-10 examples per phrase)
2. Collect negative clips (background noise, other speech)
3. Run this script for each executive

Example:
    python train_wakeword_models.py --executive axiom --positive-dir data/positive/axiom --negative-dir data/negative --output-dir models/wakeword
"""

import argparse
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from openwakeword.custom_verifier_model import train_custom_verifier
from openwakeword.utils import download_models


EXECUTIVE_WAKE_WORDS = {
    "axiom": ["axiom on", "axiom", "hey axiom", "ok axiom"],
    "jenson": ["jenson", "hey jenson", "hey good jenson", "jensen"],
    "valta_prime": ["valta prime", "valta", "hey valta", "prime"],
    "yamako": ["yamako", "hey yamako", "hey good yamako"],
}

# Base model to use for training
BASE_MODEL = "hey_jarvis"


def ensure_base_model(models_dir: Path):
    """Download base model if not present."""
    base_model_path = models_dir / f"{BASE_MODEL}_v0.1.onnx"
    if not base_model_path.exists():
        print(f"Downloading base model: {BASE_MODEL}")
        download_models(model_names=[BASE_MODEL], target_directory=str(models_dir))
    return base_model_path


def train_executive_model(
    executive: str,
    positive_dir: Path,
    negative_dir: Path,
    output_dir: Path,
    models_dir: Path,
):
    """Train a custom verifier model for an executive."""
    
    wake_words = EXECUTIVE_WAKE_WORDS[executive]
    print(f"\n{'='*60}")
    print(f"Training model for {executive.upper()}")
    print(f"Wake words: {wake_words}")
    print(f"{'='*60}")
    
    # Verify directories exist
    if not positive_dir.exists():
        print(f"ERROR: Positive directory not found: {positive_dir}")
        return False
    
    if not negative_dir.exists():
        print(f"ERROR: Negative directory not found: {negative_dir}")
        return False
    
    # Count files
    positive_files = list(positive_dir.glob("*.wav"))
    negative_files = list(negative_dir.glob("*.wav"))
    
    print(f"Positive clips: {len(positive_files)}")
    print(f"Negative clips: {len(negative_files)}")
    
    if len(positive_files) < 5:
        print("WARNING: Less than 5 positive clips - results may be poor")
    
    if len(negative_files) < 10:
        print("WARNING: Less than 10 negative clips - results may be poor")
    
    # Ensure base model exists
    base_model_path = ensure_base_model(models_dir)
    
    # Output path
    output_path = output_dir / f"{executive}_verifier.joblib"
    
    try:
        print(f"Training verifier model...")
        train_custom_verifier(
            positive_reference_clips=str(positive_dir),
            negative_reference_clips=str(negative_dir),
            output_path=str(output_path),
            model_name=str(base_model_path),
            inference_framework="onnx",
        )
        print(f"✓ Model saved to: {output_path}")
        return True
        
    except Exception as e:
        print(f"✗ Training failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description="Train custom wake word models for Axiom executives")
    parser.add_argument("--executive", choices=list(EXECUTIVE_WAKE_WORDS.keys()) + ["all"], 
                       default="all", help="Executive to train (default: all)")
    parser.add_argument("--positive-dir", required=True, help="Directory with positive reference clips")
    parser.add_argument("--negative-dir", required=True, help="Directory with negative reference clips")
    parser.add_argument("--output-dir", default="runtime/state/models/wakeword", help="Output directory for models")
    parser.add_argument("--models-dir", default="runtime/state/models/wakeword", help="Base models directory")
    
    args = parser.parse_args()
    
    positive_dir = Path(args.positive_dir)
    negative_dir = Path(args.negative_dir)
    output_dir = Path(args.output_dir)
    models_dir = Path(args.models_dir)
    
    # Create output directories
    output_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine which executives to train
    if args.executive == "all":
        executives = list(EXECUTIVE_WAKE_WORDS.keys())
    else:
        executives = [args.executive]
    
    print(f"Training wake word models for: {executives}")
    print(f"Positive dir: {positive_dir}")
    print(f"Negative dir: {negative_dir}")
    print(f"Output dir: {output_dir}")
    print(f"Models dir: {models_dir}")
    
    # Train each executive
    success_count = 0
    for exec_id in executives:
        # Each executive has their own positive/negative directories
        exec_positive = positive_dir / exec_id
        exec_negative = negative_dir / exec_id
        
        if not exec_positive.exists():
            print(f"\nSkipping {exec_id}: positive directory not found: {exec_positive}")
            continue
        
        if not exec_negative.exists():
            print(f"\nSkipping {exec_id}: negative directory not found: {exec_negative}")
            continue
        
        if train_executive_model(exec_id, exec_positive, exec_negative, output_dir, models_dir):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"Training complete: {success_count}/{len(executives)} successful")
    print(f"{'='*60}")
    
    return 0 if success_count == len(executives) else 1


if __name__ == "__main__":
    sys.exit(main())
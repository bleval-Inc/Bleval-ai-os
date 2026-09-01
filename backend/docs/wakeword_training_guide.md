# Wake Word Model Training Guide

This guide explains how to record reference clips and train custom openWakeWord models for each Axiom OS executive.

## Overview

Each executive needs a custom wake word verifier model trained on:
- **Positive clips**: Recordings of the wake word phrases
- **Negative clips**: Recordings of other speech/noise (NOT containing wake words)

## Prerequisites

```bash
cd backend
pip install openwakeword sounddevice numpy scipy
```

## Step 1: Record Reference Clips

### Positive Clips (Wake Words)

For each executive, record 5-10 clips per wake word phrase:

```bash
# Axiom
python scripts/record_reference_clips.py \
  --executive axiom \
  --output-dir data/positive/axiom \
  --mode positive \
  --num-clips 10

# Jenson
python scripts/record_reference_clips.py \
  --executive jenson \
  --output-dir data/positive/jenson \
  --mode positive \
  --num-clips 10

# Valta Prime
python scripts/record_reference_clips.py \
  --executive valta_prime \
  --output-dir data/positive/valta_prime \
  --mode positive \
  --num-clips 10

# Yamako
python scripts/record_reference_clips.py \
  --executive yamako \
  --output-dir data/positive/yamako \
  --mode positive \
  --num-clips 10
```

**Tips for positive clips:**
- Speak naturally, as you would when using the system
- Vary your distance from the microphone (close, arm's length, across room)
- Vary background noise (quiet room, TV in background, typing, etc.)
- Say each phrase clearly but conversationally

### Negative Clips (Non-Wake Words)

Record 20-30 clips of non-wake-word audio for each executive:

```bash
# Axiom negative clips
python scripts/record_reference_clips.py \
  --executive axiom \
  --output-dir data/negative/axiom \
  --mode negative \
  --num-clips 30

# Jenson negative clips
python scripts/record_reference_clips.py \
  --executive jenson \
  --output-dir data/negative/jenson \
  --mode negative \
  --num-clips 30

# Valta Prime negative clips
python scripts/record_reference_clips.py \
  --executive valta_prime \
  --output-dir data/negative/valta_prime \
  --mode negative \
  --num-clips 30

# Yamako negative clips
python scripts/record_reference_clips.py \
  --executive yamako \
  --output-dir data/negative/yamako \
  --mode negative \
  --num-clips 30
```

**Tips for negative clips:**
- Record background noise (silence, fan, AC, traffic)
- Record random speech (read a book, have a conversation)
- Record similar-sounding words that are NOT wake words
- Record other executives' wake words
- Record typing, mouse clicks, paper shuffling
- Vary volume and distance from mic

## Step 2: Train Models

Once you have reference clips for all executives:

```bash
# Train all executives
python scripts/train_wakeword_models.py \
  --executive all \
  --positive-dir data/positive \
  --negative-dir data/negative \
  --output-dir runtime/state/models/wakeword \
  --models-dir runtime/state/models/wakeword

# Or train a single executive
python scripts/train_wakeword_models.py \
  --executive axiom \
  --positive-dir data/positive \
  --negative-dir data/negative \
  --output-dir runtime/state/models/wakeword \
  --models-dir runtime/state/models/wakeword
```

This will produce verifier models (`*_verifier.joblib`) in the output directory.

## Step 3: Verify Models

The trained verifier models work alongside the base openWakeWord models. The pipeline will:
1. Use base model (hey_jarvis) for initial detection
2. Apply verifier model for voice-specific confirmation

To test a model:

```python
from openwakeword import Model
import numpy as np

# Load base model + verifier
model = Model(
    wakeword_models=["runtime/state/models/wakeword/hey_jarvis_v0.1.onnx"],
    inference_framework="onnx"
)

# The verifier is applied automatically during prediction
# Test with audio
audio = np.random.randint(-32768, 32767, 16000, dtype=np.int16)
predictions = model.predict(audio)
print(predictions)
```

## Step 4: Deploy

The pipeline automatically loads models from `runtime/state/models/wakeword/`. 
Model files expected:
- `axiom.onnx` / `axiom_verifier.joblib`
- `jenson.onnx` / `jenson_verifier.joblib`
- `valta_prime.onnx` / `valta_prime_verifier.joblib`
- `yamako.onnx` / `yamako_verifier.joblib`

## Directory Structure

```
backend/
├── data/
│   ├── positive/
│   │   ├── axiom/
│   │   │   ├── axiom_axiom_on_001.wav
│   │   │   ├── axiom_hey_axiom_001.wav
│   │   │   └── ...
│   │   ├── jenson/
│   │   ├── valta_prime/
│   │   └── yamako/
│   └── negative/
│       ├── axiom/
│       │   ├── negative_001.wav
│       │   └── ...
│       ├── jenson/
│       ├── valta_prime/
│       └── yamako/
├── runtime/
│   └── state/
│       └── models/
│           └── wakeword/
│               ├── hey_jarvis_v0.1.onnx (base model)
│               ├── axiom_verifier.joblib
│               ├── jenson_verifier.joblib
│               ├── valta_prime_verifier.joblib
│               └── yamako_verifier.joblib
└── scripts/
    ├── record_reference_clips.py
    └── train_wakeword_models.py
```

## Troubleshooting

### Poor Detection Accuracy
- Record more positive clips (15-20 per phrase)
- Ensure negative clips are diverse
- Check audio quality (16kHz, 16-bit, mono)
- Adjust confidence threshold in config

### Model Loading Errors
- Ensure ONNX models are in the models directory
- Verify verifier .joblib files exist
- Check file permissions

### Audio Device Issues
```bash
# List devices
python scripts/record_reference_clips.py --list-devices

# Specify device
python scripts/record_reference_clips.py ... --device 2
```

## Model Architecture

The training uses a two-stage approach:
1. **Base Model** (hey_jarvis): General wake word detection using embeddings
2. **Verifier Model**: Logistic regression on embedding features, specific to your voice

This provides speaker-dependent wake word detection with high accuracy for the enrolled user.

## Advanced: Using Different Base Models

The `hey_jarvis` model is used by default. You can experiment with other base models:
- `alexa` - Amazon Alexa style
- `hey_mycroft` - Mycroft AI style  
- `hey_rhasspy` - Rhasspy style
- `timer` - Timer command
- `weather` - Weather command

```bash
python scripts/train_wakeword_models.py ... --base-model hey_mycroft
```

(Note: This would require modifying the script to accept a base model parameter)
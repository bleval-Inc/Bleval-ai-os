# Training Custom Wake Word Models for Axiom OS

This guide explains how to train custom wake word models for the entities: axiom, jenson, yamako, valtaprime.

## Prerequisites

1. Python environment with openwakeword installed (already in backend/.venv)
2. Audio data for each wake phrase:
   - Positive samples: recordings of "hey axiom", "hey jenson", "hey yamako", "hey valtaprime"
   - Negative samples: background noise, random speech, other phrases
3. Recommended: At least 50+ positive samples and 100+ negative samples per entity

## Method 1: Generate Synthetic Data with TTS (Quick Start)

Run the data generation script:

```bash
cd C:\Users\byagi\Desktop\Bleval-ai-os
backend\.venv\Scripts\python.exe generate_wake_word_data.py
```

This creates:
- `positive_samples/axiom/` - 20 variations of "hey axiom"
- `positive_samples/jenson/` - 20 variations of "hey jenson"
- `positive_samples/yamako/` - 20 variations of "hey yamako"
- `positive_samples/valtaprime/` - 20 variations of "hey valtaprime"
- `negative_samples/` - 60 negative samples (mixed speech, noise, silence)

## Method 2: Use Your Own Audio Data

Organize your data as:
```
training_data/
├── positive_samples/
│   ├── axiom/
│   │   ├── hey_axiom_001.wav
│   │   └── ...
│   ├── jenson/
│   ├── yamako/
│   └── valtaprime/
└── negative_samples/
    ├── background_noise_001.wav
    ├── random_speech_001.wav
    └── ...
```

## Training Command

For each entity, run:

```bash
cd C:\Users\byagi\Desktop\Bleval-ai-os\backend
backend\.venv\Scripts\python.exe -m openwakeword.train \
    --positive-data-path ../positive_samples/ENTITY_NAME \
    --negative-data-path ../negative_samples \
    --output-model-dir ../trained_models \
    --wakeword hey_ENTITY_NAME \
    --batch-size 32 \
    --epochs 30
```

Replace `ENTITY_NAME` with `axiom`, `jenson`, `yamako`, or `valtaprime`.

Example for axiom:
```bash
backend\.venv\Scripts\python.exe -m openwakeword.train \
    --positive-data-path ../positive_samples/axiom \
    --negative-data-path ../negative_samples \
    --output-model-dir ../trained_models \
    --wakeword hey_axiom \
    --batch-size 32 \
    --epochs 30
```

## Post-Training Steps

1. The trained model will be saved as:
   `../trained_models/hey_ENTITY_NAME/hey_entity_name_v0.1.onnx`

2. Update `axiom_voice_pipeline/config.py`:
   - Change `model_paths` to point to your trained models
   - Example:
     ```python
     model_paths: Dict[str, str] = {
         "axiom": "C:/Users/byagi/Desktop/Bleval-ai-os/trained_models/hey_axiom/hey_axiom_v0.1.onnx",
         "jenson": "C:/Users/byagi/Desktop/Bleval-ai-os/trained_models/hey_jenson/hey_jenson_v0.1.onnx",
         "yamako": "C:/Users/byagi/Desktop/Bleval-ai-os/trained_models/hey_yamako/hey_yamako_v0.1.onnx",
         "valtaprime": "C:/Users/byagi/Desktop/Bleval-ai-os/trained_models/hey_valtaprime/hey_valtaprime_v0.1.onnx"
     }
     ```

3. Restart the pipeline and test with actual wake word audio.

## Verification

After updating config, test with:
```bash
cd backend
backend\.venv\Scripts\python.exe ..\test_full_pipeline.py
```

The system should now respond to "hey axiom", "hey jenson", etc.
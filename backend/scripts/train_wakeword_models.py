#!/usr/bin/env python3
"""
Train independent custom wake-word classifiers for AXIOM OS.

Creates:
    runtime/state/models/wakeword/axiom.onnx
    runtime/state/models/wakeword/jenson.onnx
    runtime/state/models/wakeword/valta_prime.onnx
    runtime/state/models/wakeword/yamako.onnx

Dataset layout:
    data/positive/<executive>/*.wav
    data/negative/<executive>/*.wav

Each WAV must be:
    16 kHz
    mono
    16-bit PCM

This uses openWakeWord's train.Model directly.
It does NOT use train_custom_verifier(), because that function
personalizes an existing wake-word model rather than creating
a new wake-word detector.
"""

import argparse
import random
import sys
from pathlib import Path

import numpy as np
import torch
from scipy.io import wavfile

from openwakeword.train import AudioFeatures, Model


EXECUTIVES = {
    "axiom": ["axiom on", "axiom", "hey axiom", "ok axiom"],
    "jenson": ["jenson", "hey jenson", "hey good jenson", "jensen"],
    "valta_prime": ["valta prime", "valta", "hey valta", "prime"],
    "yamako": ["yamako", "hey yamako", "hey good yamako", "ok yamako"],
}

SAMPLE_RATE = 16000
FEATURE_SHAPE = (16, 96)

SEED = 42
BATCH_SIZE = 32
TRAIN_STEPS = 1000
WARMUP_STEPS = 100
HOLD_STEPS = 300
LEARNING_RATE = 0.0001


def set_seed(seed: int = SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def load_wav(path: Path) -> np.ndarray:
    sr, audio = wavfile.read(str(path))

    if sr != SAMPLE_RATE:
        raise ValueError(
            f"{path}: expected {SAMPLE_RATE} Hz, got {sr} Hz"
        )

    if audio.dtype != np.int16:
        raise ValueError(
            f"{path}: expected int16 PCM, got {audio.dtype}"
        )

    if audio.ndim != 1:
        raise ValueError(
            f"{path}: expected mono audio, got shape {audio.shape}"
        )

    return audio


def extract_features(files, audio_features):
    features = []

    # The classifier expects exactly 2 seconds of audio.
    target_samples = SAMPLE_RATE * 2

    for index, path in enumerate(files, 1):
        audio = load_wav(path)

        # Positive clips are already exactly 2 seconds.
        # Negative clips may be longer, so take the first 2 seconds.
        if len(audio) < target_samples:
            raise ValueError(
                f"{path}: audio is too short "
                f"({len(audio) / SAMPLE_RATE:.2f}s); "
                f"need at least 2.0s"
            )

        if len(audio) > target_samples:
            audio = audio[:target_samples]

        embedded = audio_features.embed_clips(
            audio[None, :],
            batch_size=1,
            ncpu=1,
        )

        if embedded.ndim != 3:
            raise ValueError(
                f"{path}: unexpected feature shape {embedded.shape}"
            )

        feature = embedded[0].astype(np.float32)

        if feature.shape != FEATURE_SHAPE:
            raise ValueError(
                f"{path}: expected feature shape {FEATURE_SHAPE}, "
                f"got {feature.shape}"
            )

        features.append(feature)

        print(
            f"    [{index:02d}/{len(files):02d}] "
            f"{path.name} -> {feature.shape}"
        )

    return np.stack(features).astype(np.float32)

def split_dataset(features, labels, seed=SEED):
    rng = np.random.default_rng(seed)

    positive_indices = np.where(labels == 1)[0]
    negative_indices = np.where(labels == 0)[0]

    rng.shuffle(positive_indices)
    rng.shuffle(negative_indices)

    # 20% validation.
    # Exact counts depend on the number of positive/negative clips.
    pos_val_count = max(1, len(positive_indices) // 5)
    neg_val_count = max(1, len(negative_indices) // 5)

    pos_val = positive_indices[:pos_val_count]
    pos_train = positive_indices[pos_val_count:]

    neg_val = negative_indices[:neg_val_count]
    neg_train = negative_indices[neg_val_count:]

    train_indices = np.concatenate([pos_train, neg_train])
    val_indices = np.concatenate([pos_val, neg_val])

    rng.shuffle(train_indices)
    rng.shuffle(val_indices)

    return (
        features[train_indices],
        labels[train_indices],
        features[val_indices],
        labels[val_indices],
    )


def infinite_batch_generator(features, labels, batch_size=BATCH_SIZE):
    rng = np.random.default_rng(SEED)

    while True:
        indices = rng.permutation(len(features))

        for start in range(0, len(indices), batch_size):
            batch_indices = indices[start:start + batch_size]

            if len(batch_indices) < batch_size:
                continue

            x = torch.from_numpy(features[batch_indices]).float()
            y = torch.from_numpy(labels[batch_indices]).float()

            yield [x, y]


def make_validation_data(features, labels):
    x = torch.from_numpy(features).float()
    y = torch.from_numpy(labels).float()

    return [(x, y)]


def train_one(
    executive: str,
    positive_dir: Path,
    negative_dir: Path,
    output_dir: Path,
):
    print()
    print("=" * 70)
    print(f"TRAINING: {executive.upper()}")
    print("=" * 70)

    positive_files = sorted(positive_dir.glob("*.wav"))

    # Keep this executive's own negative recordings.
    own_negative_files = sorted(negative_dir.glob("*.wav"))

    # Add the other executives' positive recordings as hard negatives.
    # This teaches each classifier to distinguish its own wake word
    # from the other executives' wake words.
    hard_negative_files = []

    for other_executive in EXECUTIVES:
        if other_executive == executive:
            continue

        other_positive_dir = positive_dir.parent / other_executive
        hard_negative_files.extend(
            sorted(other_positive_dir.glob("*.wav"))
        )

    negative_files = own_negative_files + hard_negative_files

    print(f"Positive clips          : {len(positive_files)}")
    print(f"Own negative clips      : {len(own_negative_files)}")
    print(f"Hard-negative clips     : {len(hard_negative_files)}")
    print(f"Total negative clips    : {len(negative_files)}")

    if not positive_files:
        raise RuntimeError(f"No positive WAV files found in {positive_dir}")

    if not negative_files:
        raise RuntimeError(f"No negative WAV files found in {negative_dir}")

    print()
    print("Extracting openWakeWord embeddings...")

    audio_features = AudioFeatures(
        sr=SAMPLE_RATE,
        inference_framework="onnx",
        device="cpu",
        ncpu=1,
    )

    print()
    print("POSITIVE FEATURES")
    positive_features = extract_features(
        positive_files,
        audio_features,
    )

    print()
    print("NEGATIVE FEATURES")
    negative_features = extract_features(
        negative_files,
        audio_features,
    )

    positive_labels = np.ones(len(positive_features), dtype=np.float32)
    negative_labels = np.zeros(len(negative_features), dtype=np.float32)

    features = np.concatenate(
        [positive_features, negative_features],
        axis=0,
    )

    labels = np.concatenate(
        [positive_labels, negative_labels],
        axis=0,
    )

    (
        x_train,
        y_train,
        x_val,
        y_val,
    ) = split_dataset(features, labels)

    print()
    print("DATASET SPLIT")
    print(f"Training samples   : {len(x_train)}")
    print(f"Validation samples : {len(x_val)}")
    print(
        f"Training positives : {int(y_train.sum())}"
    )
    print(
        f"Training negatives : {int((y_train == 0).sum())}"
    )
    print(
        f"Validation positives: {int(y_val.sum())}"
    )
    print(
        f"Validation negatives: {int((y_val == 0).sum())}"
    )

    print()
    print("BUILDING CLASSIFIER...")

    classifier = Model(
        n_classes=1,
        input_shape=FEATURE_SHAPE,
        model_type="dnn",
        layer_dim=128,
        n_blocks=1,
        seconds_per_example=2,
    )

    train_generator = infinite_batch_generator(
        x_train,
        y_train,
        batch_size=BATCH_SIZE,
    )

    validation_data = make_validation_data(
        x_val,
        y_val,
    )

    print()
    print("TRAINING...")
    print(f"Steps       : {TRAIN_STEPS}")
    print(f"Warmup      : {WARMUP_STEPS}")
    print(f"Hold        : {HOLD_STEPS}")
    print(f"Learning rate: {LEARNING_RATE}")
    print()

    classifier.train_model(
        train_generator,
        max_steps=TRAIN_STEPS,
        warmup_steps=WARMUP_STEPS,
        hold_steps=HOLD_STEPS,
        X_val=validation_data,
        false_positive_val_data=None,
        positive_test_clips=None,
        negative_weight_schedule=[1.0],
        val_steps=list(range(100, TRAIN_STEPS + 1, 100)),
        lr=LEARNING_RATE,
        val_set_hrs=1,
    )

    print()
    print("TRAINING FINISHED")

    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{executive}.onnx"

    print(f"Exporting: {output_path}")

    classifier.export_to_onnx(
        str(output_path),
        class_mapping=executive,
    )

    if not output_path.exists():
        raise RuntimeError(
            f"ONNX export reported success but file was not created: "
            f"{output_path}"
        )

    print(f"✓ CREATED: {output_path}")
    print(f"  Size: {output_path.stat().st_size:,} bytes")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Train AXIOM OS custom wake-word models"
    )

    parser.add_argument(
        "--executive",
        choices=list(EXECUTIVES.keys()) + ["all"],
        default="all",
    )

    parser.add_argument(
        "--positive-dir",
        default="data/positive",
    )

    parser.add_argument(
        "--negative-dir",
        default="data/negative",
    )

    parser.add_argument(
        "--output-dir",
        default="runtime/state/models/wakeword",
    )

    args = parser.parse_args()

    set_seed()

    positive_root = Path(args.positive_dir)
    negative_root = Path(args.negative_dir)
    output_dir = Path(args.output_dir)

    executives = (
        list(EXECUTIVES.keys())
        if args.executive == "all"
        else [args.executive]
    )

    print("=" * 70)
    print("AXIOM OS CUSTOM WAKE-WORD TRAINER")
    print("=" * 70)
    print(f"Executives : {executives}")
    print(f"Positive   : {positive_root}")
    print(f"Negative   : {negative_root}")
    print(f"Output     : {output_dir}")
    print("=" * 70)

    successful = 0

    for executive in executives:
        positive_dir = positive_root / executive
        negative_dir = negative_root / executive

        try:
            train_one(
                executive,
                positive_dir,
                negative_dir,
                output_dir,
            )
            successful += 1

        except Exception as exc:
            print()
            print(f"✗ FAILED: {executive}")
            print(f"  {type(exc).__name__}: {exc}")

            import traceback
            traceback.print_exc()

    print()
    print("=" * 70)
    print(
        f"TRAINING COMPLETE: "
        f"{successful}/{len(executives)} successful"
    )
    print("=" * 70)

    return 0 if successful == len(executives) else 1


if __name__ == "__main__":
    sys.exit(main())

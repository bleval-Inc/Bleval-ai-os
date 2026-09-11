import time

from axiom.voice.wakeword.detector import WakeWordDetector


events = []


def on_wake(executive, confidence, wake_word):
    print(
        f"WAKE DETECTED | executive={executive} "
        f"| confidence={confidence:.3f} "
        f"| wake_word={wake_word}"
    )

    events.append(
        (
            executive,
            confidence,
            wake_word,
        )
    )


def main():
    detector = WakeWordDetector(on_wake=on_wake)

    print("=" * 70)
    print("AXIOM FOUR-WAY WAKE WORD LIVE TEST")
    print("=" * 70)

    print()
    print("Loading wake-word models...")

    loaded = detector.load_models()

    print("LOAD:", loaded)
    print("MODELS:", list(detector._models.keys()))
    print("MODEL COUNT:", len(detector._models))
    print("THRESHOLD:", detector.config.confidence_threshold)

    print()
    print("Runtime decision logic:")
    print("  Winner margin: 0.05")
    print("  Cooldown:      1.0 second")

    print()
    print("Microphone configuration:")
    print("  Sample rate:   16000 Hz")
    print("  Chunk size:    1280 samples")
    print("  Audio device:  1")

    if not loaded:
        print()
        print("ERROR: No wake-word models loaded.")
        return

    print()
    print("=" * 70)
    print("LISTENING FOR 30 SECONDS")
    print("=" * 70)

    print()
    print("Say each wake word separately:")
    print()
    print("  AXIOM")
    print("  JENSON")
    print("  VALTA PRIME")
    print("  YAMAKO")
    print()
    print("Try each wake word several times.")
    print("Pause briefly between attempts.")
    print("Do NOT say multiple wake words together.")
    print()

    started = detector.start()

    print("START:", started)

    if not started:
        print()
        print("ERROR: Detector failed to start.")
        return

    print()
    print(">>> LISTENING <<<")
    print()

    try:
        time.sleep(30)

    except KeyboardInterrupt:
        print()
        print("Test interrupted by user.")

    finally:
        print()
        print("Stopping detector...")

        detector.stop()

        print("Detector stopped.")

    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)

    print()
    print("EVENTS:", len(events))

    if not events:
        print()
        print("NO WAKE WORDS DETECTED.")
        print()
        print("This means the runtime threshold/margin may be too strict,")
        print("or the microphone input was not detected during the test.")
        print()
        return

    print()

    for i, event in enumerate(events, 1):
        executive, confidence, wake_word = event

        print(
            f"{i}: "
            f"executive={executive} "
            f"confidence={confidence:.3f} "
            f"wake_word={wake_word}"
        )

    print()
    print("=" * 70)
    print("EVENT SUMMARY")
    print("=" * 70)

    counts = {
        "axiom": 0,
        "jenson": 0,
        "valta_prime": 0,
        "yamako": 0,
    }

    for executive, confidence, wake_word in events:
        if executive in counts:
            counts[executive] += 1

    print()
    print("AXIOM       :", counts["axiom"])
    print("JENSON      :", counts["jenson"])
    print("VALTA PRIME :", counts["valta_prime"])
    print("YAMAKO      :", counts["yamako"])

    print()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()

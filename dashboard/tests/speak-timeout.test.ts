import test from 'node:test';
import assert from 'node:assert/strict';
import { speak } from '../lib/voice/speak.ts';

// Browser speech synthesis can fail to fire end events in some environments.
// The speak helper should still resolve instead of leaving the boot sequence stuck.
test('speak resolves when browser voice synthesis never ends', async () => {
  const originalWindow = (globalThis as any).window;

  (globalThis as any).window = {
    speechSynthesis: {
      getVoices: () => [],
      cancel: () => {},
      speak: () => {
        // Intentionally do nothing so the end event never fires.
      },
    },
  };

  try {
    let settled = false;
    const promise = speak('Booting AXIOM OS');
    promise.then(() => {
      settled = true;
    });

    await new Promise((resolve) => setTimeout(resolve, 50));
    assert.equal(settled, false, 'speak should not resolve immediately when TTS never emits an end event');

    await promise;
    assert.equal(settled, true, 'speak should resolve even without a speech end callback');
  } finally {
    (globalThis as any).window = originalWindow;
  }
});

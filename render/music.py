"""
Lo-fi music bed for LGTM episodes.

Programmatic 4-element loop:
  - Held minor chord pad (warm, lowpassed)
  - Sub bass note on each beat root
  - Soft kick on beats 1 and 3
  - Closed hi-hat on every 8th note

Tempo defaults to 84 BPM. The chord progression is a 2-bar Cm — Ab loop —
sad-but-functional, the kind of thing that plays in a corporate elevator that
doesn't quite trust you.

No external dependencies beyond numpy.
"""

from __future__ import annotations

import numpy as np

SR = 44100
BPM = 84
BEAT_S = 60.0 / BPM            # ~0.714s per beat
BAR_S = BEAT_S * 4             # ~2.857s per bar

# 2-bar chord progression: Cm (C Eb G) → Ab (Ab C Eb)
# Voiced in ~C2-C4 range
CHORDS = [
    (130.81, 155.56, 196.00, 65.41),   # Cm: C3 Eb3 G3 + sub C2
    (103.83, 130.81, 155.56, 51.91),   # Ab/C: Ab2 C3 Eb3 + sub Ab1
]


def _iir_lowpass(x: np.ndarray, cutoff_hz: float) -> np.ndarray:
    alpha = 1.0 - np.exp(-2.0 * np.pi * cutoff_hz / SR)
    out = np.empty_like(x)
    s = 0.0
    for i in range(len(x)):
        s += alpha * (float(x[i]) - s)
        out[i] = s
    return out


def _kick(duration_s: float = 0.30) -> np.ndarray:
    """Soft 808-style kick: pitch sweep 130 → 45 Hz, exponential decay."""
    n = int(duration_s * SR)
    freq = 45.0 + 85.0 * np.exp(-np.linspace(0, 5.0, n))
    phase = np.cumsum(2.0 * np.pi * freq / SR)
    sine = np.sin(phase)
    env = np.exp(-np.linspace(0, 4.5, n))
    env[:6] = np.linspace(0, 1, 6)
    return (sine * env * 0.85).astype(np.float64)


def _hat(duration_s: float = 0.06) -> np.ndarray:
    """Closed hat: short shaped noise burst, highpassed feel via decay shape."""
    n = int(duration_s * SR)
    rng = np.random.default_rng(13)
    noise = rng.standard_normal(n)
    env = np.exp(-np.linspace(0, 24, n))
    return (noise * env * 0.32).astype(np.float64)


def _chord_pad(duration_s: float, freqs: tuple[float, ...]) -> np.ndarray:
    """Sustained chord pad: stacked detuned sines, lowpassed for warmth."""
    n = int(duration_s * SR)
    t = np.arange(n, dtype=np.float64) / SR
    pad = np.zeros(n, dtype=np.float64)
    for freq in freqs[:3]:  # only the three voiced notes, sub bass handled separately
        for det in (-0.20, 0.0, +0.25):
            pad += np.sin(2.0 * np.pi * (freq + det) * t)
    pad /= max(1, len(freqs[:3]) * 3)
    pad = _iir_lowpass(pad, cutoff_hz=520)
    # Slow tremolo
    pad *= 1.0 - 0.06 * (0.5 - 0.5 * np.cos(2.0 * np.pi * 0.5 * t))
    return pad * 0.40


def _sub_bass(duration_s: float, freq: float) -> np.ndarray:
    """Held sub-bass tone with slight tremolo."""
    n = int(duration_s * SR)
    t = np.arange(n, dtype=np.float64) / SR
    sig = np.sin(2.0 * np.pi * freq * t)
    sig *= 1.0 - 0.10 * (0.5 - 0.5 * np.cos(2.0 * np.pi * 0.7 * t))
    # Soft attack so it doesn't click
    attack_n = int(0.05 * SR)
    sig[:attack_n] *= np.linspace(0, 1, attack_n)
    return sig * 0.55


def _place(track: np.ndarray, sample: np.ndarray, start_s: float, gain: float = 1.0) -> None:
    """In-place add of `sample` into mono `track` starting at `start_s`."""
    start = int(start_s * SR)
    end = start + len(sample)
    if start >= len(track):
        return
    if end > len(track):
        sample = sample[: len(track) - start]
    track[start : start + len(sample)] += sample * gain


def generate_music_bed(duration_s: float, volume: float = 0.10) -> np.ndarray:
    """
    Return stereo float32 array of shape (n_samples, 2).

    Builds a lo-fi loop: pad + sub-bass + kick on 1/3 + hat on every 8th.
    Loops as many times as needed to cover `duration_s`.
    """
    n = int(duration_s * SR)
    track = np.zeros(n, dtype=np.float64)

    kick = _kick()
    hat = _hat()

    # Walk the timeline bar-by-bar
    t = 0.0
    chord_idx = 0
    while t < duration_s:
        chord = CHORDS[chord_idx % len(CHORDS)]
        chord_idx += 1

        # Chord pad: held for the whole bar
        pad = _chord_pad(min(BAR_S, duration_s - t), chord)
        _place(track, pad, t, gain=1.0)

        # Sub bass on the chord root for the bar
        sub = _sub_bass(min(BAR_S, duration_s - t), chord[3])
        _place(track, sub, t, gain=1.0)

        # Kick on beats 1 and 3
        for beat in (0, 2):
            _place(track, kick, t + beat * BEAT_S, gain=1.0)

        # Hat on every 8th note (8 per bar)
        for eighth in range(8):
            # Slightly quieter on downbeats for groove
            gain = 0.55 if eighth % 2 == 1 else 0.78
            _place(track, hat, t + eighth * (BEAT_S / 2), gain=gain)

        t += BAR_S

    # Normalize, then apply volume
    peak = np.max(np.abs(track))
    if peak > 1e-9:
        track /= peak

    # Fade in / fade out
    fade_in_n = min(int(0.6 * SR), n // 6)
    fade_out_n = min(int(1.5 * SR), n // 4)
    track[:fade_in_n]      *= np.linspace(0.0, 1.0, fade_in_n)
    track[n - fade_out_n:] *= np.linspace(1.0, 0.0, fade_out_n)

    mono = (track * volume).astype(np.float32)
    return np.column_stack([mono, mono])

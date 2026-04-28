"""
SFX synthesis for LGTM. Generates the sound library as WAV files.

Run once to populate assets/sfx/:
    python render/sfx.py

Design principle: everything should feel heavier and more deadpan than you'd
expect. No game-UI bleeps. No ascending pitch sweeps. No cartoon sound effects.
The comedy is in the VO; the SFX should feel like a cold, professional show.

SFX vocabulary:
    whoosh      — scene transition: filtered noise + tone sweep, downward
    thud        — heavy impact: 808-style pitched sub kick
    click       — UI tick: mechanical press, not a beep
    ding        — punchline accent: low muted thock, not a bell
    stinger     — tension/bad news: two-note minor chord hit
    pop         — air-release pop: short breath, not a pitch sweep
    typewriter  — text reveal: burst of keyboard clicks
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

SR = 44100
SFX_DIR = Path(__file__).parent.parent / "assets" / "sfx"


def _envelope(n: int, attack_s: float, decay_curve: float = 5.0) -> np.ndarray:
    """Linear attack + exponential decay."""
    a = max(1, int(attack_s * SR))
    d = max(1, n - a)
    return np.concatenate([
        np.linspace(0, 1, a),
        np.exp(-np.linspace(0, decay_curve, d)),
    ])[:n]


def _whoosh(duration: float = 0.35) -> np.ndarray:
    """
    Scene transition. Downward-sweeping filtered noise with a faint tonal layer.
    Heavier and more cinematic than a simple noise whoosh.
    """
    n = int(duration * SR)
    rng = np.random.default_rng(11)
    noise = rng.standard_normal(n)

    # IIR lowpass with rising alpha = increasingly heavy filtering (downward feel)
    out = np.zeros(n)
    alpha = np.linspace(0.06, 0.96, n)
    prev = 0.0
    for i in range(n):
        prev = alpha[i] * prev + (1.0 - alpha[i]) * noise[i]
        out[i] = prev

    # Subtle tone sweep: 520 Hz → 80 Hz
    freq = 520.0 * np.exp(-np.linspace(0, 1.8, n))
    phase = np.cumsum(2.0 * np.pi * freq / SR)
    out += 0.18 * np.sin(phase)

    out *= _envelope(n, 0.025, 3.5)
    return (out / (np.max(np.abs(out)) + 1e-9)) * 0.80


def _thud(duration: float = 0.32) -> np.ndarray:
    """
    Heavy impact. 808-style: sine pitch drops from 180 Hz to 42 Hz over the
    first 100ms, then decays. Click transient at onset for snap.
    """
    n = int(duration * SR)
    freq = 180.0 * np.exp(-np.linspace(0, 2.2, n)) + 42.0
    phase = np.cumsum(2.0 * np.pi * freq / SR)
    sine = np.sin(phase)

    # Fast attack, exponential decay
    env = np.exp(-np.linspace(0, 5.0, n))
    env[:4] = np.linspace(0, 1, 4)

    # Noise click transient at onset
    click_n = int(0.007 * SR)
    rng = np.random.default_rng(7)
    click = rng.standard_normal(click_n) * np.exp(-np.linspace(0, 12, click_n))
    sine[:click_n] += click * 0.45

    return sine * env * 0.85


def _click(duration: float = 0.05) -> np.ndarray:
    """
    Mechanical button press. Two-part: sharp noise transient + brief
    low-mid resonance. Sounds like a physical key, not a UI bleep.
    """
    n = int(duration * SR)
    rng = np.random.default_rng(3)

    # Transient: shaped noise
    t_n = int(0.006 * SR)
    transient = rng.standard_normal(t_n) * np.exp(-np.linspace(0, 14, t_n))

    # Body: 900 Hz resonance
    t = np.arange(n) / SR
    body = np.sin(2.0 * np.pi * 900 * t) * np.exp(-np.linspace(0, 20, n))

    sig = body * 0.5
    sig[:t_n] += transient * 0.7
    return sig * 0.55


def _ding(duration: float = 0.20) -> np.ndarray:
    """
    Punchline accent. Low, muted thock — like stamping a document.
    Not a bell. Short decay, no ring.
    """
    n = int(duration * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(5)

    # Low-frequency body (130 Hz + 195 Hz)
    body = (
        np.sin(2.0 * np.pi * 130 * t) * 0.7
        + np.sin(2.0 * np.pi * 195 * t) * 0.35
    )
    body *= _envelope(n, 0.002, 9.0)

    # Noise transient for the "thock" attack
    t_n = int(0.014 * SR)
    click = rng.standard_normal(t_n) * np.exp(-np.linspace(0, 10, t_n))
    body[:t_n] += click * 0.55

    return body * 0.60


def _stinger(duration: float = 0.40) -> np.ndarray:
    """
    Tension / bad news. Two-note minor chord hit (A3 + Eb4 = tritone —
    the 'devil's interval'). Sounds like a wrong answer, not a cartoon sweep.
    Slight inharmonic partial adds unease.
    """
    n = int(duration * SR)
    t = np.arange(n) / SR
    env = _envelope(n, 0.005, 4.0)

    # Tritone: A3 (220 Hz) + Eb4 (311 Hz)
    sig = (
        np.sin(2.0 * np.pi * 220.0 * t) * 0.6
        + np.sin(2.0 * np.pi * 311.0 * t) * 0.55
        + np.sin(2.0 * np.pi * 185.0 * t) * 0.20  # inharmonic low partial
    )
    sig *= env
    return sig * 0.50


def _pop(duration: float = 0.08) -> np.ndarray:
    """
    Air-release pop. Short shaped noise burst — like a small bubble or a
    breath. No pitch sweep, no game-UI sound.
    """
    n = int(duration * SR)
    rng = np.random.default_rng(9)
    noise = rng.standard_normal(n)
    env = np.exp(-np.linspace(0, 14, n))
    env[:3] = np.linspace(0, 1, 3)
    sig = noise * env

    # Lowpass to muffle the pop (air-like, not crispy)
    out = np.zeros(n)
    alpha = 1.0 - np.exp(-2.0 * np.pi * 380 / SR)
    s = 0.0
    for i in range(n):
        s += alpha * (sig[i] - s)
        out[i] = s

    peak = np.max(np.abs(out))
    if peak > 1e-9:
        out /= peak
    return out * 0.60


def _typewriter(duration: float = 0.55) -> np.ndarray:
    """
    Text reveal: burst of keyboard clicks with natural timing variation.
    Each click uses the _click() synthesis for physical key feel.
    """
    n = int(duration * SR)
    out = np.zeros(n)
    t = 0.0
    rng = np.random.default_rng(42)

    while t < duration - 0.05:
        key = _click(0.030)
        start = int(t * SR)
        end = min(start + len(key), n)
        vol = 0.55 + 0.45 * rng.random()
        out[start:end] += key[:end - start] * vol
        # Slightly irregular timing (35–65 ms between keystrokes)
        t += 0.035 + 0.030 * rng.random()

    return out * 0.90


def _write_wav(path: Path, samples: np.ndarray) -> None:
    samples = np.clip(samples, -1.0, 1.0)
    pcm = (samples * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


GENERATORS: dict[str, object] = {
    "whoosh":     _whoosh,
    "thud":       _thud,
    "click":      _click,
    "ding":       _ding,
    "stinger":    _stinger,
    "pop":        _pop,
    "typewriter": _typewriter,
}


def generate_all(out_dir: Path = SFX_DIR) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, gen in GENERATORS.items():
        samples = gen()
        path = out_dir / f"{name}.wav"
        _write_wav(path, samples)
        print(f"  {name}.wav  {len(samples) / SR:.3f}s  peak={np.max(np.abs(samples)):.3f}")


def load_sfx(name: str) -> np.ndarray:
    """Load an SFX by name. Returns mono float32 array at SR."""
    path = SFX_DIR / f"{name}.wav"
    if not path.exists():
        raise FileNotFoundError(f"SFX not found: {name} (expected {path})")
    with wave.open(str(path), "rb") as w:
        frames = w.readframes(w.getnframes())
        pcm = np.frombuffer(frames, dtype=np.int16)
    return pcm.astype(np.float32) / 32767.0


if __name__ == "__main__":
    print(f"Generating SFX library -> {SFX_DIR}")
    generate_all()
    print("Done.")

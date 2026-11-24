"""
RESONA Audio Synthesizer
Generates programmatic acoustic earcons, multi-tone chords, and microtonal depth cues
as standard 16-bit PCM WAV buffers using accelerated NumPy array processing.
"""

from __future__ import annotations
import math
import struct
import io
import wave
from typing import List, Tuple, Dict, Any, Optional

try:
    import numpy as np
    HAVE_NUMPY = True
except ImportError:
    HAVE_NUMPY = False


class AudioSynthesizer:
    """Synthesizes high-fidelity earcons and sonification audio."""

    SAMPLE_RATE = 44100

    @classmethod
    def generate_tone(cls, frequency: float, duration_ms: float, volume: float = 0.5, shape: str = "sine") -> bytes:
        """Generate a single-tone WAV buffer with an ADSR envelope."""
        n_samples = int(cls.SAMPLE_RATE * (duration_ms / 1000.0))
        if n_samples <= 0:
            n_samples = 1

        if HAVE_NUMPY:
            t = np.linspace(0, duration_ms / 1000.0, n_samples, endpoint=False)
            if shape == "triangle":
                val = 2.0 * np.abs(2.0 * (t * frequency - np.floor(t * frequency + 0.5))) - 1.0
            elif shape == "square":
                val = np.sign(np.sin(2.0 * np.pi * frequency * t))
            else:
                val = np.sin(2.0 * np.pi * frequency * t)

            # Fast linear envelope
            attack_len = min(int(cls.SAMPLE_RATE * 0.01), n_samples // 4)
            release_len = min(int(cls.SAMPLE_RATE * 0.02), n_samples // 4)
            env = np.ones(n_samples, dtype=np.float32)
            if attack_len > 0:
                env[:attack_len] = np.linspace(0, 1, attack_len)
            if release_len > 0:
                env[-release_len:] = np.linspace(1, 0, release_len)

            samples = (val * env * volume * 32767.0).clip(-32768, 32767).astype(np.int16)
            raw_frames = samples.tobytes()
        else:
            buffer = io.BytesIO()
            attack_len = min(int(cls.SAMPLE_RATE * 0.01), n_samples // 4)
            release_len = min(int(cls.SAMPLE_RATE * 0.02), n_samples // 4)
            decay_start = n_samples - release_len
            raw_samples = bytearray()
            for i in range(n_samples):
                env = (i / attack_len) if i < attack_len else ((n_samples - i) / release_len if i > decay_start else 1.0)
                t = i / cls.SAMPLE_RATE
                val = math.sin(2.0 * math.pi * frequency * t)
                sample_val = int(val * env * volume * 32767.0)
                raw_samples.extend(struct.pack("<h", max(-32768, min(32767, sample_val))))
            raw_frames = bytes(raw_samples)

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(cls.SAMPLE_RATE)
            wf.writeframes(raw_frames)

        return buffer.getvalue()

    @classmethod
    def generate_chord(cls, frequencies: List[float], duration_ms: float, volume: float = 0.5) -> bytes:
        """Generate a polyphonic multi-frequency chord."""
        n_samples = int(cls.SAMPLE_RATE * (duration_ms / 1000.0))
        if n_samples <= 0:
            n_samples = 1

        if HAVE_NUMPY and frequencies:
            t = np.linspace(0, duration_ms / 1000.0, n_samples, endpoint=False)
            val = np.zeros(n_samples, dtype=np.float32)
            for f in frequencies:
                val += np.sin(2.0 * np.pi * f * t)
            val /= max(len(frequencies), 1)

            attack_len = min(int(cls.SAMPLE_RATE * 0.015), n_samples // 4)
            release_len = min(int(cls.SAMPLE_RATE * 0.03), n_samples // 3)
            env = np.ones(n_samples, dtype=np.float32)
            if attack_len > 0:
                env[:attack_len] = np.linspace(0, 1, attack_len)
            if release_len > 0:
                env[-release_len:] = np.linspace(1, 0, release_len)

            samples = (val * env * volume * 32767.0).clip(-32768, 32767).astype(np.int16)
            raw_frames = samples.tobytes()
        else:
            raw_frames = cls.generate_tone(frequencies[0] if frequencies else 440.0, duration_ms, volume)[44:]

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(cls.SAMPLE_RATE)
            wf.writeframes(raw_frames)

        return buffer.getvalue()

    @classmethod
    def generate_arpeggio(cls, notes: List[Tuple[float, float]], gap_ms: float = 10.0, volume: float = 0.5) -> bytes:
        """Generate an arpeggio sequence."""
        raw_frames = bytearray()
        for freq, dur in notes:
            tone_wav = cls.generate_tone(freq, dur, volume=volume, shape="sine")
            raw_frames.extend(tone_wav[44:])
            gap_samples = int(cls.SAMPLE_RATE * (gap_ms / 1000.0))
            raw_frames.extend(b"\x00\x00" * gap_samples)

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(cls.SAMPLE_RATE)
            wf.writeframes(raw_frames)

        return buffer.getvalue()

    @classmethod
    def get_earcon_library(cls) -> Dict[str, bytes]:
        """Pre-generate standard accessible earcons."""
        earcons = {}

        # 1. Indentation levels (C-major pentatonic scale)
        indent_pitches = [261.63, 293.66, 329.63, 392.00, 440.00, 523.25, 587.33, 659.25]
        for depth, freq in enumerate(indent_pitches):
            earcons[f"indent_level_{depth}"] = cls.generate_tone(freq, 70.0, volume=0.35)

        # 2. Function Entry: Ascending major triad
        earcons["function_entry"] = cls.generate_arpeggio([
            (261.63, 50.0), (329.63, 50.0), (392.00, 90.0)
        ], gap_ms=5.0, volume=0.45)

        # 3. Class Entry: Noble brass fourth interval
        earcons["class_entry"] = cls.generate_arpeggio([
            (293.66, 60.0), (392.00, 60.0), (587.33, 100.0)
        ], gap_ms=5.0, volume=0.45)

        # 4. Loop Iteration: Percussive double tap
        earcons["loop_iteration"] = cls.generate_arpeggio([
            (440.0, 35.0), (440.0, 45.0)
        ], gap_ms=15.0, volume=0.4)

        # 5. Branch True: High crisp ding
        earcons["branch_true"] = cls.generate_tone(987.77, 80.0, volume=0.4, shape="triangle")

        # 6. Branch False: Subdued blip
        earcons["branch_false"] = cls.generate_tone(349.23, 70.0, volume=0.35, shape="sine")

        # 7. Variable Change: Subtle bell ping
        earcons["variable_change"] = cls.generate_tone(783.99, 50.0, volume=0.3)

        # 8. Return Statement: Descending cadence
        earcons["function_return"] = cls.generate_arpeggio([
            (392.00, 60.0), (329.63, 60.0), (261.63, 100.0)
        ], gap_ms=5.0, volume=0.4)

        # 9. Exception: Dissonant tritone chord
        earcons["runtime_error"] = cls.generate_chord([130.81, 261.63, 369.99], 320.0, volume=0.6)

        # 10. Breakpoint Hit
        earcons["breakpoint_hit"] = cls.generate_chord([659.25, 987.77], 200.0, volume=0.5)

        # 11. Execution Success
        earcons["execution_success"] = cls.generate_chord([261.63, 329.63, 392.00, 523.25], 350.0, volume=0.45)

        # 12. Cursor Step Tick
        earcons["step_tick"] = cls.generate_tone(1200.0, 15.0, volume=0.2, shape="sine")

        return earcons

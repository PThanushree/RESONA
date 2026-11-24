"""
Unit tests for Audio Synthesizer & Sonification Engine
"""

import wave
import io
from resona.core.audio_synthesizer import AudioSynthesizer
from resona.core.sonification_engine import SonificationEngine
from resona.core.ast_analyzer import ASTAnalyzer
from resona.core.runtime_debugger import RuntimeDebugger


def test_tone_wav_generation():
    wav_bytes = AudioSynthesizer.generate_tone(440.0, 100.0, volume=0.5)
    assert len(wav_bytes) > 44  # Has WAV header

    # Verify standard valid RIFF header
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getframerate() == 44100
        assert wf.getnframes() > 0


def test_earcon_library_integrity():
    lib = AudioSynthesizer.get_earcon_library()
    expected_keys = [
        "function_entry", "class_entry", "loop_iteration",
        "branch_true", "branch_false", "variable_change",
        "runtime_error", "execution_success"
    ]
    for key in expected_keys:
        assert key in lib
        assert len(lib[key]) > 44


def test_depth_frequency_scale():
    engine = SonificationEngine()
    freq0 = engine.get_frequency_for_depth(0)
    freq1 = engine.get_frequency_for_depth(1)
    freq2 = engine.get_frequency_for_depth(2)

    # Fundamental pitch must increase monotonically with depth
    assert freq0 < freq1 < freq2

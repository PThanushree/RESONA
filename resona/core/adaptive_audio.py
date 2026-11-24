"""
RESONA Adaptive Audio Feedback Settings Module
Fulfills Objective 6 & Deliverable 7 of KSCST Proposal:
'Adaptive audio feedback settings that allow users to control the level of spoken explanations and audio cues.'
"""

from __future__ import annotations
import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class AdaptiveAudioSettings:
    """Configurable accessibility settings for earcon sonification and speech synthesis."""
    verbosity_level: str = "standard"  # 'verbose', 'standard', 'minimal', 'silent'
    feedback_mode: str = "hybrid"      # 'hybrid', 'sonification_only', 'speech_only'
    earcon_volume: float = 0.5         # 0.0 to 1.0
    speech_volume: float = 0.8         # 0.0 to 1.0
    speech_rate: float = 1.15          # 0.5 to 2.5
    speech_pitch: float = 1.0          # 0.5 to 1.5
    indentation_audio: bool = True     # Play pitch scale on line cursor move
    stereo_panning: bool = True        # Pan soundscape left-to-right across headphones
    variable_chimes: bool = True       # Audio chime on variable mutation
    soundscape_pace_ms: int = 180      # Playback pacing in milliseconds

    def should_play_earcon(self, event_type: str) -> bool:
        """Determine if an acoustic cue should play under active settings."""
        if self.feedback_mode == "speech_only":
            return False
        if self.earcon_volume <= 0.01:
            return False
        return True

    def should_speak(self, priority: str = "normal") -> bool:
        """Determine if speech synthesis should speak under active settings."""
        if self.feedback_mode == "sonification_only":
            return False
        if self.verbosity_level == "silent":
            return False
        if self.verbosity_level == "minimal" and priority != "assertive":
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AdaptiveAudioSettings:
        valid_keys = set(cls.__annotations__.keys())
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


class AdaptiveAudioManager:
    """Manages adaptive audio profiles and persistence."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.join(os.path.dirname(os.path.dirname(__file__)), "audio_settings.json")
        self.settings = self.load()

    def load(self) -> AdaptiveAudioSettings:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return AdaptiveAudioSettings.from_dict(data)
            except Exception:
                pass
        return AdaptiveAudioSettings()

    def save(self, new_settings: AdaptiveAudioSettings):
        self.settings = new_settings
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(asdict(new_settings), f, indent=2)
        except Exception:
            pass

    def apply_preset(self, preset_name: str) -> AdaptiveAudioSettings:
        """Apply pre-configured accessibility profiles."""
        if preset_name == "beginner":
            self.settings = AdaptiveAudioSettings(
                verbosity_level="verbose",
                feedback_mode="hybrid",
                speech_rate=1.0,
                soundscape_pace_ms=250
            )
        elif preset_name == "expert":
            self.settings = AdaptiveAudioSettings(
                verbosity_level="minimal",
                feedback_mode="hybrid",
                speech_rate=1.6,
                soundscape_pace_ms=80
            )
        elif preset_name == "sonification_only":
            self.settings = AdaptiveAudioSettings(
                verbosity_level="silent",
                feedback_mode="sonification_only",
                earcon_volume=0.8
            )
        elif preset_name == "speech_only":
            self.settings = AdaptiveAudioSettings(
                verbosity_level="verbose",
                feedback_mode="speech_only",
                speech_rate=1.3
            )
        else:  # standard
            self.settings = AdaptiveAudioSettings()
        
        self.save(self.settings)
        return self.settings

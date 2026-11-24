/**
 * RESONA Web Audio Synthesizer
 * Zero-latency browser-side audio sonification using Web Audio API.
 * Provides microtonal pitch scaling for code nesting depth and rich auditory earcons.
 */

class ResonaAudioSynthesizer {
  constructor() {
    this.audioCtx = null;
    this.masterGain = null;
    this.muted = false;
    this.volume = 0.5;
    
    // Pentatonic depth scale (Hz)
    this.depthFrequencies = [
      261.63, // Depth 0: C4
      293.66, // Depth 1: D4
      329.63, // Depth 2: E4
      392.00, // Depth 3: G4
      440.00, // Depth 4: A4
      523.25, // Depth 5: C5
      587.33, // Depth 6: D5
      659.25  // Depth 7+: E5
    ];
  }

  init() {
    if (!this.audioCtx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      this.audioCtx = new AudioContext();
      this.masterGain = this.audioCtx.createGain();
      this.masterGain.gain.setValueAtTime(this.volume, this.audioCtx.currentTime);
      this.masterGain.connect(this.audioCtx.destination);
    }
    if (this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
  }

  setVolume(val) {
    this.volume = Math.max(0, Math.min(1, val));
    if (this.masterGain && !this.muted) {
      this.masterGain.gain.setValueAtTime(this.volume, this.audioCtx.currentTime);
    }
  }

  toggleMute() {
    this.muted = !this.muted;
    if (this.masterGain) {
      this.masterGain.gain.setValueAtTime(this.muted ? 0 : this.volume, this.audioCtx.currentTime);
    }
    return this.muted;
  }

  _createPanner(panValue = 0) {
    if (!this.audioCtx) this.init();
    panValue = Math.max(-1, Math.min(1, panValue));
    
    if (this.audioCtx.createStereoPanner) {
      const panner = this.audioCtx.createStereoPanner();
      panner.pan.setValueAtTime(panValue, this.audioCtx.currentTime);
      panner.connect(this.masterGain);
      return panner;
    }
    // Fallback if StereoPanner is unavailable
    return this.masterGain;
  }

  /**
   * Play a clean sine tone with an exponential ADSR envelope.
   */
  playTone(frequency, durationMs = 80, pan = 0, type = 'sine', gainScale = 1.0) {
    if (this.muted) return;
    this.init();

    const osc = this.audioCtx.createOscillator();
    const gainNode = this.audioCtx.createGain();
    const panner = this._createPanner(pan);

    osc.type = type;
    osc.frequency.setValueAtTime(frequency, this.audioCtx.currentTime);

    const startTime = this.audioCtx.currentTime;
    const duration = durationMs / 1000.0;
    const peakGain = 0.4 * gainScale;

    gainNode.gain.setValueAtTime(0.0001, startTime);
    gainNode.gain.exponentialRampToValueAtTime(peakGain, startTime + 0.01);
    gainNode.gain.exponentialRampToValueAtTime(0.0001, startTime + duration);

    osc.connect(gainNode);
    gainNode.connect(panner);

    osc.start(startTime);
    osc.stop(startTime + duration + 0.05);
  }

  /**
   * Play audio cue indicating code nesting depth.
   */
  playDepthTone(depth = 0, pan = 0) {
    const idx = Math.max(0, Math.min(depth, this.depthFrequencies.length - 1));
    const freq = this.depthFrequencies[idx];
    this.playTone(freq, 70, pan, 'sine', 0.8);
  }

  /**
   * Play polyphonic multi-frequency chord.
   */
  playChord(frequencies, durationMs = 250, pan = 0, gainScale = 0.8) {
    if (this.muted) return;
    this.init();

    const panner = this._createPanner(pan);
    const startTime = this.audioCtx.currentTime;
    const duration = durationMs / 1000.0;
    const perOscGain = (0.35 * gainScale) / Math.max(frequencies.length, 1);

    frequencies.forEach(freq => {
      const osc = this.audioCtx.createOscillator();
      const gainNode = this.audioCtx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, startTime);

      gainNode.gain.setValueAtTime(0.0001, startTime);
      gainNode.gain.exponentialRampToValueAtTime(perOscGain, startTime + 0.015);
      gainNode.gain.exponentialRampToValueAtTime(0.0001, startTime + duration);

      osc.connect(gainNode);
      gainNode.connect(panner);

      osc.start(startTime);
      osc.stop(startTime + duration + 0.05);
    });
  }

  /**
   * Play sequential arpeggio (earcon melody).
   */
  playArpeggio(notes, gapMs = 15, pan = 0) {
    if (this.muted) return;
    this.init();

    let currentTimeMs = 0;
    notes.forEach(([freq, dur, type = 'sine']) => {
      setTimeout(() => {
        this.playTone(freq, dur, pan, type, 0.9);
      }, currentTimeMs);
      currentTimeMs += dur + gapMs;
    });
  }

  /**
   * Play standard semantic earcons by identifier.
   */
  playEarcon(earconId, pan = 0) {
    this.init();

    switch (earconId) {
      case 'function_entry':
        // Ascending major triad: C4 -> E4 -> G4
        this.playArpeggio([[261.63, 45], [329.63, 45], [392.00, 80]], 8, pan);
        break;

      case 'class_entry':
        // Regal fourths: D4 -> G4 -> D5
        this.playArpeggio([[293.66, 50], [392.00, 50], [587.33, 90]], 8, pan);
        break;

      case 'loop_iteration':
        // Percussive woodblock double tap
        this.playArpeggio([[440.0, 30, 'triangle'], [440.0, 35, 'triangle']], 15, pan);
        break;

      case 'branch_true':
        // High crystalline chime
        this.playTone(987.77, 75, pan, 'triangle', 1.0);
        break;

      case 'branch_false':
        // Lower subdued blip
        this.playTone(349.23, 65, pan, 'sine', 0.8);
        break;

      case 'variable_change':
        // Gentle water drop ping (G5)
        this.playTone(783.99, 45, pan, 'sine', 0.85);
        break;

      case 'function_return':
        // Descending cadence: G4 -> E4 -> C4
        this.playArpeggio([[392.00, 50], [329.63, 50], [261.63, 80]], 8, pan);
        break;

      case 'runtime_error':
        // Dissonant tritone alarm (C3 + C4 + F#4)
        this.playChord([130.81, 261.63, 369.99], 350, pan, 1.3);
        break;

      case 'breakpoint_hit':
        // Crystal bell dual harmonic (E5 + B5)
        this.playChord([659.25, 987.77], 220, pan, 1.1);
        break;

      case 'execution_success':
        // Sparkling major completion chord (C4, E4, G4, C5)
        this.playChord([261.63, 329.63, 392.00, 523.25], 380, pan, 1.0);
        break;

      case 'step_tick':
        this.playTone(1200.0, 15, pan, 'sine', 0.4);
        break;

      default:
        if (earconId.startsWith('indent_level_')) {
          const depth = parseInt(earconId.replace('indent_level_', ''), 10) || 0;
          this.playDepthTone(depth, pan);
        } else {
          this.playTone(440, 60, pan);
        }
        break;
    }
  }
}

// Global instance
window.resonaAudio = new ResonaAudioSynthesizer();

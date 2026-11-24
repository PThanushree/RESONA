/**
 * RESONA Speech Narrator & ARIA Announcer
 * Manages text-to-speech audio narration and live screen reader regions.
 */

class ResonaSpeechNarrator {
  constructor() {
    this.synth = window.speechSynthesis;
    this.speaking = false;
    this.rate = 1.15; // Natural conversational rate
    this.pitch = 1.0;
    this.voice = null;
    this.politeRegion = null;
    this.assertiveRegion = null;

    this._initRegions();
    this._initVoices();
  }

  _initRegions() {
    this.politeRegion = document.getElementById('aria-live-polite');
    this.assertiveRegion = document.getElementById('aria-live-assertive');
  }

  _initVoices() {
    if (!this.synth) return;
    const loadVoices = () => {
      const voices = this.synth.getVoices();
      // Prefer clear natural English voices
      this.voice = voices.find(v => v.lang.startsWith('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('David') || v.name.includes('Zira'))) || voices[0];
    };
    loadVoices();
    if (this.synth.onvoiceschanged !== undefined) {
      this.synth.onvoiceschanged = loadVoices;
    }
  }

  setRate(rateVal) {
    this.rate = Math.max(0.5, Math.min(2.5, rateVal));
  }

  stop() {
    if (this.synth) {
      this.synth.cancel();
      this.speaking = false;
    }
  }

  announce(text, priority = 'polite') {
    // 1. Update DOM ARIA Live Region for screen readers (NVDA/JAWS)
    const targetRegion = priority === 'assertive' ? this.assertiveRegion : this.politeRegion;
    if (targetRegion) {
      targetRegion.textContent = '';
      setTimeout(() => {
        targetRegion.textContent = text;
      }, 50);
    }
  }

  speak(text, priority = 'polite', interrupt = true) {
    if (!text) return;
    this.announce(text, priority);

    if (!this.synth) return;

    if (interrupt) {
      this.synth.cancel();
    }

    const utterance = new SpeechSynthesisUtterance(text);
    if (this.voice) utterance.voice = this.voice;
    utterance.rate = this.rate;
    utterance.pitch = this.pitch;

    utterance.onstart = () => {
      this.speaking = true;
    };
    utterance.onend = () => {
      this.speaking = false;
    };
    utterance.onerror = () => {
      this.speaking = false;
    };

    this.synth.speak(utterance);
  }
}

window.resonaSpeech = new ResonaSpeechNarrator();

/**
 * RESONA Master Application Controller (Ultra-Fast Single-Pass Pipeline)
 * Coordinates AST analysis, variable scopes, runtime debugging, audio sonification,
 * contextual AI Q&A, and adaptive audio settings (WCAG 2.2 AAA).
 */

class ResonaApp {
  constructor() {
    this.editor = null;
    this.currentAnalysis = null;
    this.currentTrace = null;
    this.currentSettings = null;
    this.currentThemeIndex = 0;
    this.themes = ['theme-dark', 'theme-yellow-black', 'theme-light-contrast', 'theme-blue-yellow'];
    this.themeLabels = ['Dark High Contrast', 'Yellow on Black (High Acuity)', 'Light Contrast', 'Blue on Yellow (Low Glare)'];
    this.breakpoints = new Set();
    this.lastProcessedCode = null;
  }

  async init() {
    this.editor = document.getElementById('code-editor');

    // Initialize sub-controllers
    window.resonaAST.init('ast-tree-view', (node, jumpToEditor) => {
      this.highlightEditorLine(node.start_line);
      if (jumpToEditor) {
        this.setEditorCursorToLine(node.start_line);
      }
    });

    window.resonaDebugger.init((event) => {
      this.highlightEditorLine(event.line_number);
    });

    this._bindGlobalKeybindings();
    this._bindHeaderButtons();
    this._bindTabs();
    this._bindExampleSelector();
    this._bindAIAssistant();
    this._bindAudioSettings();

    // Initial run with default code
    await this.analyzeAndRun();
    await this.fetchSettings();
  }

  async fetchSettings() {
    try {
      const res = await fetch('/api/settings');
      this.currentSettings = await res.json();
      this.applySettingsToAudio(this.currentSettings);
    } catch (e) {}
  }

  applySettingsToAudio(settings) {
    if (!settings) return;
    this.currentSettings = settings;
    if (window.resonaAudio) {
      window.resonaAudio.setVolume(settings.earcon_volume || 0.5);
    }
    if (window.resonaSpeech) {
      window.resonaSpeech.setRate(settings.speech_rate || 1.15);
    }
  }

  async analyzeAndRun() {
    const code = this.editor.value;
    if (!code.trim()) return;

    try {
      const res = await fetch('/api/pipeline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          code, 
          breakpoints: Array.from(this.breakpoints),
          active_line: this.getCurrentLineNumber()
        })
      });
      const data = await res.json();
      this.currentAnalysis = data.analysis;
      this.currentTrace = data.trace;

      // Update AST Tree
      window.resonaAST.setTree(data.analysis);

      // Render Variable Scopes (Objective 2 / Phase 3)
      this.renderScopes(data.analysis.variable_scopes || []);

      // Update Debugger & Soundscape
      if (data.trace) {
        window.resonaDebugger.loadTrace(data.trace);
      }

      // Render AI Narration
      this.renderNarrative(data.narration);

      // Status bar updates
      const isSuccess = data.trace ? data.trace.success : false;
      const statusText = isSuccess
        ? `Status: Success (${data.trace.total_steps} steps in ${data.trace.execution_time_seconds}s)`
        : (data.trace 
            ? `Status: Error - ${data.trace.error_type} at line ${data.trace.error_line}`
            : `Status: Syntax Error at line ${data.analysis.syntax_error?.line || 1}`);
      
      const statusEl = document.getElementById('footer-status-text');
      if (statusEl) statusEl.textContent = statusText;

      if (!isSuccess && data.trace) {
        if (window.resonaAudio) window.resonaAudio.playEarcon('runtime_error');
        if (window.resonaSpeech) {
          window.resonaSpeech.announce(`Execution failed with ${data.trace.error_type} at line ${data.trace.error_line}. Press Alt+A to hear diagnosis.`, 'assertive');
        }
      } else if (data.analysis.is_valid) {
        if (window.resonaSpeech) {
          window.resonaSpeech.announce(`Ready. ${data.analysis.total_functions} functions, ${data.analysis.total_loops} loops.`);
        }
      }

    } catch (err) {
      console.error("Execution error:", err);
      if (window.resonaSpeech) {
        window.resonaSpeech.announce("Error connecting to RESONA backend server.", "assertive");
      }
    }
  }

  renderScopes(scopes) {
    const container = document.getElementById('scopes-container');
    if (!container) return;
    container.innerHTML = '';

    if (!scopes || scopes.length === 0) {
      container.innerHTML = '<div style="opacity:0.7;font-style:italic;">No variable scopes extracted.</div>';
      return;
    }

    scopes.forEach(sc => {
      const card = document.createElement('div');
      card.className = 'ai-narrative-card';
      card.style.padding = '8px 12px';
      card.style.fontSize = '0.85rem';

      let shadowBadge = '';
      if (sc.shadowed_variables && sc.shadowed_variables.length > 0) {
        shadowBadge = `<div style="color:var(--warning-color);margin-top:4px;"><strong>Shadowed outer vars:</strong> ${sc.shadowed_variables.join(', ')}</div>`;
      }

      card.innerHTML = `
        <div style="font-weight:700;display:flex;justify-content:space-between;border-bottom:1px solid var(--border-color);padding-bottom:4px;margin-bottom:6px;">
          <span>${sc.scope_type.toUpperCase()}: ${sc.name}</span>
          <span style="opacity:0.7;font-size:0.75rem;">Lines ${sc.start_line}-${sc.end_line}</span>
        </div>
        <div><strong>Defined Variables:</strong> ${sc.variables_defined.length ? sc.variables_defined.join(', ') : 'None'}</div>
        <div><strong>Parameters:</strong> ${sc.parameters.length ? sc.parameters.join(', ') : 'None'}</div>
        ${shadowBadge}
      `;
      container.appendChild(card);
    });
  }

  renderNarrative(data) {
    const cardEl = document.getElementById('ai-narrative-display');
    if (!cardEl) return;

    const isSuccess = data.runtime ? data.runtime.status !== 'error' : true;
    cardEl.className = `ai-narrative-card ${isSuccess ? 'success-border' : 'error-border'}`;

    let html = `
      <div class="ai-narrative-title" role="heading" aria-level="3">
        ${data.structure.headline}
      </div>
      <div class="ai-narrative-body">
        ${data.structure.narrative}
      </div>
    `;

    if (data.runtime) {
      html += `
        <div style="margin-top:12px;padding-top:8px;border-top:1px solid var(--border-color);">
          <strong>Runtime Narrative:</strong> ${data.runtime.narrative}
        </div>
      `;
      if (data.runtime.fix_recommendation) {
        html += `
          <div class="ai-fix-box">
            <strong>Recommended Fix:</strong> ${data.runtime.fix_recommendation}
          </div>
        `;
      }
    }

    html += `
      <div style="margin-top:12px;display:flex;gap:8px;">
        <button id="btn-speak-narrative" class="btn btn-primary" aria-label="Speak AI Narration aloud">
          &#128266; Speak Narration (Alt+A)
        </button>
      </div>
    `;

    cardEl.innerHTML = html;

    const speakBtn = document.getElementById('btn-speak-narrative');
    if (speakBtn) {
      speakBtn.addEventListener('click', () => {
        const fullText = `${data.structure.narrative} ${data.runtime?.narrative || ''} ${data.runtime?.fix_recommendation || ''}`;
        if (window.resonaSpeech) {
          window.resonaSpeech.speak(fullText, 'assertive');
        }
      });
    }
  }

  getCurrentLineNumber() {
    if (!this.editor) return 1;
    const text = this.editor.value;
    const cursorPos = this.editor.selectionStart;
    return text.substring(0, cursorPos).split('\n').length;
  }

  highlightEditorLine(lineNum) {
    const lineDisplay = document.getElementById('footer-cursor-line');
    if (lineDisplay) lineDisplay.textContent = `Line: ${lineNum}`;
  }

  setEditorCursorToLine(lineNum) {
    if (!this.editor) return;
    const text = this.editor.value;
    const lines = text.split('\n');
    let charOffset = 0;
    for (let i = 0; i < lineNum - 1 && i < lines.length; i++) {
      charOffset += lines[i].length + 1;
    }
    this.editor.focus();
    this.editor.setSelectionRange(charOffset, charOffset + (lines[lineNum - 1]?.length || 0));
  }

  cycleTheme() {
    this.currentThemeIndex = (this.currentThemeIndex + 1) % this.themes.length;
    document.body.className = this.themes[this.currentThemeIndex];
    const themeName = this.themeLabels[this.currentThemeIndex];
    if (window.resonaSpeech) {
      window.resonaSpeech.announce(`Theme changed to ${themeName}`);
    }
  }

  announceOutline() {
    if (!this.currentAnalysis || !this.currentAnalysis.is_valid) {
      if (window.resonaSpeech) window.resonaSpeech.announce("No valid code outline available.");
      return;
    }
    const landmarks = this.currentAnalysis.audio_landmarks || [];
    if (landmarks.length === 0) {
      if (window.resonaSpeech) window.resonaSpeech.announce("The file has no functions, classes, or loops.");
      return;
    }
    const summary = landmarks.map(lm => lm.spoken).join(". ");
    if (window.resonaSpeech) {
      window.resonaSpeech.speak(`Structural Code Outline: ${summary}`);
    }
  }

  announceHelp() {
    const helpMsg = "RESONA Keyboard Shortcuts: " +
      "Press F5 to Run code and sonify. " +
      "Press F6 to switch focus between editor and panels. " +
      "Press F10 to Step Next in debugger. " +
      "Press Shift plus F10 to Step Back. " +
      "Press Control Shift P to Play continuous audio soundscape. " +
      "Press Alt O to hear structural code outline. " +
      "Press Alt A to hear AI narration and bug diagnosis. " +
      "Press Alt S to open Adaptive Audio Settings. " +
      "Press Alt T to cycle high contrast accessibility themes. " +
      "Press Escape to cancel speech audio.";
    if (window.resonaSpeech) {
      window.resonaSpeech.speak(helpMsg, 'assertive');
    }
  }

  _bindAIAssistant() {
    const input = document.getElementById('ai-question-input');
    const btn = document.getElementById('btn-submit-ai-question');
    const answerBox = document.getElementById('ai-answer-box');

    const handleAsk = async () => {
      const q = input.value.trim();
      if (!q) return;

      answerBox.style.display = 'block';
      answerBox.innerHTML = '<em>Consulting RESONA AI Assistant...</em>';

      try {
        const res = await fetch('/api/ask_ai', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            question: q,
            code: this.editor.value,
            line: this.getCurrentLineNumber()
          })
        });
        const data = await res.json();
        answerBox.innerHTML = `<strong>${data.source}:</strong> ${data.answer}`;
        if (window.resonaSpeech) {
          window.resonaSpeech.speak(data.spoken, 'assertive');
        }
      } catch (err) {
        answerBox.textContent = 'Error connecting to AI service.';
      }
    };

    if (btn) btn.addEventListener('click', handleAsk);
    if (input) {
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          handleAsk();
        }
      });
    }
  }

  _bindAudioSettings() {
    const modal = document.getElementById('modal-settings');
    const openBtn = document.getElementById('btn-audio-settings');
    const closeBtn = document.getElementById('btn-close-settings');
    const saveBtn = document.getElementById('btn-save-settings');

    const openModal = () => {
      modal.style.display = 'flex';
      modal.classList.remove('sr-only');
      closeBtn.focus();
      if (window.resonaSpeech) window.resonaSpeech.announce("Adaptive audio settings dialog opened.");
    };

    const closeModal = () => {
      modal.style.display = 'none';
      modal.classList.add('sr-only');
      if (this.editor) this.editor.focus();
    };

    if (openBtn) openBtn.addEventListener('click', openModal);
    if (closeBtn) closeBtn.addEventListener('click', closeModal);

    if (saveBtn) {
      saveBtn.addEventListener('click', async () => {
        const verbosity = document.getElementById('set-verbosity').value;
        const mode = document.getElementById('set-mode').value;
        const earconVol = parseInt(document.getElementById('set-earcon-vol').value, 10) / 100.0;
        const speechRate = parseInt(document.getElementById('set-speech-rate').value, 10) / 100.0;
        const indentAudio = document.getElementById('chk-indent-audio').checked;
        const stereoPan = document.getElementById('chk-stereo-pan').checked;
        const varChimes = document.getElementById('chk-var-chimes').checked;

        const payload = {
          verbosity_level: verbosity,
          feedback_mode: mode,
          earcon_volume: earconVol,
          speech_rate: speechRate,
          indentation_audio: indentAudio,
          stereo_panning: stereoPan,
          variable_chimes: varChimes
        };

        const res = await fetch('/api/settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const saved = await res.json();
        this.applySettingsToAudio(saved);
        closeModal();
        if (window.resonaSpeech) window.resonaSpeech.speak("Adaptive audio settings saved.");
      });
    }

    // Sliders readouts
    const earconSlider = document.getElementById('set-earcon-vol');
    if (earconSlider) {
      earconSlider.addEventListener('input', (e) => {
        document.getElementById('lbl-earcon-vol').textContent = `${e.target.value}%`;
      });
    }
    const speechSlider = document.getElementById('set-speech-rate');
    if (speechSlider) {
      speechSlider.addEventListener('input', (e) => {
        document.getElementById('lbl-speech-rate').textContent = `${(e.target.value / 100.0).toFixed(2)}x`;
      });
    }
  }

  async applyPreset(presetName) {
    try {
      const res = await fetch(`/api/settings/preset/${presetName}`, { method: 'POST' });
      const saved = await res.json();
      this.applySettingsToAudio(saved);

      // Update dialog inputs if open
      document.getElementById('set-verbosity').value = saved.verbosity_level;
      document.getElementById('set-mode').value = saved.feedback_mode;
      document.getElementById('set-earcon-vol').value = Math.round(saved.earcon_volume * 100);
      document.getElementById('lbl-earcon-vol').textContent = `${Math.round(saved.earcon_volume * 100)}%`;
      document.getElementById('set-speech-rate').value = Math.round(saved.speech_rate * 100);
      document.getElementById('lbl-speech-rate').textContent = `${saved.speech_rate.toFixed(2)}x`;

      if (window.resonaSpeech) {
        window.resonaSpeech.speak(`Applied ${presetName} audio preset.`);
      }
    } catch (e) {}
  }

  _bindGlobalKeybindings() {
    window.addEventListener('keydown', (e) => {
      if (e.key === 'F5' || (e.ctrlKey && e.key === 'Enter')) {
        e.preventDefault();
        this.analyzeAndRun();
      } else if (e.key === 'F10' && !e.shiftKey) {
        e.preventDefault();
        window.resonaDebugger.stepForward();
      } else if (e.key === 'F10' && e.shiftKey) {
        e.preventDefault();
        window.resonaDebugger.stepBackward();
      } else if (e.ctrlKey && e.shiftKey && (e.key === 'P' || e.key === 'p')) {
        e.preventDefault();
        window.resonaDebugger.toggleContinuousSoundscape();
      } else if (e.altKey && (e.key === 'O' || e.key === 'o')) {
        e.preventDefault();
        this.announceOutline();
      } else if (e.altKey && (e.key === 'A' || e.key === 'a')) {
        e.preventDefault();
        const speakBtn = document.getElementById('btn-speak-narrative');
        if (speakBtn) speakBtn.click();
      } else if (e.altKey && (e.key === 'S' || e.key === 's')) {
        e.preventDefault();
        const settingsBtn = document.getElementById('btn-audio-settings');
        if (settingsBtn) settingsBtn.click();
      } else if (e.altKey && (e.key === 'T' || e.key === 't')) {
        e.preventDefault();
        this.cycleTheme();
      } else if (e.altKey && (e.key === 'H' || e.key === 'h')) {
        e.preventDefault();
        this.announceHelp();
      } else if (e.key === 'Escape') {
        const modal = document.getElementById('modal-settings');
        if (modal && modal.style.display === 'flex') {
          modal.style.display = 'none';
          modal.classList.add('sr-only');
        }
        if (window.resonaSpeech) window.resonaSpeech.stop();
        if (window.resonaDebugger) window.resonaDebugger.stopSoundscape();
      }
    });

    if (this.editor) {
      this.editor.addEventListener('keyup', (e) => {
        if (['ArrowUp', 'ArrowDown', 'Enter', 'Home', 'End'].includes(e.key)) {
          this._sonifyCurrentEditorLine();
        }
      });
      this.editor.addEventListener('click', () => {
        this._sonifyCurrentEditorLine();
      });
    }
  }

  _sonifyCurrentEditorLine() {
    if (!this.editor) return;
    const text = this.editor.value;
    const cursorPos = this.editor.selectionStart;

    const lastNewline = text.lastIndexOf('\n', cursorPos - 1);
    const lineStart = lastNewline === -1 ? 0 : lastNewline + 1;
    let lineEnd = text.indexOf('\n', cursorPos);
    if (lineEnd === -1) lineEnd = text.length;

    const lineText = text.substring(lineStart, lineEnd);
    let spaces = 0;
    for (let i = 0; i < lineText.length; i++) {
      if (lineText[i] === ' ') spaces++;
      else if (lineText[i] === '\t') spaces += 4;
      else break;
    }
    const depth = Math.floor(spaces / 4);

    if (window.resonaAudio && (!this.currentSettings || this.currentSettings.indentation_audio)) {
      window.resonaAudio.playDepthTone(depth);
    }
    const lineDisplay = document.getElementById('footer-cursor-line');
    if (lineDisplay) lineDisplay.textContent = `Line: ${this.getCurrentLineNumber()} (Depth ${depth})`;
  }

  _bindHeaderButtons() {
    const runBtn = document.getElementById('btn-run-code');
    const outlineBtn = document.getElementById('btn-hear-outline');
    const themeBtn = document.getElementById('btn-toggle-theme');
    const helpBtn = document.getElementById('btn-help-shortcuts');
    const muteBtn = document.getElementById('btn-toggle-audio');

    if (runBtn) runBtn.addEventListener('click', () => this.analyzeAndRun());
    if (outlineBtn) outlineBtn.addEventListener('click', () => this.announceOutline());
    if (themeBtn) themeBtn.addEventListener('click', () => this.cycleTheme());
    if (helpBtn) helpBtn.addEventListener('click', () => this.announceHelp());
    if (muteBtn) {
      muteBtn.addEventListener('click', () => {
        const isMuted = window.resonaAudio.toggleMute();
        muteBtn.textContent = isMuted ? '🔇 Audio Muted' : '🔊 Audio Active';
      });
    }
  }

  _bindTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        tabBtns.forEach(b => b.classList.remove('active'));
        tabPanes.forEach(p => p.style.display = 'none');

        btn.classList.add('active');
        const targetId = btn.dataset.tab;
        const targetPane = document.getElementById(targetId);
        if (targetPane) targetPane.style.display = 'block';
      });
    });
  }

  _bindExampleSelector() {
    const sel = document.getElementById('example-code-select');
    if (!sel) return;

    sel.addEventListener('change', async (e) => {
      const filename = e.target.value;
      if (!filename) return;

      try {
        const res = await fetch(`/api/example/${filename}`);
        const data = await res.json();
        if (data.code) {
          this.editor.value = data.code;
          await this.analyzeAndRun();
        }
      } catch (err) {
        console.error("Failed to load example:", err);
      }
    });
  }
}

window.addEventListener('DOMContentLoaded', () => {
  window.resonaApp = new ResonaApp();
  window.resonaApp.init();
});

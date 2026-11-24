/**
 * RESONA Debugger UI & Soundscape Player
 * Manages step-by-step time-travel debugging, variable watches, and automated audio playback.
 */

class ResonaDebuggerUI {
  constructor() {
    this.events = [];
    this.currentStepIndex = -1;
    this.isPlayingSoundscape = false;
    this.soundscapeTimer = null;
    this.playbackIntervalMs = 220;
    this.onStepChangeCallback = null;
  }

  init(onStepChange) {
    this.onStepChangeCallback = onStepChange;
    this._bindControls();
  }

  loadTrace(traceResult) {
    this.stopSoundscape();
    this.events = traceResult.events || [];
    this.currentStepIndex = -1;

    const totalStepsEl = document.getElementById('debug-total-steps');
    if (totalStepsEl) totalStepsEl.textContent = this.events.length;

    // Render console stdout
    const consoleEl = document.getElementById('console-output-view');
    if (consoleEl) {
      consoleEl.textContent = traceResult.full_stdout || '(No standard output generated)';
    }

    if (this.events.length > 0) {
      this.jumpToStep(0);
    } else {
      this.updateUIEmpty();
    }
  }

  jumpToStep(stepIdx) {
    if (stepIdx < 0 || stepIdx >= this.events.length) return;
    this.currentStepIndex = stepIdx;
    const ev = this.events[stepIdx];

    // Update UI counters
    const currStepEl = document.getElementById('debug-curr-step');
    const currLineEl = document.getElementById('debug-curr-line');
    if (currStepEl) currStepEl.textContent = stepIdx + 1;
    if (currLineEl) currLineEl.textContent = ev.line_number;

    // Update Call Stack
    const stackEl = document.getElementById('call-stack-view');
    if (stackEl) {
      stackEl.innerHTML = `
        <div style="font-family:var(--font-mono);font-size:0.88rem;padding:4px 0;">
          <strong>Function:</strong> ${ev.function_name}() | <strong>Depth:</strong> ${ev.call_depth}
        </div>
      `;
    }

    // Update Variables Table
    const varTbody = document.getElementById('variables-table-body');
    if (varTbody) {
      varTbody.innerHTML = '';
      const changedVarNames = new Set((ev.variable_changes || []).map(vc => vc.name));

      const entries = Object.entries(ev.locals_snapshot || {});
      if (entries.length === 0) {
        varTbody.innerHTML = '<tr><td colspan="2" style="opacity:0.6;font-style:italic;">No active variables in scope</td></tr>';
      } else {
        entries.forEach(([name, val]) => {
          const row = document.createElement('tr');
          if (changedVarNames.has(name)) {
            row.className = 'highlight-change';
          }
          row.innerHTML = `
            <td><code>${name}</code></td>
            <td><code>${val}</code></td>
          `;
          varTbody.appendChild(row);
        });
      }
    }

    // Play acoustic sonification
    this._playEventAudio(ev);

    if (this.onStepChangeCallback) {
      this.onStepChangeCallback(ev);
    }
  }

  stepForward() {
    if (this.currentStepIndex < this.events.length - 1) {
      this.jumpToStep(this.currentStepIndex + 1);
    } else {
      if (window.resonaSpeech) window.resonaSpeech.announce("Reached end of execution trace.");
    }
  }

  stepBackward() {
    if (this.currentStepIndex > 0) {
      this.jumpToStep(this.currentStepIndex - 1);
    } else {
      if (window.resonaSpeech) window.resonaSpeech.announce("Already at the start of execution.");
    }
  }

  toggleContinuousSoundscape() {
    if (this.isPlayingSoundscape) {
      this.stopSoundscape();
    } else {
      this.startSoundscape();
    }
  }

  startSoundscape() {
    if (this.events.length === 0) return;
    this.isPlayingSoundscape = true;
    const playBtn = document.getElementById('btn-play-soundscape');
    if (playBtn) playBtn.innerHTML = '&#10074;&#10074; Pause Audio';

    if (window.resonaSpeech) window.resonaSpeech.announce("Starting continuous audio soundscape playback.");

    if (this.currentStepIndex >= this.events.length - 1) {
      this.currentStepIndex = -1;
    }

    this.soundscapeTimer = setInterval(() => {
      if (this.currentStepIndex < this.events.length - 1) {
        this.stepForward();
      } else {
        this.stopSoundscape();
        if (window.resonaAudio) window.resonaAudio.playEarcon('execution_success');
        if (window.resonaSpeech) window.resonaSpeech.announce("Soundscape playback complete.");
      }
    }, this.playbackIntervalMs);
  }

  stopSoundscape() {
    this.isPlayingSoundscape = false;
    if (this.soundscapeTimer) {
      clearInterval(this.soundscapeTimer);
      this.soundscapeTimer = null;
    }
    const playBtn = document.getElementById('btn-play-soundscape');
    if (playBtn) playBtn.innerHTML = '&#9658; Play Soundscape';
  }

  jumpToError() {
    const errIdx = this.events.findIndex(e => e.event_type === 'exception');
    if (errIdx !== -1) {
      this.jumpToStep(errIdx);
      if (window.resonaSpeech) window.resonaSpeech.announce(`Jumped to exception at line ${this.events[errIdx].line_number}`);
    } else {
      if (window.resonaSpeech) window.resonaSpeech.announce("No exceptions found in this execution.");
    }
  }

  _playEventAudio(ev) {
    if (!window.resonaAudio) return;

    if (ev.event_type === 'exception') {
      window.resonaAudio.playEarcon('runtime_error');
    } else if (ev.event_type === 'call') {
      window.resonaAudio.playEarcon('function_entry');
    } else if (ev.event_type === 'return') {
      window.resonaAudio.playEarcon('function_return');
    } else if (ev.variable_changes && ev.variable_changes.length > 0) {
      window.resonaAudio.playEarcon('variable_change');
    } else if (ev.code_text.startsWith('for ') || ev.code_text.startsWith('while ')) {
      window.resonaAudio.playEarcon('loop_iteration');
    } else if (ev.code_text.startsWith('if ') || ev.code_text.startsWith('elif ')) {
      window.resonaAudio.playEarcon('branch_true');
    } else {
      window.resonaAudio.playDepthTone(ev.call_depth);
    }
  }

  updateUIEmpty() {
    const currStepEl = document.getElementById('debug-curr-step');
    const currLineEl = document.getElementById('debug-curr-line');
    if (currStepEl) currStepEl.textContent = '0';
    if (currLineEl) currLineEl.textContent = '-';
  }

  _bindControls() {
    const stepNextBtn = document.getElementById('btn-step-next');
    const stepPrevBtn = document.getElementById('btn-step-prev');
    const playSoundscapeBtn = document.getElementById('btn-play-soundscape');
    const jumpErrorBtn = document.getElementById('btn-jump-error');

    if (stepNextBtn) stepNextBtn.addEventListener('click', () => this.stepForward());
    if (stepPrevBtn) stepPrevBtn.addEventListener('click', () => this.stepBackward());
    if (playSoundscapeBtn) playSoundscapeBtn.addEventListener('click', () => this.toggleContinuousSoundscape());
    if (jumpErrorBtn) jumpErrorBtn.addEventListener('click', () => this.jumpToError());
  }
}

window.resonaDebugger = new ResonaDebuggerUI();

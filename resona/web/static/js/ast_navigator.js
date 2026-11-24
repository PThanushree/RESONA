/**
 * RESONA AST Tree Navigator
 * Accessible hierarchical tree explorer with keyboard navigation and sonification.
 */

class ResonaASTNavigator {
  constructor() {
    this.container = null;
    this.nodes = [];
    this.selectedIndex = -1;
    this.onNodeSelectCallback = null;
  }

  init(containerId, onNodeSelect) {
    this.container = document.getElementById(containerId);
    this.onNodeSelectCallback = onNodeSelect;
    this._bindKeyboard();
  }

  setTree(analysisResult) {
    if (!this.container) return;
    this.container.innerHTML = '';
    this.nodes = [];
    this.selectedIndex = -1;

    if (!analysisResult || !analysisResult.is_valid) {
      this.container.innerHTML = `
        <div class="tree-node error-border" role="alert">
          <span class="node-badge" style="background:#f87171;color:#000;">Syntax Error</span>
          <span style="font-size:0.85rem;margin-left:6px;">Line ${analysisResult?.syntax_error?.line || 1}</span>
        </div>
      `;
      return;
    }

    // Flatten tree for sequential keyboard navigation
    this.nodes = analysisResult.flattened_nodes || [];
    this.nodes.forEach((node, index) => {
      const el = document.createElement('div');
      el.className = `tree-node node-indent-${Math.min(node.nesting_level, 4)}`;
      el.setAttribute('role', 'treeitem');
      el.setAttribute('tabindex', index === 0 ? '0' : '-1');
      el.setAttribute('aria-label', `${node.node_type}: ${node.name}, line ${node.start_line}, depth ${node.nesting_level}`);
      el.dataset.index = index;
      el.dataset.nodeId = node.id;
      el.dataset.startLine = node.start_line;

      let badgeColor = 'var(--accent-primary)';
      if (node.node_type.includes('Function')) badgeColor = 'var(--success-color)';
      else if (node.node_type === 'ClassDef') badgeColor = 'var(--info-color)';
      else if (['For', 'While'].includes(node.node_type)) badgeColor = 'var(--warning-color)';
      else if (['If', 'Elif', 'Else'].includes(node.node_type)) badgeColor = 'var(--accent-primary)';

      el.innerHTML = `
        <div style="display:flex;align-items:center;gap:6px;overflow:hidden;">
          <span class="node-badge" style="border-color:${badgeColor}">${node.node_type}</span>
          <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${node.name}</span>
        </div>
        <span style="font-size:0.75rem;opacity:0.7;">L${node.start_line}</span>
      `;

      el.addEventListener('click', () => this.selectNode(index));
      this.container.appendChild(el);
    });

    if (this.nodes.length > 0) {
      this.selectNode(0, false);
    }
  }

  selectNode(index, focusElement = true) {
    if (index < 0 || index >= this.nodes.length) return;
    this.selectedIndex = index;
    const node = this.nodes[index];

    // Update DOM selection
    const items = this.container.querySelectorAll('.tree-node');
    items.forEach((item, idx) => {
      if (idx === index) {
        item.classList.add('selected');
        item.setAttribute('tabindex', '0');
        item.setAttribute('aria-selected', 'true');
        if (focusElement) item.focus();
      } else {
        item.classList.remove('selected');
        item.setAttribute('tabindex', '-1');
        item.setAttribute('aria-selected', 'false');
      }
    });

    // Sonification: Play earcon based on node type & nesting depth
    let earcon = 'indent_level_' + Math.min(node.nesting_level, 7);
    if (node.node_type.includes('Function')) earcon = 'function_entry';
    else if (node.node_type === 'ClassDef') earcon = 'class_entry';
    else if (['For', 'While'].includes(node.node_type)) earcon = 'loop_iteration';
    else if (['If', 'Elif'].includes(node.node_type)) earcon = 'branch_true';
    else if (node.node_type === 'Else') earcon = 'branch_false';
    else if (node.node_type === 'Return') earcon = 'function_return';

    if (window.resonaAudio) {
      window.resonaAudio.playEarcon(earcon);
    }

    // Accessible narration
    if (window.resonaSpeech) {
      window.resonaSpeech.announce(`${node.node_type} ${node.name} at line ${node.start_line}, depth ${node.nesting_level}`);
    }

    if (this.onNodeSelectCallback) {
      this.onNodeSelectCallback(node);
    }
  }

  _bindKeyboard() {
    if (!this.container) return;
    this.container.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        this.selectNode(Math.min(this.selectedIndex + 1, this.nodes.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        this.selectNode(Math.max(this.selectedIndex - 1, 0));
      } else if (e.key === 'Home') {
        e.preventDefault();
        this.selectNode(0);
      } else if (e.key === 'End') {
        e.preventDefault();
        this.selectNode(this.nodes.length - 1);
      } else if (e.key === 'Enter') {
        e.preventDefault();
        const node = this.nodes[this.selectedIndex];
        if (this.onNodeSelectCallback) this.onNodeSelectCallback(node, true);
      }
    });
  }
}

window.resonaAST = new ResonaASTNavigator();

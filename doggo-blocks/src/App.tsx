import { useEffect, useRef, useState } from 'react';
import { Play, Square, Code2 } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import * as ScratchBlocks from 'scratch-blocks';
import { defineBlocks } from './blocks.js';
import { createGenerator } from './generator.js';
import { toolboxConfig } from './toolbox.js';
import { doggoTheme } from './theme.js';

ScratchBlocks.ScratchMsgs.setLocale('en');
defineBlocks();
const pyGen = createGenerator();

// Register a flyout inflater for 'category' items.
const _noOpRect = { getHeight: () => 0, getWidth: () => 0 };
const _noOpEl   = { moveBy: () => {}, getBoundingRectangle: () => _noOpRect };
const _noOpItem = { getType: () => 'category', getElement: () => _noOpEl };
ScratchBlocks.registry.register(
  ScratchBlocks.registry.Type.FLYOUT_INFLATER,
  'category',
  class {
    load()        { return _noOpItem; }
    gapForItem()  { return 0; }
    disposeItem() {}
    setFlyout()   {}
    getType()     { return 'category'; }
  },
);

// Generate XML flyout elements for the Variables category.
// Overrides the built-in Scratch callback which:
//   (a) omits the math_number shadow on VALUE (Scratch expects reporter blocks),
//   (b) re-registers CREATE_VARIABLE → prompt() on every call.
// Our version adds the shadow and leaves the button callback alone.
function variablesFlyoutXML(ws: ScratchBlocks.WorkspaceSvg): Element[] {
  const vars = ws.getVariableMap().getAllVariables();
  const items: Element[] = [];

  const button = document.createElement('button');
  button.setAttribute('text', 'Create Variable');
  button.setAttribute('callbackKey', 'CREATE_VARIABLE');
  items.push(button);

  for (const v of vars) {
    // set [var] to [0]
    const setBlock = document.createElement('block');
    setBlock.setAttribute('type', 'variables_set');
    const setField = document.createElement('field');
    setField.setAttribute('name', 'VAR');
    setField.setAttribute('id', v.getId());
    setField.textContent = v.getName();
    setBlock.appendChild(setField);
    const valueEl = document.createElement('value');
    valueEl.setAttribute('name', 'VALUE');
    const shadow = document.createElement('shadow');
    shadow.setAttribute('type', 'math_number');
    const numField = document.createElement('field');
    numField.setAttribute('name', 'NUM');
    numField.textContent = '0';
    shadow.appendChild(numField);
    valueEl.appendChild(shadow);
    setBlock.appendChild(valueEl);
    items.push(setBlock);

    // [var] reporter
    const getBlock = document.createElement('block');
    getBlock.setAttribute('type', 'variables_get');
    const getField = document.createElement('field');
    getField.setAttribute('name', 'VAR');
    getField.setAttribute('id', v.getId());
    getField.textContent = v.getName();
    getBlock.appendChild(getField);
    items.push(getBlock);
  }

  return items;
}

export function App() {
  const blocklyDivRef = useRef<HTMLDivElement>(null);
  const workspaceRef = useRef<ScratchBlocks.WorkspaceSvg | null>(null);
  const [running, setRunning] = useState(false);
  const [status, setStatus] = useState('');
  const [varDialog, setVarDialog] = useState(false);
  const [varName, setVarName] = useState('');
  const [codeOpen, setCodeOpen] = useState(false);
  const [generatedCode, setGeneratedCode] = useState('# Place blocks to generate code');

  useEffect(() => {
    if (!blocklyDivRef.current || workspaceRef.current) return;

    const ws = ScratchBlocks.inject(blocklyDivRef.current, {
      toolbox: toolboxConfig,
      theme: doggoTheme,
      media: '/media/',
      grid: { spacing: 24, length: 1, colour: '#c0c0c0', snap: true },
      scrollbars: true,
      zoom: { controls: true, wheel: true, startScale: 0.85 },
      sounds: false,
    }) as ScratchBlocks.WorkspaceSvg;
    workspaceRef.current = ws;

    // Replace the built-in 'VARIABLE' callback with ours.
    ws.registerToolboxCategoryCallback(
      'VARIABLE',
      variablesFlyoutXML,
    );
    // Our callback never calls registerButtonCallback(prompt), so this
    // registration is permanent for the lifetime of the workspace.
    ws.registerButtonCallback('CREATE_VARIABLE', () => {
      setVarName('');
      setVarDialog(true);
    });

    ws.addChangeListener((event: ScratchBlocks.Events.Abstract) => {
      setGeneratedCode(pyGen.workspaceToCode(ws) || '# Place blocks to generate code');

      if (event.type === 'delete') {
        ws.trashcan?.emptyContents();
      }

      // Refresh the variables flyout when a variable is deleted or renamed.
      if (event.type === 'var_delete' || event.type === 'var_rename') {
        const tb = ws.getToolbox() as unknown as {
          getFlyout: () => { show: (c: unknown) => void };
          getInitialFlyoutContents: () => unknown;
        };
        tb.getFlyout().show(tb.getInitialFlyoutContents());
      }
    });

    for (const [cls, label] of [
      ['blocklyZoomIn', 'Zoom in'],
      ['blocklyZoomOut', 'Zoom out'],
      ['blocklyZoomReset', 'Reset zoom'],
    ] as const) {
      const el = blocklyDivRef.current.querySelector(`.${cls}`);
      if (el) {
        const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
        title.textContent = label;
        el.prepend(title);
      }
    }

    const observer = new ResizeObserver(() => {
      ScratchBlocks.svgResize(ws);
    });
    observer.observe(blocklyDivRef.current);

    return () => {
      observer.disconnect();
      ws.dispose();
      workspaceRef.current = null;
    };
  }, []);

  useEffect(() => {
    window.doggo.onOutput((line) => console.log('[doggo]', line));
    window.doggo.onDone((exitCode) => {
      setRunning(false);
      setStatus(exitCode === 0 ? 'Done ✓' : `Error (exit ${exitCode})`);
      setTimeout(() => setStatus(''), 3000);
    });
  }, []);

  function handleRun() {
    const ws = workspaceRef.current;
    if (!ws) return;
    const code = pyGen.workspaceToCode(ws);
    console.log('[doggo-blocks] generated script:\n' + code);
    setRunning(true);
    setStatus('Running…');
    window.doggo.runScript(code);
  }

  function handleStop() {
    window.doggo.stopScript();
  }

  function handleCreateVar() {
    const name = varName.trim();
    const ws = workspaceRef.current;
    if (name && ws) {
      ws.getVariableMap().createVariable(name);
      const tb = ws.getToolbox() as unknown as {
        getFlyout: () => {
          show: (c: unknown) => void;
          scrollToCategory: (item: unknown) => void;
        };
        getInitialFlyoutContents: () => unknown;
        getToolboxItems: () => Array<{ getName: () => string }>;
      };
      tb.getFlyout().show(tb.getInitialFlyoutContents());
      const varItem = tb.getToolboxItems().find((item) => item.getName?.() === 'Variables');
      if (varItem) tb.getFlyout().scrollToCategory(varItem);
    }
    setVarDialog(false);
  }

  return (
    <>
      <div id="toolbar">
        <button id="btn-run" onClick={handleRun} disabled={running}>
          <Play size={14} /> Run
        </button>
        <button id="btn-stop" onClick={handleStop} disabled={!running}>
          <Square size={14} /> Stop
        </button>
        <span id="status">{status}</span>
        <button
          id="btn-code"
          onClick={() => setCodeOpen((o) => !o)}
          title="Toggle Python code viewer"
        >
          <Code2 size={14} /> Code
        </button>
      </div>
      <div id="main-area">
        <div id="blockly-div" ref={blocklyDivRef} />
        <div id="code-panel" className={codeOpen ? 'open' : ''}>
          <div id="code-panel-header">
            <span>Generated Python</span>
          </div>
          <SyntaxHighlighter
            language="python"
            style={vscDarkPlus}
            customStyle={{
              margin: 0,
              flex: 1,
              fontSize: '13px',
              lineHeight: '1.6',
              background: '#1e1e2e',
              minWidth: '360px',
              height: '100%',
              overflow: 'auto',
            }}
          >
            {generatedCode}
          </SyntaxHighlighter>
        </div>
      </div>

      {varDialog && (
        <div className="dialog-overlay" onClick={() => setVarDialog(false)}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <h3>New variable</h3>
            <input
              autoFocus
              placeholder="Variable name"
              value={varName}
              onChange={(e) => setVarName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') { e.preventDefault(); handleCreateVar(); }
                if (e.key === 'Escape') setVarDialog(false);
              }}
            />
            <div className="dialog-buttons">
              <button onClick={handleCreateVar} disabled={!varName.trim()}>OK</button>
              <button onClick={() => setVarDialog(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

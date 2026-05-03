import { Code2, Play } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import * as ScratchBlocks from 'scratch-blocks';

import { defineBlocks } from './blocks.js';
import { createGenerator } from './generator.js';
import { doggoTheme } from './theme.js';
import { toolboxConfig } from './toolbox.js';

ScratchBlocks.ScratchMsgs.setLocale('en');
defineBlocks();
const pyGen = createGenerator();

// Build the flat flyout item array that show() expects — one label + contents
// per toolbox category, with Variables section updated for current variables.
const buildFlyoutItems = (
  vars: ScratchBlocks.IVariableModel<ScratchBlocks.IVariableState>[],
): ScratchBlocks.utils.toolbox.FlyoutItemInfoArray => {
  const numShadow = { shadow: { type: 'math_number', fields: { NUM: 0 } } };
  // FieldVariable.loadState() expects { id, name, type } not a bare UUID string.
  // One set block is enough (it has a dropdown); one get block per variable.
  const firstVar = vars[0];
  const varBlocks = [
    ...(firstVar
      ? [
          {
            kind: 'block',
            type: 'variables_set',
            fields: {
              VAR: { id: firstVar.getId(), name: firstVar.getName(), type: firstVar.getType() },
            },
            inputs: { VALUE: numShadow },
          },
        ]
      : []),
    ...vars.map((v) => ({
      kind: 'block',
      type: 'variables_get',
      fields: { VAR: { id: v.getId(), name: v.getName(), type: v.getType() } },
    })),
  ];

  return toolboxConfig.contents.flatMap((cat): ScratchBlocks.utils.toolbox.FlyoutItemInfo[] => {
    const label = { kind: 'label', text: cat.name };
    if (cat.name === 'Variables') {
      const button = { kind: 'button', text: 'Create Variable', callbackkey: 'CREATE_VARIABLE' };
      return [label, button, ...varBlocks];
    }
    return [label, ...cat.contents];
  });
}

export const App = () => {
  const blocklyDivRef = useRef<HTMLDivElement>(null);
  const workspaceRef = useRef<ScratchBlocks.WorkspaceSvg | null>(null);
  const refreshVariablesRef = useRef<(() => void) | null>(null);
  const [status, setStatus] = useState('');
  const [varDialog, setVarDialog] = useState(false);
  const [varName, setVarName] = useState('');
  const [codeOpen, setCodeOpen] = useState(false);
  const [generatedCode, setGeneratedCode] = useState('# Place blocks to generate code');
  const [ctxMenu, setCtxMenu] = useState<{
    x: number;
    y: number;
    varId: string;
    varName: string;
  } | null>(null);
  const [renameVarId, setRenameVarId] = useState<string | null>(null);
  const [renameName, setRenameName] = useState('');

  useEffect(() => {
    if (!blocklyDivRef.current || workspaceRef.current) {
      return;
    }

    const ws = ScratchBlocks.inject(blocklyDivRef.current, {
      toolbox: toolboxConfig,
      theme: doggoTheme,
      media: './media/',
      grid: { spacing: 24, length: 1, colour: '#c0c0c0', snap: true },
      scrollbars: true,
      zoom: { controls: true, wheel: true, startScale: 0.85 },
      sounds: false,
    });
    workspaceRef.current = ws;

    ws.registerButtonCallback('CREATE_VARIABLE', () => {
      setVarName('');
      setVarDialog(true);
    });

    const refreshVariables = () => {
      const vars = ws.getVariableMap().getAllVariables();
      const items = buildFlyoutItems(vars);
      ws.getToolbox()?.getFlyout()?.show(items);
      // show() resets scroll to top — click the Variables sidebar item to scroll back.
      setTimeout(() => {
        const cats =
          blocklyDivRef.current?.querySelectorAll<HTMLElement>('.blocklyToolboxCategory');
        for (const el of cats ?? []) {
          if (
            el.querySelector('.blocklyToolboxCategoryLabel')?.textContent?.trim() === 'Variables'
          ) {
            el.click();
            break;
          }
        }
      }, 50);
    };
    refreshVariablesRef.current = refreshVariables;

    ws.addChangeListener((event: ScratchBlocks.Events.Abstract) => {
      setGeneratedCode(pyGen.workspaceToCode(ws) || '# Place blocks to generate code');

      if (event.type === 'delete') {
        ws.trashcan?.emptyContents();
      }

      if (event.type === 'var_delete' || event.type === 'var_rename') {
        refreshVariables();
      }
    });

    for (const [cls, label] of [
      ['blocklyZoomIn', 'Zoom in'],
      ['blocklyZoomOut', 'Zoom out'],
      ['blocklyZoomReset', 'Reset zoom'],
    ]) {
      const el = blocklyDivRef.current.querySelector(`.${cls}`);
      if (el) {
        const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
        title.textContent = label;
        el.prepend(title);
      }
    }

    const observer = new ResizeObserver(() => ScratchBlocks.svgResize(ws));
    observer.observe(blocklyDivRef.current);

    const blocklyEl = blocklyDivRef.current;

    // Resolve the flyout variable block (if any) under the event target.
    // Block SVG groups carry data-id; walk up to find it.
    const flyoutVarBlockAt = (target: EventTarget | null) => {
      let el: Element | null = target as Element | null;
      while (el && !el.hasAttribute('data-id')) {
        el = el.parentElement;
      }
      if (!el) {
        return null;
      }
      const dataId = el.getAttribute('data-id');
      if (!dataId) {
        return null;
      }
      const flyout = ws.getToolbox()?.getFlyout();
      if (!flyout) {
        return null;
      }
      const block = flyout.getWorkspace().getBlockById(dataId);
      if (!block?.workspace.isFlyout) {
        return null;
      }
      if (block.type !== 'variables_get') {
        return null;
      }
      return block;
    };

    // Intercept right-click pointerdown before Blockly starts its gesture.
    const handlePointerDown = (e: PointerEvent) => {
      if (e.button !== 2 || !flyoutVarBlockAt(e.target)) {
        return;
      }
      e.stopPropagation();
    };

    const handleContextMenu = (e: MouseEvent) => {
      const block = flyoutVarBlockAt(e.target);
      if (!block) {
        return;
      }
      const varId = block.getField('VAR')?.getValue();
      if (!varId) {
        return;
      }
      const variable = ws.getVariableMap().getVariableById(varId);
      if (!variable) {
        return;
      }
      e.preventDefault();
      e.stopPropagation();
      setCtxMenu({ x: e.clientX, y: e.clientY, varId, varName: variable.getName() });
    };

    blocklyEl.addEventListener('pointerdown', handlePointerDown, true);
    blocklyEl.addEventListener('contextmenu', handleContextMenu, true);

    return () => {
      observer.disconnect();
      blocklyEl.removeEventListener('pointerdown', handlePointerDown, true);
      blocklyEl.removeEventListener('contextmenu', handleContextMenu, true);
      ws.dispose();
      workspaceRef.current = null;
    };
  }, []);

  useEffect(() => {
    window.doggo.onOutput((line) => console.log('[doggo]', line));
    window.doggo.onDone((exitCode) => {
      setStatus(exitCode === 0 ? 'Done ✓' : `Error (exit ${exitCode})`);
      setTimeout(() => setStatus(''), 3000);
    });
  }, []);

  const handleRun = () => {
    const ws = workspaceRef.current;
    if (!ws) {
      return;
    }
    const code = pyGen.workspaceToCode(ws);
    console.log(`[doggo-blocks] generated script:\n${code}`);
    setStatus('Running…');
    window.doggo.runScript(code);
  }

  const handleRenameVar = () => {
    const ws = workspaceRef.current;
    const newName = renameName.trim();
    if (!ws || !renameVarId || !newName) {
      return;
    }
    const variable = ws.getVariableMap().getVariableById(renameVarId);
    if (variable) {
      ws.getVariableMap().renameVariable(variable, newName);
    }
    setRenameVarId(null);
  }

  const handleDeleteVar = (varId: string) => {
    const ws = workspaceRef.current;
    const variable = ws?.getVariableMap().getVariableById(varId);
    if (ws && variable) {
      ws.getVariableMap().deleteVariable(variable);
    }
    setCtxMenu(null);
  }

  const handleCreateVar = () => {
    const name = varName.trim();
    const ws = workspaceRef.current;
    if (name && ws) {
      ws.getVariableMap().createVariable(name);
      refreshVariablesRef.current?.();
    }
    setVarDialog(false);
  }

  return (
    <>
      <div id="toolbar">
        <button id="btn-run" onClick={handleRun}>
          <Play size={14} /> Run
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
        <div id="blockly-div" ref={blocklyDivRef} onClick={() => setCtxMenu(null)} />
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

      {ctxMenu && (
        <>
          <div
            style={{ position: 'fixed', inset: 0, zIndex: 999 }}
            onClick={() => setCtxMenu(null)}
          />
          <div className="context-menu" style={{ left: ctxMenu.x, top: ctxMenu.y }}>
            <button
              onClick={() => {
                setRenameVarId(ctxMenu.varId);
                setRenameName(ctxMenu.varName);
                setCtxMenu(null);
              }}
            >
              Rename
            </button>
            <button onClick={() => handleDeleteVar(ctxMenu.varId)}>Delete</button>
          </div>
        </>
      )}

      {renameVarId && (
        <div className="dialog-overlay" onClick={() => setRenameVarId(null)}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <h3>Rename variable</h3>
            <input
              autoFocus
              value={renameName}
              onChange={(e) => setRenameName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleRenameVar();
                }
                if (e.key === 'Escape') {
                  setRenameVarId(null);
                }
              }}
            />
            <div className="dialog-buttons">
              <button onClick={handleRenameVar} disabled={!renameName.trim()}>
                OK
              </button>
              <button onClick={() => setRenameVarId(null)}>Cancel</button>
            </div>
          </div>
        </div>
      )}

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
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleCreateVar();
                }
                if (e.key === 'Escape') {
                  setVarDialog(false);
                }
              }}
            />
            <div className="dialog-buttons">
              <button onClick={handleCreateVar} disabled={!varName.trim()}>
                OK
              </button>
              <button onClick={() => setVarDialog(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

import { useEffect, useRef, useState } from 'react';
import * as ScratchBlocks from 'scratch-blocks';
import { defineBlocks } from './blocks.js';
import { createGenerator } from './generator.js';
import { toolboxConfig } from './toolbox.js';
import { doggoTheme } from './theme.js';

// Initialise once at module load — not inside the component.
ScratchBlocks.ScratchMsgs.setLocale('en');
defineBlocks();
const pyGen = createGenerator();

export function App() {
  const blocklyDivRef = useRef<HTMLDivElement>(null);
  const workspaceRef = useRef<ScratchBlocks.WorkspaceSvg | null>(null);
  const [running, setRunning] = useState(false);
  const [status, setStatus] = useState('');

  // Inject the Blockly workspace once the div is mounted.
  useEffect(() => {
    if (!blocklyDivRef.current || workspaceRef.current) return;

    const ws = ScratchBlocks.inject(blocklyDivRef.current, {
      toolbox: toolboxConfig,
      theme: doggoTheme,
      media: '/media/',
      scrollbars: true,
      zoom: { controls: true, wheel: true, startScale: 0.85 },
      sounds: false,
    }) as ScratchBlocks.WorkspaceSvg;
    workspaceRef.current = ws;

    // Add tooltips to the scratch zoom controls (SVG <title> = native browser tooltip).
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

    // Keep workspace filling its container as the window resizes.
    const observer = new ResizeObserver(() => {
      (ScratchBlocks as unknown as { svgResize: (ws: ScratchBlocks.WorkspaceSvg) => void })
        .svgResize(ws);
    });
    observer.observe(blocklyDivRef.current);

    return () => {
      observer.disconnect();
      ws.dispose();
      workspaceRef.current = null;
    };
  }, []);

  // Wire up IPC callbacks.
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

  return (
    <>
      <div id="toolbar">
        <button id="btn-run" onClick={handleRun} disabled={running}>
          &#9654; Run
        </button>
        <button id="btn-stop" onClick={handleStop} disabled={!running}>
          &#9632; Stop
        </button>
        <span id="status">{status}</span>
      </div>
      <div id="blockly-div" ref={blocklyDivRef} />
    </>
  );
}

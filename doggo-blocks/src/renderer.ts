import * as ScratchBlocks from 'scratch-blocks';
import { defineBlocks } from './blocks.js';
import { createGenerator } from './generator.js';
import { toolboxConfig } from './toolbox.js';
import { doggoTheme } from './theme.js';

// Required before inject() so scratch-blocks' own built-in blocks have their
// locale messages available when the workspace initialises.
ScratchBlocks.ScratchMsgs.setLocale('en');

defineBlocks();
const pyGen = createGenerator();

const workspace = ScratchBlocks.inject(document.getElementById('blockly-div') as HTMLElement, {
  toolbox: toolboxConfig,
  theme: doggoTheme,
  scrollbars: true,
  zoom: { controls: true, wheel: true, startScale: 0.85 },
  sounds: false,
});

const btnRun  = document.getElementById('btn-run')  as HTMLButtonElement;
const btnStop = document.getElementById('btn-stop') as HTMLButtonElement;
const status  = document.getElementById('status')  as HTMLSpanElement;

btnRun.addEventListener('click', () => {
  const code = pyGen.workspaceToCode(workspace);
  console.log('[doggo-blocks] generated script:\n' + code);
  btnRun.disabled = true;
  btnStop.disabled = false;
  status.textContent = 'Running…';
  window.doggo.runScript(code);
});

btnStop.addEventListener('click', () => {
  window.doggo.stopScript();
});

window.doggo.onOutput((line) => console.log('[doggo]', line));

window.doggo.onDone((exitCode) => {
  btnRun.disabled  = false;
  btnStop.disabled = true;
  status.textContent = exitCode === 0 ? 'Done ✓' : `Error (exit ${exitCode})`;
  setTimeout(() => { status.textContent = ''; }, 3000);
});

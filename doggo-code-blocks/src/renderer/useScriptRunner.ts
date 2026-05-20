import { useEffect, useRef, useState } from 'react';
import type * as ScratchBlocks from 'scratch-blocks';

import type { ErrorData } from './components/ErrorDialog.js';

interface CodeGenerator {
  workspaceToCode(ws: ScratchBlocks.WorkspaceSvg): string;
}

export const useScriptRunner = (
  workspaceRef: { current: ScratchBlocks.WorkspaceSvg | null },
  pyGen: CodeGenerator,
) => {
  const outputRef = useRef<string[]>([]);
  const [status, setStatus] = useState('');
  const [errorDialog, setErrorDialog] = useState<ErrorData | null>(null);

  useEffect(() => {
    window.doggo.onOutput((line) => {
      outputRef.current.push(line);
    });
    window.doggo.onDone((exitCode) => {
      setStatus('');
      if (exitCode === 0) {
        setStatus('Done ✓');
        setTimeout(() => setStatus(''), 3000);
      } else {
        setErrorDialog({
          title: 'Run failed',
          detail: `Exit code ${exitCode ?? 1}`,
          body: outputRef.current.join(''),
        });
      }
    });
  }, []);

  const handleRun = () => {
    const ws = workspaceRef.current;
    if (!ws) {
      return;
    }
    const code = pyGen.workspaceToCode(ws);
    console.log(`[doggo-code-blocks] generated script:\n${code}`);
    outputRef.current = [];
    setStatus('Running…');
    void window.doggo.runScript(code);
  };

  return { status, errorDialog, setErrorDialog, handleRun };
};

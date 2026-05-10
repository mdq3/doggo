import { useEffect, useRef, useState } from 'react';
import * as ScratchBlocks from 'scratch-blocks';

import type { ErrorData } from './components/ErrorDialog.js';
import { ParseError, parsePython } from './pythonParser.js';

export const useFileHandling = (
  workspaceRef: { current: ScratchBlocks.WorkspaceSvg | null },
  refreshVariablesRef: { current: (() => void) | null },
  generatedCode: string,
) => {
  const [currentFilePath, setCurrentFilePath] = useState<string | null>(null);
  const [parseError, setParseError] = useState<ErrorData | null>(null);
  const [newFileConfirmOpen, setNewFileConfirmOpen] = useState(false);

  const doNewFile = () => {
    const ws = workspaceRef.current;
    if (ws) {
      ws.clear();
      refreshVariablesRef.current?.();
    }
    setCurrentFilePath(null);
    setNewFileConfirmOpen(false);
  };

  const newFile = () => {
    const ws = workspaceRef.current;
    if ((ws?.getAllBlocks(false).length ?? 0) > 0) {
      setNewFileConfirmOpen(true);
    } else {
      doNewFile();
    }
  };

  const handleOpenFile = async () => {
    const result = await window.doggo.openFile();
    if (!result) {
      return;
    }
    try {
      const dom = await parsePython(result.content);
      const ws = workspaceRef.current;
      if (!ws) {
        return;
      }
      ScratchBlocks.Xml.clearWorkspaceAndLoadFromXml(dom, ws);
      refreshVariablesRef.current?.();
      setCurrentFilePath(result.filePath);
    } catch (err) {
      setParseError(
        err instanceof ParseError
          ? {
              title: "Can't open as blocks",
              detail: err.line !== undefined ? `Line ${err.line}` : undefined,
              body: err.message,
            }
          : { title: "Can't open as blocks", body: String(err) },
      );
    }
  };

  const handleSaveFile = async (saveAs: boolean) => {
    const filePath = saveAs ? null : currentFilePath;
    const savedPath = await window.doggo.saveFile(filePath, generatedCode);
    if (savedPath) {
      setCurrentFilePath(savedPath);
    }
  };

  const newFileRef = useRef(newFile);
  newFileRef.current = newFile;
  const handleOpenFileRef = useRef(handleOpenFile);
  handleOpenFileRef.current = handleOpenFile;
  const handleSaveFileRef = useRef(handleSaveFile);
  handleSaveFileRef.current = handleSaveFile;

  useEffect(() => {
    window.doggo.onMenuNewFile(() => newFileRef.current());
    window.doggo.onMenuOpenFile(() => void handleOpenFileRef.current());
    window.doggo.onMenuSaveFile(() => void handleSaveFileRef.current(false));
    window.doggo.onMenuSaveFileAs(() => void handleSaveFileRef.current(true));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    parseError,
    setParseError,
    newFile,
    newFileConfirmOpen,
    confirmNewFile: doNewFile,
    cancelNewFile: () => setNewFileConfirmOpen(false),
    openFile: () => void handleOpenFileRef.current(),
    saveFile: () => void handleSaveFileRef.current(false),
  };
};

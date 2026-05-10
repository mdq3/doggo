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
  const [recents, setRecents] = useState<string[]>([]);

  // ── Dirty tracking ─────────────────────────────────────────────────────────
  // generatedCodeRef always holds the latest prop value — set synchronously on
  // every render so confirmIfDirty never reads a stale value regardless of
  // where it is in React's render/effect cycle.
  const generatedCodeRef = useRef(generatedCode);
  generatedCodeRef.current = generatedCode;

  const lastCleanCodeRef = useRef(generatedCode);
  const pendingCleanRef = useRef(false);
  const [isDirty, setIsDirty] = useState(false);

  // Keep isDirty state in sync for reactive consumers (title bar, etc.)
  useEffect(() => {
    if (pendingCleanRef.current) {
      lastCleanCodeRef.current = generatedCode;
      pendingCleanRef.current = false;
      setIsDirty(false);
      return;
    }
    setIsDirty(generatedCode !== lastCleanCodeRef.current);
  }, [generatedCode]); // eslint-disable-line react-hooks/exhaustive-deps

  const markClean = () => {
    lastCleanCodeRef.current = generatedCode;
    setIsDirty(false);
  };

  // ── Title ──────────────────────────────────────────────────────────────────
  useEffect(() => {
    window.doggo.setTitle(currentFilePath, isDirty);
  }, [currentFilePath, isDirty]);

  // ── Discard-unsaved-changes confirmation ───────────────────────────────────
  interface DiscardContext {
    title: string;
    confirmLabel: string;
  }
  const [discardConfirmOpen, setDiscardConfirmOpen] = useState(false);
  const [discardContext, setDiscardContext] = useState<DiscardContext>({
    title: 'Discard unsaved changes?',
    confirmLabel: 'Discard',
  });
  const discardActionRef = useRef<(() => void) | null>(null);

  const confirmIfDirty = (action: () => void, context: DiscardContext) => {
    if (generatedCodeRef.current !== lastCleanCodeRef.current) {
      discardActionRef.current = action;
      setDiscardContext(context);
      setDiscardConfirmOpen(true);
    } else {
      action();
    }
  };

  const confirmDiscard = () => {
    discardActionRef.current?.();
    discardActionRef.current = null;
    setDiscardConfirmOpen(false);
  };

  const cancelDiscard = () => {
    discardActionRef.current = null;
    setDiscardConfirmOpen(false);
  };

  // ── Actions ────────────────────────────────────────────────────────────────
  const doNewFile = () => {
    const ws = workspaceRef.current;
    if (ws) {
      if (ws.getAllBlocks(false).length > 0) {
        // clear() will fire change events — absorb them as clean
        pendingCleanRef.current = true;
      }
      ws.clear();
      refreshVariablesRef.current?.();
    }
    setCurrentFilePath(null);
  };

  const newFile = () =>
    confirmIfDirty(doNewFile, { title: 'Create new file?', confirmLabel: 'Create New' });

  const pushRecent = (filePath: string) => {
    void window.doggo.addRecent(filePath);
    setRecents((prev) => [filePath, ...prev.filter((p) => p !== filePath)].slice(0, 10));
  };

  const handleOpenFile = async (filePath?: string) => {
    const result = await window.doggo.openFile(filePath);
    if (!result) {
      return;
    }
    try {
      const dom = await parsePython(result.content);
      const ws = workspaceRef.current;
      if (!ws) {
        return;
      }
      pendingCleanRef.current = true; // workspace about to change — treat it as clean baseline
      ScratchBlocks.Xml.clearWorkspaceAndLoadFromXml(dom, ws);
      refreshVariablesRef.current?.();
      setCurrentFilePath(result.filePath);
      pushRecent(result.filePath);
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
      pushRecent(savedPath);
      markClean();
    }
  };

  // ── Stable refs for IPC listeners ─────────────────────────────────────────
  const newFileRef = useRef(newFile);
  newFileRef.current = newFile;
  const handleOpenFileRef = useRef(handleOpenFile);
  handleOpenFileRef.current = handleOpenFile;
  const handleSaveFileRef = useRef(handleSaveFile);
  handleSaveFileRef.current = handleSaveFile;
  const confirmIfDirtyRef = useRef(confirmIfDirty);
  confirmIfDirtyRef.current = confirmIfDirty;

  useEffect(() => {
    void window.doggo.getRecents().then(setRecents);
    window.doggo.onMenuNewFile(() => newFileRef.current());
    window.doggo.onMenuOpenFile(() =>
      confirmIfDirtyRef.current(() => void handleOpenFileRef.current(), {
        title: 'Open file?',
        confirmLabel: 'Open',
      }),
    );
    window.doggo.onMenuSaveFile(() => void handleSaveFileRef.current(false));
    window.doggo.onMenuSaveFileAs(() => void handleSaveFileRef.current(true));
    window.doggo.onMenuOpenRecent((filePath) =>
      confirmIfDirtyRef.current(() => void handleOpenFileRef.current(filePath), {
        title: 'Open recent file?',
        confirmLabel: 'Open',
      }),
    );
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    parseError,
    setParseError,
    newFile,
    discardConfirmOpen,
    discardContext,
    confirmDiscard,
    cancelDiscard,
    openFile: () =>
      confirmIfDirty(() => void handleOpenFileRef.current(), {
        title: 'Open file?',
        confirmLabel: 'Open',
      }),
    saveFile: () => void handleSaveFileRef.current(false),
    saveFileAs: () => void handleSaveFileRef.current(true),
    recents,
    openRecent: (filePath: string) =>
      confirmIfDirty(() => void handleOpenFileRef.current(filePath), {
        title: 'Open recent file?',
        confirmLabel: 'Open',
      }),
    clearRecents: () => {
      void window.doggo.clearRecents();
      setRecents([]);
    },
  };
};

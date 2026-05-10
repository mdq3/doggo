import { useEffect, useRef, useState } from 'react';
import * as ScratchBlocks from 'scratch-blocks';

import { defineBlocks } from '../blocks.js';
import { createGenerator } from '../generator.js';
import { useBlocklyWorkspace } from '../useBlocklyWorkspace.js';
import { useFileHandling } from '../useFileHandling.js';
import { useScriptRunner } from '../useScriptRunner.js';
import { useSettings } from '../useSettings.js';
import { CodePanel } from './CodePanel.js';
import { CreateVariableDialog } from './CreateVariableDialog.js';
import { ErrorDialog } from './ErrorDialog.js';
import { RenameDialog } from './RenameDialog.js';
import { SettingsDialog } from './SettingsDialog.js';
import { SplashScreen } from './SplashScreen.js';
import { Toolbar } from './Toolbar.js';
import { VariableContextMenu, type VarMenu } from './VariableContextMenu.js';

ScratchBlocks.ScratchMsgs.setLocale('en');
defineBlocks();
const pyGen = createGenerator();

export const App = () => {
  const [showSplash, setShowSplash] = useState(true);
  const [codeOpen, setCodeOpen] = useState(false);
  const [generatedCode, setGeneratedCode] = useState('# Place blocks to generate code');
  const [ctxMenu, setCtxMenu] = useState<VarMenu | null>(null);
  const [renameVarId, setRenameVarId] = useState<string | null>(null);
  const [renameName, setRenameName] = useState('');
  const [promptOpen, setPromptOpen] = useState(false);
  const promptCallbackRef = useRef<((name: string | null) => void) | null>(null);
  const [varDialog, setVarDialog] = useState(false);
  const [varName, setVarName] = useState('');
  const [settingsOpen, setSettingsOpen] = useState(false);

  const { blocklyDivRef, workspaceRef, refreshVariablesRef } = useBlocklyWorkspace({
    pyGen,
    onCodeChange: setGeneratedCode,
    onCreateVar: () => {
      setVarName('');
      setVarDialog(true);
    },
    onVarContextMenu: setCtxMenu,
  });

  const { status, errorDialog, setErrorDialog, handleRun } = useScriptRunner(workspaceRef, pyGen);
  const { parseError, setParseError, openFile, saveFile } = useFileHandling(
    workspaceRef,
    refreshVariablesRef,
    generatedCode,
  );

  const { hostname, setHostname, password, setPassword, save: saveSettings } = useSettings();

  useEffect(() => {
    ScratchBlocks.dialog.setPrompt((message, defaultValue, callback) => {
      // Blockly passes "" as defaultValue for rename — extract the current name
      // from the message which has the form 'Rename all "varName" variables to:'.
      const extracted = /"(.+)"/.exec(message)?.[1] ?? '';
      setRenameName(defaultValue || extracted);
      promptCallbackRef.current = callback;
      setPromptOpen(true);
    });
  }, []);

  const closeRenameDialog = () => {
    if (promptCallbackRef.current) {
      promptCallbackRef.current(null);
      promptCallbackRef.current = null;
    }
    setRenameVarId(null);
    setPromptOpen(false);
  };

  const handleRenameVar = () => {
    const newName = renameName.trim();
    if (!newName) {
      return;
    }
    if (renameVarId) {
      const ws = workspaceRef.current;
      const variable = ws?.getVariableMap().getVariableById(renameVarId);
      if (ws && variable) {
        ws.getVariableMap().renameVariable(variable, newName);
      }
      setRenameVarId(null);
    } else if (promptOpen && promptCallbackRef.current) {
      promptCallbackRef.current(newName);
      promptCallbackRef.current = null;
      setPromptOpen(false);
    }
  };

  const handleDeleteVar = (varId: string) => {
    const ws = workspaceRef.current;
    const variable = ws?.getVariableMap().getVariableById(varId);
    if (ws && variable) {
      ws.getVariableMap().deleteVariable(variable);
    }
    setCtxMenu(null);
  };

  const handleCreateVar = () => {
    const name = varName.trim();
    const ws = workspaceRef.current;
    if (name && ws) {
      ws.getVariableMap().createVariable(name);
      refreshVariablesRef.current?.();
    }
    setVarDialog(false);
  };

  const handleSaveSettings = async () => {
    await saveSettings();
    setSettingsOpen(false);
  };

  return (
    <>
      {showSplash && <SplashScreen onStart={() => setShowSplash(false)} />}
      <Toolbar
        status={status}
        onRun={handleRun}
        onToggleCode={() => setCodeOpen((o) => !o)}
        onOpen={openFile}
        onSave={saveFile}
        onOpenSettings={() => setSettingsOpen(true)}
      />
      <div id="main-area">
        <div id="blockly-div" ref={blocklyDivRef} onClick={() => setCtxMenu(null)} />
        <CodePanel open={codeOpen} code={generatedCode} />
      </div>

      {ctxMenu && (
        <VariableContextMenu
          menu={ctxMenu}
          onClose={() => setCtxMenu(null)}
          onRename={(varId, name) => {
            setRenameVarId(varId);
            setRenameName(name);
            setCtxMenu(null);
          }}
          onDelete={handleDeleteVar}
        />
      )}
      <RenameDialog
        open={!!(renameVarId || promptOpen)}
        name={renameName}
        onChange={setRenameName}
        onConfirm={handleRenameVar}
        onCancel={closeRenameDialog}
      />
      <CreateVariableDialog
        open={varDialog}
        name={varName}
        onChange={setVarName}
        onCreate={handleCreateVar}
        onClose={() => setVarDialog(false)}
      />
      <SettingsDialog
        open={settingsOpen}
        hostname={hostname}
        password={password}
        onChangeHostname={setHostname}
        onChangePassword={setPassword}
        onSave={handleSaveSettings}
        onClose={() => setSettingsOpen(false)}
      />
      <ErrorDialog error={errorDialog} onClose={() => setErrorDialog(null)} />
      <ErrorDialog error={parseError} onClose={() => setParseError(null)} />
    </>
  );
};

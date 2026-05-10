import { useEffect, useRef } from 'react';
import * as ScratchBlocks from 'scratch-blocks';

import { doggoTheme } from './theme.js';
import { buildToolboxItems, toolboxConfig } from './toolbox.js';

interface CodeGenerator {
  workspaceToCode(ws: ScratchBlocks.WorkspaceSvg): string;
}

interface VarMenu {
  x: number;
  y: number;
  varId: string;
  varName: string;
}

export const useBlocklyWorkspace = ({
  pyGen,
  onCodeChange,
  onCreateVar,
  onVarContextMenu,
}: {
  pyGen: CodeGenerator;
  onCodeChange: (code: string) => void;
  onCreateVar: () => void;
  onVarContextMenu: (menu: VarMenu) => void;
}) => {
  const blocklyDivRef = useRef<HTMLDivElement>(null);
  const workspaceRef = useRef<ScratchBlocks.WorkspaceSvg | null>(null);
  const refreshVariablesRef = useRef<(() => void) | null>(null);

  // Callback refs prevent stale closures in the one-time setup effect.
  const onCodeChangeRef = useRef(onCodeChange);
  onCodeChangeRef.current = onCodeChange;
  const onCreateVarRef = useRef(onCreateVar);
  onCreateVarRef.current = onCreateVar;
  const onVarContextMenuRef = useRef(onVarContextMenu);
  onVarContextMenuRef.current = onVarContextMenu;

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
      onCreateVarRef.current();
    });

    const refreshVariables = () => {
      const vars = ws.getVariableMap().getAllVariables();
      const items = buildToolboxItems(vars);
      ws.getToolbox()?.getFlyout()?.show(items);
    };
    refreshVariablesRef.current = refreshVariables;

    ws.addChangeListener((event: ScratchBlocks.Events.Abstract) => {
      onCodeChangeRef.current(pyGen.workspaceToCode(ws) || '# Place blocks to generate code');

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
      let block: ScratchBlocks.Block | null = flyout.getWorkspace().getBlockById(dataId);
      if (!block?.workspace.isFlyout) {
        return null;
      }
      // Walk up the block parent chain — handles clicks on the shadow number input
      // inside the set block, where the DOM walker resolves to math_number, not variables_set.
      while (block) {
        if (block.type === 'variables_get' || block.type === 'variables_set') {
          return block;
        }
        block = block.getParent?.() ?? null;
      }
      return null;
    };

    // Intercept right-click before Blockly starts its gesture.
    // Both pointerdown and mousedown must be stopped — they are separate event chains
    // and Scratch-Blocks listens on mousedown, so stopping only pointerdown is not enough.
    const stopRightClickOnVarBlock = (e: MouseEvent) => {
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
      onVarContextMenuRef.current({
        x: e.clientX,
        y: e.clientY,
        varId,
        varName: variable.getName(),
      });
    };

    blocklyEl.addEventListener('pointerdown', stopRightClickOnVarBlock, true);
    blocklyEl.addEventListener('mousedown', stopRightClickOnVarBlock, true);
    blocklyEl.addEventListener('contextmenu', handleContextMenu, true);

    return () => {
      observer.disconnect();
      blocklyEl.removeEventListener('pointerdown', stopRightClickOnVarBlock, true);
      blocklyEl.removeEventListener('mousedown', stopRightClickOnVarBlock, true);
      blocklyEl.removeEventListener('contextmenu', handleContextMenu, true);
      ws.dispose();
      workspaceRef.current = null;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return { blocklyDivRef, workspaceRef, refreshVariablesRef };
};

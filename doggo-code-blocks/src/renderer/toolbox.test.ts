import type * as ScratchBlocks from 'scratch-blocks';
import { describe, expect, it } from 'vite-plus/test';

import { MOTION_COMMANDS, POSE_COMMANDS, TRICK_COMMANDS } from './commands.js';
import { buildToolboxItems, toolboxConfig } from './toolbox.js';

type FlyoutItem = ScratchBlocks.utils.toolbox.FlyoutItemInfo;
type BlockItem = ScratchBlocks.utils.toolbox.BlockInfo;

const isBlock = (i: FlyoutItem): i is BlockItem => 'type' in i;
const isLabel = (i: FlyoutItem): i is ScratchBlocks.utils.toolbox.LabelInfo =>
  i.kind === 'label' && 'text' in i && !('callbackkey' in i);
const isButton = (i: FlyoutItem): i is ScratchBlocks.utils.toolbox.ButtonInfo =>
  i.kind === 'button' && 'callbackkey' in i;

const mockVar = (
  id: string,
  name: string,
): ScratchBlocks.IVariableModel<ScratchBlocks.IVariableState> => ({
  getId: () => id,
  getName: () => name,
  getType: () => '',
  setName(_: string) {
    return this;
  },
  setType(_: string) {
    return this;
  },
  getWorkspace: (): never => {
    throw new Error('not used in test');
  },
  save: (): never => {
    throw new Error('not used in test');
  },
});

describe('toolboxConfig', () => {
  it('contains a Poses category', () => {
    expect(toolboxConfig.contents.some((c) => c.name === 'Poses')).toBe(true);
  });

  it('contains a Motion category', () => {
    expect(toolboxConfig.contents.some((c) => c.name === 'Motion')).toBe(true);
  });

  it('Poses category lists every POSE_COMMAND block type', () => {
    const poses = toolboxConfig.contents.find((c) => c.name === 'Poses')!;
    const types = poses.contents.filter(isBlock).map((item) => item.type);
    for (const cmd of POSE_COMMANDS) {
      expect(types).toContain(cmd.blockType);
    }
  });

  it('contains a Tricks category', () => {
    expect(toolboxConfig.contents.some((c) => c.name === 'Tricks')).toBe(true);
  });

  it('Tricks category lists every TRICK_COMMAND block type', () => {
    const tricks = toolboxConfig.contents.find((c) => c.name === 'Tricks')!;
    const types = tricks.contents.filter(isBlock).map((item) => item.type);
    for (const cmd of TRICK_COMMANDS) {
      expect(types).toContain(cmd.blockType);
    }
  });

  it('Motion category lists every MOTION_COMMAND block type', () => {
    const motion = toolboxConfig.contents.find((c) => c.name === 'Motion')!;
    const types = motion.contents.filter(isBlock).map((item) => item.type);
    for (const cmd of MOTION_COMMANDS) {
      expect(types).toContain(cmd.blockType);
    }
  });

  it('Motion blocks include a shadow input keyed by param', () => {
    const motion = toolboxConfig.contents.find((c) => c.name === 'Motion')!;
    for (const item of motion.contents.filter(isBlock)) {
      const cmd = MOTION_COMMANDS.find((c) => c.blockType === item.type)!;
      expect(item.inputs?.[cmd.param.toUpperCase()]).toBeDefined();
    }
  });
});

describe('buildToolboxItems', () => {
  it('emits a label for each toolbox category', () => {
    const items = buildToolboxItems([]);
    const labels = items.filter(isLabel).map((i) => i.text);
    for (const cat of toolboxConfig.contents) {
      expect(labels).toContain(cat.name);
    }
  });

  it('includes Create Variable button when there are no variables', () => {
    const items = buildToolboxItems([]);
    expect(items.some((i) => isButton(i) && i.text === 'Create Variable')).toBe(true);
  });

  it('does not include variable blocks when there are no variables', () => {
    const items = buildToolboxItems([]);
    expect(items.filter(isBlock).some((i) => i.type === 'variables_set')).toBe(false);
    expect(items.filter(isBlock).some((i) => i.type === 'variables_get')).toBe(false);
  });

  it('includes one variables_set block for the first variable', () => {
    const items = buildToolboxItems([mockVar('id-1', 'x')]);
    const setBlocks = items.filter(isBlock).filter((i) => i.type === 'variables_set');
    expect(setBlocks).toHaveLength(1);
  });

  it('includes one variables_get block per variable', () => {
    const items = buildToolboxItems([mockVar('id-1', 'x'), mockVar('id-2', 'y')]);
    const getBlocks = items.filter(isBlock).filter((i) => i.type === 'variables_get');
    expect(getBlocks).toHaveLength(2);
  });

  it('variables_get block carries the variable id and name', () => {
    const items = buildToolboxItems([mockVar('id-1', 'myVar')]);
    const getBlock = items.filter(isBlock).find((i) => i.type === 'variables_get');
    expect(getBlock?.fields?.['VAR'].id).toBe('id-1');
    expect(getBlock?.fields?.['VAR'].name).toBe('myVar');
  });
});

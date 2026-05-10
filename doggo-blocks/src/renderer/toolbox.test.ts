import { describe, expect, it } from 'vitest';

import { MOTION_COMMANDS, POSE_COMMANDS } from './commands.js';
import { buildToolboxItems, toolboxConfig } from './toolbox.js';

const mockVar = (id: string, name: string) =>
  ({ getId: () => id, getName: () => name, getType: () => '' }) as any;

describe('toolboxConfig', () => {
  it('contains a Poses category', () => {
    expect(toolboxConfig.contents.some((c) => c.name === 'Poses')).toBe(true);
  });

  it('contains a Motion category', () => {
    expect(toolboxConfig.contents.some((c) => c.name === 'Motion')).toBe(true);
  });

  it('Poses category lists every POSE_COMMAND block type', () => {
    const poses = toolboxConfig.contents.find((c) => c.name === 'Poses')!;
    const types = poses.contents.map((item: any) => item.type);
    for (const cmd of POSE_COMMANDS) {
      expect(types).toContain(cmd.blockType);
    }
  });

  it('Motion category lists every MOTION_COMMAND block type', () => {
    const motion = toolboxConfig.contents.find((c) => c.name === 'Motion')!;
    const types = motion.contents.map((item: any) => item.type);
    for (const cmd of MOTION_COMMANDS) {
      expect(types).toContain(cmd.blockType);
    }
  });

  it('Motion blocks include a shadow input keyed by param', () => {
    const motion = toolboxConfig.contents.find((c) => c.name === 'Motion')!;
    for (const item of motion.contents as any[]) {
      const cmd = MOTION_COMMANDS.find((c) => c.blockType === item.type)!;
      expect(item.inputs[cmd.param.toUpperCase()]).toBeDefined();
    }
  });
});

describe('buildToolboxItems', () => {
  it('emits a label for each toolbox category', () => {
    const items = buildToolboxItems([]);
    const labels = items.filter((i: any) => i.kind === 'label').map((i: any) => i.text);
    for (const cat of toolboxConfig.contents) {
      expect(labels).toContain(cat.name);
    }
  });

  it('includes Create Variable button when there are no variables', () => {
    const items = buildToolboxItems([]);
    expect(items.some((i: any) => i.kind === 'button' && i.text === 'Create Variable')).toBe(true);
  });

  it('does not include variable blocks when there are no variables', () => {
    const items = buildToolboxItems([]);
    expect(items.some((i: any) => i.type === 'variables_set')).toBe(false);
    expect(items.some((i: any) => i.type === 'variables_get')).toBe(false);
  });

  it('includes one variables_set block for the first variable', () => {
    const items = buildToolboxItems([mockVar('id-1', 'x')]);
    const setBlocks = items.filter((i: any) => i.type === 'variables_set');
    expect(setBlocks).toHaveLength(1);
  });

  it('includes one variables_get block per variable', () => {
    const items = buildToolboxItems([mockVar('id-1', 'x'), mockVar('id-2', 'y')]);
    const getBlocks = items.filter((i: any) => i.type === 'variables_get');
    expect(getBlocks).toHaveLength(2);
  });

  it('variables_get block carries the variable id and name', () => {
    const items = buildToolboxItems([mockVar('id-1', 'myVar')]);
    const getBlock = items.find((i: any) => i.type === 'variables_get') as any;
    expect(getBlock.fields.VAR.id).toBe('id-1');
    expect(getBlock.fields.VAR.name).toBe('myVar');
  });
});

import { describe, expect, it } from 'vite-plus/test';

import { MOTION_COMMANDS, POSE_COMMANDS, TRICK_COMMANDS } from './commands.js';

describe('POSE_COMMANDS', () => {
  it('block types are unique', () => {
    const types = POSE_COMMANDS.map((c) => c.blockType);
    expect(new Set(types).size).toBe(types.length);
  });

  it('function names are unique', () => {
    const names = POSE_COMMANDS.map((c) => c.functionName);
    expect(new Set(names).size).toBe(names.length);
  });

  it('importLine references functionName', () => {
    for (const cmd of POSE_COMMANDS) {
      expect(cmd.importLine).toContain(cmd.functionName);
    }
  });
});

describe('TRICK_COMMANDS', () => {
  it('block types are unique', () => {
    const types = TRICK_COMMANDS.map((c) => c.blockType);
    expect(new Set(types).size).toBe(types.length);
  });

  it('function names are unique', () => {
    const names = TRICK_COMMANDS.map((c) => c.functionName);
    expect(new Set(names).size).toBe(names.length);
  });

  it('importLine references functionName', () => {
    for (const cmd of TRICK_COMMANDS) {
      expect(cmd.importLine).toContain(cmd.functionName);
    }
  });
});

describe('MOTION_COMMANDS', () => {
  it('param is lowercase', () => {
    for (const cmd of MOTION_COMMANDS) {
      expect(cmd.param).toBe(cmd.param.toLowerCase());
    }
  });

  it('importLine references functionName', () => {
    for (const cmd of MOTION_COMMANDS) {
      expect(cmd.importLine).toContain(cmd.functionName);
    }
  });

  it('block types are unique across all commands', () => {
    const all = [...POSE_COMMANDS, ...TRICK_COMMANDS, ...MOTION_COMMANDS].map((c) => c.blockType);
    expect(new Set(all).size).toBe(all.length);
  });

  it('function names are unique across all commands', () => {
    const all = [...POSE_COMMANDS, ...TRICK_COMMANDS, ...MOTION_COMMANDS].map(
      (c) => c.functionName,
    );
    expect(new Set(all).size).toBe(all.length);
  });
});

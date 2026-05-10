import { describe, expect, it } from 'vite-plus/test';

import { createGenerator } from './generator.js';
import type { MinBlock, MinWorkspace } from './generator.js';

// ── Mock block builders ───────────────────────────────────────────────────────
// scratch-blocks' blockToCode needs: isEnabled, isInsertionMarker, type,
// outputConnection (null for statements, non-null for value blocks),
// getFieldValue, getField, getInputTargetBlock, getInput, nextConnection.

type MockBlock = MinBlock;

const baseBlock = (type: string, extra: Partial<MockBlock> = {}): MockBlock => ({
  type,
  isEnabled: () => true,
  isInsertionMarker: () => false,
  outputConnection: null,
  suppressPrefixSuffix: false,
  getFieldValue: () => '',
  getField: () => null,
  getInputTargetBlock: () => null,
  getInput: () => ({}), // non-null = input slot exists
  nextConnection: null,
  ...extra,
});

// Statement block — may have value inputs and a next block
const stmtBlock = (
  type: string,
  inputs: Record<string, MockBlock> = {},
  next?: MockBlock,
): MockBlock =>
  baseBlock(type, {
    outputConnection: null,
    getInputTargetBlock: (name) => inputs[name] ?? null,
    nextConnection: next ? { targetBlock: () => next } : null,
  });

// Value block — returns [code, order]; outputConnection must be non-null
const numBlock = (n: number): MockBlock =>
  baseBlock('math_number', {
    outputConnection: {},
    getFieldValue: (name) => (name === 'NUM' ? String(n) : ''),
  });

const varGetBlock = (varName: string): MockBlock =>
  baseBlock('variables_get', {
    outputConnection: {},
    getField: (name) => (name === 'VAR' ? { getText: () => varName } : null),
  });

// Workspace mock — only top-level hat blocks are used by workspaceToCode
const workspace = (...topBlocks: MockBlock[]): MinWorkspace => ({ getTopBlocks: () => topBlocks });

// Hat block: workspaceToCode reads hat.nextConnection.targetBlock() for the body
const hat = (first?: MockBlock): MockBlock =>
  baseBlock('doggo_on_start', {
    nextConnection: first ? { targetBlock: () => first } : null,
  });

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('createGenerator', () => {
  it('returns empty string for a workspace with no top blocks', () => {
    const gen = createGenerator();
    expect(gen.workspaceToCode(workspace())).toBe('');
  });

  it('ignores top-level blocks that are not doggo_on_start', () => {
    const gen = createGenerator();
    expect(gen.workspaceToCode(workspace(stmtBlock('doggo_stand')))).toBe('');
  });

  it('returns empty string for a hat block with no body', () => {
    const gen = createGenerator();
    expect(gen.workspaceToCode(workspace(hat()))).toBe('');
  });

  it('generates stand() with its import', () => {
    const gen = createGenerator();
    const out = gen.workspaceToCode(workspace(hat(stmtBlock('doggo_stand'))));
    expect(out).toBe('from poses import stand\n\nstand()\n');
  });

  it('generates sit() with its import', () => {
    const gen = createGenerator();
    const out = gen.workspaceToCode(workspace(hat(stmtBlock('doggo_sit'))));
    expect(out).toBe('from poses import sit\n\nsit()\n');
  });

  it('generates rest() with its import', () => {
    const gen = createGenerator();
    const out = gen.workspaceToCode(workspace(hat(stmtBlock('doggo_rest'))));
    expect(out).toBe('from poses import rest\n\nrest()\n');
  });

  it('chains consecutive statement blocks', () => {
    const gen = createGenerator();
    const sit = stmtBlock('doggo_sit');
    const stand = stmtBlock('doggo_stand', {}, sit);
    const out = gen.workspaceToCode(workspace(hat(stand)));
    expect(out).toContain('stand()\n');
    expect(out).toContain('sit()\n');
    expect(out.indexOf('stand()')).toBeLessThan(out.indexOf('sit()'));
  });

  it('deduplicates and sorts imports from multiple blocks', () => {
    const gen = createGenerator();
    const sit = stmtBlock('doggo_sit');
    const stand = stmtBlock('doggo_stand', {}, sit);
    const out = gen.workspaceToCode(workspace(hat(stand)));
    const header = out.split('\n\n')[0];
    const lines = header.split('\n');
    expect(lines).toHaveLength(2);
    expect(lines).toEqual(lines.toSorted());
  });

  it('generates walk(steps=2) with connected value', () => {
    const gen = createGenerator();
    const block = stmtBlock('doggo_walk', { STEPS: numBlock(2) });
    const out = gen.workspaceToCode(workspace(hat(block)));
    expect(out).toContain('walk(steps=2)');
    expect(out).toContain('from gaits.walk import walk');
  });

  it('falls back to steps=1 when no STEPS value is connected', () => {
    const gen = createGenerator();
    const out = gen.workspaceToCode(workspace(hat(stmtBlock('doggo_walk'))));
    expect(out).toContain('walk(steps=1)');
  });

  it('generates time.sleep() for doggo_wait', () => {
    const gen = createGenerator();
    const block = stmtBlock('doggo_wait', { SECONDS: numBlock(3) });
    const out = gen.workspaceToCode(workspace(hat(block)));
    expect(out).toContain('import time');
    expect(out).toContain('time.sleep(3)');
  });

  it('generates for loop for doggo_repeat', () => {
    const gen = createGenerator();
    const body = stmtBlock('doggo_stand');
    const block = stmtBlock('doggo_repeat', { TIMES: numBlock(5), SUBSTACK: body });
    const out = gen.workspaceToCode(workspace(hat(block)));
    expect(out).toContain('for _ in range(5):');
    expect(out).toContain('    stand()');
  });

  it('falls back to pass when doggo_repeat body is empty', () => {
    const gen = createGenerator();
    const block = stmtBlock('doggo_repeat', { TIMES: numBlock(3) });
    const out = gen.workspaceToCode(workspace(hat(block)));
    expect(out).toContain('for _ in range(3):');
    expect(out).toContain('    pass');
  });

  it('generates while True for doggo_forever', () => {
    const gen = createGenerator();
    const body = stmtBlock('doggo_stand');
    const block = stmtBlock('doggo_forever', { SUBSTACK: body });
    const out = gen.workspaceToCode(workspace(hat(block)));
    expect(out).toContain('while True:');
    expect(out).toContain('    stand()');
  });

  it('generates variable assignment for variables_set', () => {
    const gen = createGenerator();
    const block = baseBlock('variables_set', {
      outputConnection: null,
      getField: (name) => (name === 'VAR' ? { getText: () => 'x' } : null),
      getInputTargetBlock: (name) => (name === 'VALUE' ? numBlock(42) : null),
    });
    const out = gen.workspaceToCode(workspace(hat(block)));
    expect(out).toContain('x = 42');
  });

  it('generates arithmetic expression for doggo_add', () => {
    const gen = createGenerator();
    const addBlock = baseBlock('doggo_add', {
      outputConnection: {},
      getInputTargetBlock: (name) => (name === 'A' ? numBlock(1) : numBlock(2)),
    });
    const setBlock = baseBlock('variables_set', {
      outputConnection: null,
      getField: (name) => (name === 'VAR' ? { getText: () => 'n' } : null),
      getInputTargetBlock: (name) => (name === 'VALUE' ? addBlock : null),
    });
    const out = gen.workspaceToCode(workspace(hat(setBlock)));
    expect(out).toContain('(1) + (2)');
  });

  it('generates comparison expression for doggo_lt', () => {
    const gen = createGenerator();
    const ltBlock = baseBlock('doggo_lt', {
      outputConnection: {},
      getInputTargetBlock: (name) => (name === 'A' ? numBlock(0) : numBlock(10)),
    });
    const setBlock = baseBlock('variables_set', {
      outputConnection: null,
      getField: (name) => (name === 'VAR' ? { getText: () => 'r' } : null),
      getInputTargetBlock: (name) => (name === 'VALUE' ? ltBlock : null),
    });
    const out = gen.workspaceToCode(workspace(hat(setBlock)));
    expect(out).toContain('(0) < (10)');
  });

  it('generates not expression for doggo_not', () => {
    const gen = createGenerator();
    const notBlock = baseBlock('doggo_not', {
      outputConnection: {},
      getInputTargetBlock: (name) => (name === 'VALUE' ? varGetBlock('flag') : null),
    });
    const setBlock = baseBlock('variables_set', {
      outputConnection: null,
      getField: (name) => (name === 'VAR' ? { getText: () => 'r' } : null),
      getInputTargetBlock: (name) => (name === 'VALUE' ? notBlock : null),
    });
    const out = gen.workspaceToCode(workspace(hat(setBlock)));
    expect(out).toContain('not (flag)');
  });

  it('clears imports between workspaceToCode calls', () => {
    const gen = createGenerator();
    gen.workspaceToCode(workspace(hat(stmtBlock('doggo_stand'))));
    const out = gen.workspaceToCode(workspace(hat()));
    expect(out).toBe('');
  });
});

import * as ScratchBlocks from 'scratch-blocks';

import { MOTION_COMMANDS, POSE_COMMANDS } from './commands.js';

// Python code generator using Blockly 12's forBlock API.
// Imports are accumulated per-generation and prepended as a header block.

// Minimal structural interfaces — matches what blockToCode actually reads from blocks.
// ScratchBlocks.Block and WorkspaceSvg both satisfy these, as does MockBlock in tests.
export interface MinBlock {
  type: string;
  isEnabled(): boolean;
  isInsertionMarker(): boolean;
  outputConnection: object | null;
  suppressPrefixSuffix: boolean | null;
  getFieldValue(name: string): string;
  getField(name: string): { getText(): string } | null;
  getInputTargetBlock(name: string): MinBlock | null;
  getInput(name: string): object | null;
  nextConnection: { targetBlock(): MinBlock | null } | null;
}

export interface MinWorkspace {
  getTopBlocks(ordered?: boolean): MinBlock[];
}

export const createGenerator = (): { workspaceToCode(workspace: MinWorkspace): string } => {
  const gen = new ScratchBlocks.CodeGenerator('Python');
  gen.INDENT = '    ';

  const imports = new Set<string>();

  // Blockly 12's default scrub_() just returns the current block's code and
  // ignores nextConnection. Override it to chain connected statement blocks.
  gen.scrub_ = function (block: ScratchBlocks.Block, code: string, opt_thisOnly?: boolean): string {
    const next = block.nextConnection?.targetBlock() ?? null;
    const nextCode = opt_thisOnly || !next ? '' : this.blockToCode(next);
    return code + nextCode;
  };

  // ─── UTILITY BLOCKS ───────────────────────────────────────────────────────
  gen.forBlock['math_number'] = (block) => [block.getFieldValue('NUM'), 0];

  // getFieldValue('VAR') returns the variable UUID — use getText() for the name.
  gen.forBlock['variables_get'] = (block) => [block.getField('VAR')!.getText(), 0];

  gen.forBlock['variables_set'] = (block, g) => {
    const name = block.getField('VAR')!.getText();
    const val = g.valueToCode(block, 'VALUE', 0) || '0';
    return `${name} = ${val}\n`;
  };

  // ─── ON START HAT ─────────────────────────────────────────────────────────
  gen.forBlock['doggo_on_start'] = () => '';

  // ─── POSES ────────────────────────────────────────────────────────────────
  for (const def of POSE_COMMANDS) {
    gen.forBlock[def.blockType] = () => {
      imports.add(def.importLine);
      return `${def.functionName}()\n`;
    };
  }

  // ─── MOTION ───────────────────────────────────────────────────────────────
  for (const def of MOTION_COMMANDS) {
    gen.forBlock[def.blockType] = (block, g) => {
      imports.add(def.importLine);
      const val = g.valueToCode(block, def.param.toUpperCase(), 0) || '1';
      return `${def.functionName}(${def.param}=${val})\n`;
    };
  }

  // ─── CONTROL ──────────────────────────────────────────────────────────────
  gen.forBlock['doggo_repeat'] = (block, g) => {
    const times = g.valueToCode(block, 'TIMES', 0) || '1';
    const body = g.statementToCode(block, 'SUBSTACK') || `${g.INDENT}pass\n`;
    return `for _ in range(${times}):\n${body}`;
  };

  gen.forBlock['doggo_forever'] = (block, g) => {
    const body = g.statementToCode(block, 'SUBSTACK') || `${g.INDENT}pass\n`;
    return `while True:\n${body}`;
  };

  gen.forBlock['doggo_while'] = (block, g) => {
    const cond = g.valueToCode(block, 'CONDITION', 0) || 'True';
    const body = g.statementToCode(block, 'SUBSTACK') || `${g.INDENT}pass\n`;
    return `while ${cond}:\n${body}`;
  };

  gen.forBlock['doggo_wait'] = (block, g) => {
    imports.add('import time');
    const secs = g.valueToCode(block, 'SECONDS', 0) || '1';
    return `time.sleep(${secs})\n`;
  };

  // ─── OPERATORS: COMPARISON ────────────────────────────────────────────────
  const compOps: Record<string, string> = {
    doggo_lt: '<',
    doggo_gt: '>',
    doggo_eq: '==',
    doggo_lte: '<=',
    doggo_gte: '>=',
  };
  for (const [type, op] of Object.entries(compOps)) {
    gen.forBlock[type] = (block, g) => {
      const a = g.valueToCode(block, 'A', 0) || '0';
      const b = g.valueToCode(block, 'B', 0) || '0';
      return [`(${a}) ${op} (${b})`, 0];
    };
  }

  // ─── OPERATORS: LOGICAL ───────────────────────────────────────────────────
  gen.forBlock['doggo_and'] = (block, g) => {
    const a = g.valueToCode(block, 'A', 0) || 'True';
    const b = g.valueToCode(block, 'B', 0) || 'True';
    return [`(${a}) and (${b})`, 0];
  };
  gen.forBlock['doggo_or'] = (block, g) => {
    const a = g.valueToCode(block, 'A', 0) || 'True';
    const b = g.valueToCode(block, 'B', 0) || 'True';
    return [`(${a}) or (${b})`, 0];
  };
  gen.forBlock['doggo_not'] = (block, g) => {
    const val = g.valueToCode(block, 'VALUE', 0) || 'True';
    return [`not (${val})`, 0];
  };

  // ─── OPERATORS: ARITHMETIC ────────────────────────────────────────────────
  const mathOps: Record<string, string> = {
    doggo_add: '+',
    doggo_sub: '-',
    doggo_mul: '*',
    doggo_div: '/',
  };
  for (const [type, op] of Object.entries(mathOps)) {
    gen.forBlock[type] = (block, g) => {
      const a = g.valueToCode(block, 'A', 0) || '0';
      const b = g.valueToCode(block, 'B', 0) || '0';
      return [`(${a}) ${op} (${b})`, 0];
    };
  }

  // Only generate code for block stacks that start with a doggo_on_start hat.
  // Disconnected blocks are silently ignored — same model as Scratch.
  const workspaceToCode = (workspace: MinWorkspace): string => {
    imports.clear();
    const body = workspace
      .getTopBlocks(true)
      .filter((b) => b.type === 'doggo_on_start')
      .map((hat) => {
        const first = hat.nextConnection?.targetBlock() ?? null;
        // eslint-disable-next-line typescript-eslint/no-unsafe-type-assertion -- MinBlock satisfies Block for all methods blockToCode calls
        return first ? gen.blockToCode(first as unknown as ScratchBlocks.Block) : '';
      })
      .join('');
    if (!imports.size) {
      return body;
    }
    return `${[...imports].toSorted().join('\n')}\n\n${body}`;
  };

  return { workspaceToCode };
};

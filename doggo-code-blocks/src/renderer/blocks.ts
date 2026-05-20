import * as ScratchBlocks from 'scratch-blocks';

import { MOTION_COMMANDS, POSE_COMMANDS } from './commands.js';

// All block definitions for Doggo Code Blocks.
// Style names must exist in Themes.Zelos (our theme) with full colour values.
// Zelos styles: list_blocks=purple, logic_blocks=blue, loop_blocks=teal,
//               math_blocks=green, variable_blocks=orange

class WorkspaceOnlyFieldVariable extends ScratchBlocks.FieldVariable {
  // Suppress dropdown only on variables_get in the flyout; variables_set keeps
  // the dropdown so users can pick which variable to assign.
  private isFlyoutGet(): boolean {
    const b = this.getSourceBlock();
    return !!(b?.workspace.isFlyout && b.type === 'variables_get');
  }

  override isClickableInFlyout(autoClosingFlyout: boolean): boolean {
    return this.isFlyoutGet() ? false : !autoClosingFlyout;
  }

  protected override createSVGArrow_(): void {
    if (this.isFlyoutGet()) {
      return;
    }
    super.createSVGArrow_();
  }

  protected override createTextArrow_(): void {
    if (this.isFlyoutGet()) {
      return;
    }
    super.createTextArrow_();
  }
}

export const defineBlocks = (): void => {
  const { Blocks, FieldNumber } = ScratchBlocks;
  const FieldVariable = WorkspaceOnlyFieldVariable;

  // ─── HAT BLOCK ────────────────────────────────────────────────────────────
  Blocks['doggo_on_start'] = {
    init(this: ScratchBlocks.Block) {
      this.appendDummyInput().appendField('when ▶ clicked');
      this.setNextStatement(true);
      this.setStyle('hat_blocks');
    },
  };

  // ─── UTILITY BLOCKS ───────────────────────────────────────────────────────
  // math_number: scratch-blocks registers its own, but we override it so it
  // uses our doggo_operators style and has a clean number-only UI.
  Blocks['math_number'] = {
    init(this: ScratchBlocks.Block) {
      this.appendDummyInput().appendField(new FieldNumber(0), 'NUM');
      this.setOutput(true, 'Number');
      this.setStyle('colour_blocks');
    },
  };

  Blocks['variables_get'] = {
    init(this: ScratchBlocks.Block) {
      this.appendDummyInput().appendField(new FieldVariable('i'), 'VAR');
      this.setOutput(true, null);
      this.setStyle('variable_blocks');
    },
  };

  Blocks['variables_set'] = {
    init(this: ScratchBlocks.Block) {
      this.appendDummyInput()
        .appendField('set')
        .appendField(new FieldVariable('i'), 'VAR')
        .appendField('to');
      this.appendValueInput('VALUE');
      this.setInputsInline(true);
      this.setPreviousStatement(true);
      this.setNextStatement(true);
      this.setStyle('variable_blocks');
    },
  };

  // ─── POSES ────────────────────────────────────────────────────────────────
  for (const def of POSE_COMMANDS) {
    Blocks[def.blockType] = {
      init(this: ScratchBlocks.Block) {
        this.appendDummyInput().appendField(def.label);
        this.setPreviousStatement(true);
        this.setNextStatement(true);
        this.setStyle(def.style);
      },
    };
  }

  // ─── MOTION ───────────────────────────────────────────────────────────────
  for (const def of MOTION_COMMANDS) {
    Blocks[def.blockType] = {
      init(this: ScratchBlocks.Block) {
        this.appendValueInput(def.param.toUpperCase()).setCheck('Number').appendField(def.label);
        this.appendDummyInput().appendField(def.param);
        this.setInputsInline(true);
        this.setPreviousStatement(true);
        this.setNextStatement(true);
        this.setStyle(def.style);
      },
    };
  }

  // ─── CONTROL ──────────────────────────────────────────────────────────────
  Blocks['doggo_repeat'] = {
    init(this: ScratchBlocks.Block) {
      this.appendValueInput('TIMES').setCheck('Number').appendField('repeat');
      this.appendDummyInput().appendField('times');
      this.appendStatementInput('SUBSTACK');
      this.setInputsInline(true);
      this.setPreviousStatement(true);
      this.setNextStatement(true);
      this.setStyle('loop_blocks');
    },
  };

  Blocks['doggo_forever'] = {
    init(this: ScratchBlocks.Block) {
      this.appendDummyInput().appendField('forever');
      this.appendStatementInput('SUBSTACK');
      this.setPreviousStatement(true);
      // No setNextStatement — nothing can follow forever
      this.setStyle('loop_blocks');
    },
  };

  Blocks['doggo_while'] = {
    init(this: ScratchBlocks.Block) {
      this.appendValueInput('CONDITION').setCheck('Boolean').appendField('while');
      this.appendStatementInput('SUBSTACK');
      this.setInputsInline(true);
      this.setPreviousStatement(true);
      this.setNextStatement(true);
      this.setStyle('loop_blocks');
    },
  };

  Blocks['doggo_wait'] = {
    init(this: ScratchBlocks.Block) {
      this.appendValueInput('SECONDS').setCheck('Number').appendField('wait');
      this.appendDummyInput().appendField('seconds');
      this.setInputsInline(true);
      this.setPreviousStatement(true);
      this.setNextStatement(true);
      this.setStyle('loop_blocks');
    },
  };

  // ─── OPERATORS: COMPARISON ────────────────────────────────────────────────
  for (const [type, op] of [
    ['doggo_lt', '<'],
    ['doggo_gt', '>'],
    ['doggo_eq', '='],
    ['doggo_lte', '≤'],
    ['doggo_gte', '≥'],
  ]) {
    Blocks[type] = {
      init(this: ScratchBlocks.Block) {
        this.appendValueInput('A');
        this.appendDummyInput().appendField(op);
        this.appendValueInput('B');
        this.setInputsInline(true);
        this.setOutput(true, 'Boolean');
        this.setStyle('colour_blocks');
      },
    };
  }

  // ─── OPERATORS: LOGICAL ───────────────────────────────────────────────────
  Blocks['doggo_and'] = {
    init(this: ScratchBlocks.Block) {
      this.appendValueInput('A').setCheck('Boolean');
      this.appendDummyInput().appendField('and');
      this.appendValueInput('B').setCheck('Boolean');
      this.setInputsInline(true);
      this.setOutput(true, 'Boolean');
      this.setStyle('colour_blocks');
    },
  };

  Blocks['doggo_or'] = {
    init(this: ScratchBlocks.Block) {
      this.appendValueInput('A').setCheck('Boolean');
      this.appendDummyInput().appendField('or');
      this.appendValueInput('B').setCheck('Boolean');
      this.setInputsInline(true);
      this.setOutput(true, 'Boolean');
      this.setStyle('colour_blocks');
    },
  };

  Blocks['doggo_not'] = {
    init(this: ScratchBlocks.Block) {
      this.appendValueInput('VALUE').setCheck('Boolean').appendField('not');
      this.setInputsInline(true);
      this.setOutput(true, 'Boolean');
      this.setStyle('colour_blocks');
    },
  };

  // ─── OPERATORS: ARITHMETIC ────────────────────────────────────────────────
  for (const [type, op] of [
    ['doggo_add', '+'],
    ['doggo_sub', '-'],
    ['doggo_mul', '×'],
    ['doggo_div', '÷'],
  ]) {
    Blocks[type] = {
      init(this: ScratchBlocks.Block) {
        this.appendValueInput('A').setCheck('Number');
        this.appendDummyInput().appendField(op);
        this.appendValueInput('B').setCheck('Number');
        this.setInputsInline(true);
        this.setOutput(true, 'Number');
        this.setStyle('colour_blocks');
      },
    };
  }
};

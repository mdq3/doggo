import * as ScratchBlocks from 'scratch-blocks';

// All block definitions for Doggo Blocks.
// Style names must exist in Themes.Zelos (our theme) with full colour values.
// Zelos styles: list_blocks=purple, logic_blocks=blue, loop_blocks=teal,
//               math_blocks=green, variable_blocks=orange

export function defineBlocks(): void {
  const { Blocks, FieldNumber, FieldVariable } = ScratchBlocks;

  // ─── HAT BLOCK ────────────────────────────────────────────────────────────
  Blocks['doggo_on_start'] = {
    init(this: ScratchBlocks.Block) {
      this.appendDummyInput().appendField('when ▶ run');
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
      this.setStyle('math_blocks');
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
  for (const [type, label] of [
    ['doggo_stand', 'stand'],
    ['doggo_sit', 'sit'],
    ['doggo_rest', 'rest'],
  ] as const) {
    Blocks[type] = {
      init(this: ScratchBlocks.Block) {
        this.appendDummyInput().appendField(label);
        this.setPreviousStatement(true);
        this.setNextStatement(true);
        this.setStyle('list_blocks');
      },
    };
  }

  // ─── MOTION ───────────────────────────────────────────────────────────────
  for (const [type, label] of [
    ['doggo_walk', 'walk'],
    ['doggo_walk_back', 'walk back'],
    ['doggo_turn_left', 'turn left'],
    ['doggo_turn_right', 'turn right'],
    ['doggo_pivot_left', 'pivot left'],
    ['doggo_pivot_right', 'pivot right'],
    ['doggo_trot', 'trot'],
  ] as const) {
    Blocks[type] = {
      init(this: ScratchBlocks.Block) {
        this.appendValueInput('STEPS').setCheck('Number').appendField(label);
        this.appendDummyInput().appendField('steps');
        this.setInputsInline(true);
        this.setPreviousStatement(true);
        this.setNextStatement(true);
        this.setStyle('logic_blocks');
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
  ] as const) {
    Blocks[type] = {
      init(this: ScratchBlocks.Block) {
        this.appendValueInput('A');
        this.appendDummyInput().appendField(op);
        this.appendValueInput('B');
        this.setInputsInline(true);
        this.setOutput(true, 'Boolean');
        this.setStyle('math_blocks');
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
      this.setStyle('math_blocks');
    },
  };

  Blocks['doggo_or'] = {
    init(this: ScratchBlocks.Block) {
      this.appendValueInput('A').setCheck('Boolean');
      this.appendDummyInput().appendField('or');
      this.appendValueInput('B').setCheck('Boolean');
      this.setInputsInline(true);
      this.setOutput(true, 'Boolean');
      this.setStyle('math_blocks');
    },
  };

  Blocks['doggo_not'] = {
    init(this: ScratchBlocks.Block) {
      this.appendValueInput('VALUE').setCheck('Boolean').appendField('not');
      this.setInputsInline(true);
      this.setOutput(true, 'Boolean');
      this.setStyle('math_blocks');
    },
  };

  // ─── OPERATORS: ARITHMETIC ────────────────────────────────────────────────
  for (const [type, op] of [
    ['doggo_add', '+'],
    ['doggo_sub', '-'],
    ['doggo_mul', '×'],
    ['doggo_div', '÷'],
  ] as const) {
    Blocks[type] = {
      init(this: ScratchBlocks.Block) {
        this.appendValueInput('A').setCheck('Number');
        this.appendDummyInput().appendField(op);
        this.appendValueInput('B').setCheck('Number');
        this.setInputsInline(true);
        this.setOutput(true, 'Number');
        this.setStyle('math_blocks');
      },
    };
  }
}

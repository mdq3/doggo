import type * as ScratchBlocks from 'scratch-blocks';

import { MOTION_COMMANDS, POSE_COMMANDS } from './commands.js';

type FlyoutItem = ScratchBlocks.utils.toolbox.FlyoutItemInfo;
type Category = { colour: string; contents: FlyoutItem[]; kind: string; name: string };

const numShadow = (n = 1) => ({ shadow: { type: 'math_number', fields: { NUM: n } } });

export const toolboxConfig: { kind: string; contents: Category[] } = {
  kind: 'categoryToolbox',
  contents: [
    {
      kind: 'category',
      name: 'Events',
      colour: '#FFBF00',
      contents: [{ kind: 'block', type: 'doggo_on_start' }],
    },
    {
      kind: 'category',
      name: 'Poses',
      colour: '#9966FF',
      contents: POSE_COMMANDS.map((def) => ({ kind: 'block', type: def.blockType })),
    },
    {
      kind: 'category',
      name: 'Motion',
      colour: '#4C97FF',
      contents: MOTION_COMMANDS.map((def) => ({
        kind: 'block',
        type: def.blockType,
        inputs: { [def.param.toUpperCase()]: numShadow(def.defaultValue) },
      })),
    },
    {
      kind: 'category',
      name: 'Control',
      colour: '#0fBD8C',
      contents: [
        { kind: 'block', type: 'doggo_repeat', inputs: { TIMES: numShadow(10) } },
        { kind: 'block', type: 'doggo_forever' },
        { kind: 'block', type: 'doggo_while' },
        { kind: 'block', type: 'doggo_wait', inputs: { SECONDS: numShadow(1) } },
      ],
    },
    {
      kind: 'category',
      name: 'Operators',
      colour: '#CF63CF',
      contents: [
        { kind: 'block', type: 'doggo_add', inputs: { A: numShadow(0), B: numShadow(0) } },
        { kind: 'block', type: 'doggo_sub', inputs: { A: numShadow(0), B: numShadow(0) } },
        { kind: 'block', type: 'doggo_mul', inputs: { A: numShadow(0), B: numShadow(0) } },
        { kind: 'block', type: 'doggo_div', inputs: { A: numShadow(0), B: numShadow(1) } },

        { kind: 'block', type: 'doggo_lt', inputs: { A: numShadow(0), B: numShadow(50) } },
        { kind: 'block', type: 'doggo_gt', inputs: { A: numShadow(0), B: numShadow(50) } },
        { kind: 'block', type: 'doggo_eq', inputs: { A: numShadow(0), B: numShadow(0) } },
        { kind: 'block', type: 'doggo_lte', inputs: { A: numShadow(0), B: numShadow(50) } },
        { kind: 'block', type: 'doggo_gte', inputs: { A: numShadow(0), B: numShadow(50) } },

        { kind: 'block', type: 'doggo_and' },
        { kind: 'block', type: 'doggo_or' },
        { kind: 'block', type: 'doggo_not' },
      ],
    },
    {
      kind: 'category',
      name: 'Variables',
      colour: '#FF8C1A',
      contents: [{ kind: 'button', text: 'Create Variable', callbackkey: 'CREATE_VARIABLE' }],
    },
  ],
};

export const buildToolboxItems = (
  vars: ScratchBlocks.IVariableModel<ScratchBlocks.IVariableState>[],
): ScratchBlocks.utils.toolbox.FlyoutItemInfoArray => {
  const firstVar = vars[0];
  const varBlocks = [
    ...(firstVar
      ? [
          {
            kind: 'block',
            type: 'variables_set',
            fields: {
              VAR: { id: firstVar.getId(), name: firstVar.getName(), type: firstVar.getType() },
            },
            inputs: { VALUE: numShadow(0) },
          },
        ]
      : []),
    ...vars.map((v) => ({
      kind: 'block',
      type: 'variables_get',
      fields: { VAR: { id: v.getId(), name: v.getName(), type: v.getType() } },
    })),
  ];

  return toolboxConfig.contents.flatMap((cat): ScratchBlocks.utils.toolbox.FlyoutItemInfo[] => {
    const label = { kind: 'label', text: cat.name };
    if (cat.name === 'Variables') {
      const button = { kind: 'button', text: 'Create Variable', callbackkey: 'CREATE_VARIABLE' };
      return [label, button, ...varBlocks];
    }
    return [label, ...cat.contents];
  });
};

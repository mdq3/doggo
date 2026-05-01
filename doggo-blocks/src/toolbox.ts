function numShadow(n = 1) {
  return { shadow: { type: 'math_number', fields: { NUM: n } } };
}

export const toolboxConfig = {
  kind: 'categoryToolbox',
  contents: [
    {
      kind: 'category',
      name: 'Events',
      colour: '#FFAB19',
      contents: [
        { kind: 'block', type: 'doggo_on_start' },
      ],
    },
    {
      kind: 'category',
      name: 'Poses',
      colour: '#9966FF',
      contents: [
        { kind: 'block', type: 'doggo_stand' },
        { kind: 'block', type: 'doggo_sit' },
        { kind: 'block', type: 'doggo_rest' },
      ],
    },
    {
      kind: 'category',
      name: 'Motion',
      colour: '#4C97FF',
      contents: [
        { kind: 'block', type: 'doggo_walk',        inputs: { STEPS: numShadow(2) } },
        { kind: 'block', type: 'doggo_walk_back',   inputs: { STEPS: numShadow(2) } },
        { kind: 'block', type: 'doggo_turn_left',   inputs: { STEPS: numShadow(2) } },
        { kind: 'block', type: 'doggo_turn_right',  inputs: { STEPS: numShadow(2) } },
        { kind: 'block', type: 'doggo_pivot_left',  inputs: { STEPS: numShadow(2) } },
        { kind: 'block', type: 'doggo_pivot_right', inputs: { STEPS: numShadow(2) } },
        { kind: 'block', type: 'doggo_trot',        inputs: { STEPS: numShadow(2) } },
      ],
    },
    {
      kind: 'category',
      name: 'Control',
      colour: '#FFAB19',
      contents: [
        { kind: 'block', type: 'doggo_repeat',  inputs: { TIMES:   numShadow(10) } },
        { kind: 'block', type: 'doggo_forever' },
        { kind: 'block', type: 'doggo_while' },
        { kind: 'block', type: 'doggo_wait',   inputs: { SECONDS: numShadow(1) } },
      ],
    },
    {
      kind: 'category',
      name: 'Operators',
      colour: '#59C059',
      contents: [
        { kind: 'block', type: 'doggo_add', inputs: { A: numShadow(0), B: numShadow(0) } },
        { kind: 'block', type: 'doggo_sub', inputs: { A: numShadow(0), B: numShadow(0) } },
        { kind: 'block', type: 'doggo_mul', inputs: { A: numShadow(0), B: numShadow(0) } },
        { kind: 'block', type: 'doggo_div', inputs: { A: numShadow(0), B: numShadow(1) } },

        { kind: 'block', type: 'doggo_lt',  inputs: { A: numShadow(0), B: numShadow(50) } },
        { kind: 'block', type: 'doggo_gt',  inputs: { A: numShadow(0), B: numShadow(50) } },
        { kind: 'block', type: 'doggo_eq',  inputs: { A: numShadow(0), B: numShadow(0) } },
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
      custom: 'VARIABLE',
      colour: '#FF8C1A',
    },
  ],
};

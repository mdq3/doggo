import { describe, expect, it, vi } from 'vite-plus/test';

// Redirect ?url imports to absolute filesystem paths.
// Parser.init uses the path directly via Emscripten's fs; Language.load uses
// fetch(), which our polyfill in vitest.setup.ts intercepts for .wasm files.
vi.mock('web-tree-sitter/tree-sitter.wasm?url', () => ({
  default: `${process.cwd()}/node_modules/web-tree-sitter/tree-sitter.wasm`,
}));
vi.mock('tree-sitter-python/tree-sitter-python.wasm?url', () => ({
  default: `${process.cwd()}/node_modules/tree-sitter-python/tree-sitter-python.wasm`,
}));

import { ParseError, parsePython } from './pythonParser.js';

const block = (el: Element, type: string) => el.querySelector(`block[type="${type}"]`);

describe('parsePython', () => {
  it('wraps output in a doggo_on_start hat block', async () => {
    const el = await parsePython('');
    expect(block(el, 'doggo_on_start')).toBeTruthy();
  });

  it('returns no body blocks for empty input', async () => {
    const el = await parsePython('');
    expect(block(el, 'doggo_on_start')!.querySelector('next')).toBeNull();
  });

  it('skips import statements', async () => {
    const el = await parsePython('from poses import stand\nimport time\n');
    expect(block(el, 'doggo_on_start')!.querySelector('next')).toBeNull();
  });

  it('parses stand()', async () => {
    const el = await parsePython('stand()\n');
    expect(block(el, 'doggo_stand')).toBeTruthy();
  });

  it('parses sit()', async () => {
    const el = await parsePython('sit()\n');
    expect(block(el, 'doggo_sit')).toBeTruthy();
  });

  it('parses rest()', async () => {
    const el = await parsePython('rest()\n');
    expect(block(el, 'doggo_rest')).toBeTruthy();
  });

  it('parses walk(steps=3) and carries the step value', async () => {
    const el = await parsePython('walk(steps=3)\n');
    const b = block(el, 'doggo_walk');
    expect(b).toBeTruthy();
    expect(
      b!.querySelector('value[name="STEPS"] block[type="math_number"] field[name="NUM"]')!
        .textContent,
    ).toBe('3');
  });

  it('parses trot_forward(steps=1)', async () => {
    const el = await parsePython('trot_forward(steps=1)\n');
    expect(block(el, 'doggo_trot')).toBeTruthy();
  });

  it('parses for _ in range(5) into doggo_repeat', async () => {
    const el = await parsePython('for _ in range(5):\n    stand()\n');
    expect(block(el, 'doggo_repeat')).toBeTruthy();
  });

  it('parses while True into doggo_forever', async () => {
    const el = await parsePython('while True:\n    stand()\n');
    expect(block(el, 'doggo_forever')).toBeTruthy();
  });

  it('parses while <condition> into doggo_while', async () => {
    const el = await parsePython('x = 1\nwhile x > 0:\n    stand()\n');
    expect(block(el, 'doggo_while')).toBeTruthy();
  });

  it('parses time.sleep(2) into doggo_wait', async () => {
    const el = await parsePython('time.sleep(2)\n');
    expect(block(el, 'doggo_wait')).toBeTruthy();
  });

  it('parses x = 5 into variables_set', async () => {
    const el = await parsePython('x = 5\n');
    expect(block(el, 'variables_set')).toBeTruthy();
  });

  it('emits a <variables> element for each unique variable', async () => {
    const el = await parsePython('x = 1\ny = 2\n');
    expect(el.querySelectorAll('variables > variable')).toHaveLength(2);
  });

  it('reuses the same variable id for the same name', async () => {
    const el = await parsePython('x = 1\nx = 2\n');
    expect(el.querySelectorAll('variables > variable')).toHaveLength(1);
  });

  it('chains consecutive statements via <next> elements', async () => {
    const el = await parsePython('stand()\nsit()\n');
    expect(block(el, 'doggo_stand')!.querySelector('next block[type="doggo_sit"]')).toBeTruthy();
  });

  it('parses (a) + (b) into doggo_add', async () => {
    const el = await parsePython('x = (1) + (2)\n');
    expect(block(el, 'doggo_add')).toBeTruthy();
  });

  it('parses (a) < (b) into doggo_lt', async () => {
    const el = await parsePython('x = (1) < (2)\n');
    expect(block(el, 'doggo_lt')).toBeTruthy();
  });

  it('throws ParseError for an unknown function call', async () => {
    await expect(parsePython('unknown_fn()\n')).rejects.toBeInstanceOf(ParseError);
  });

  it('throws ParseError for a for loop not using range()', async () => {
    await expect(parsePython('for x in [1, 2]:\n    stand()\n')).rejects.toBeInstanceOf(ParseError);
  });

  it('throws ParseError for a standalone expression', async () => {
    await expect(parsePython('1 + 2\n')).rejects.toBeInstanceOf(ParseError);
  });

  it('includes the line number in a ParseError', async () => {
    const err = await parsePython('stand()\nunknown_fn()\n').catch((e) => e);
    expect(err).toBeInstanceOf(ParseError);
    if (err instanceof ParseError) {
      expect(err.line).toBe(2);
    }
  });
});

import '@testing-library/jest-dom';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

// Language.load() calls fetch() to load the Python grammar WASM. In the test
// environment there is no dev server, so we intercept absolute file paths and
// read them from disk directly.
const realFetch = globalThis.fetch;

globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
  const url = input.toString();
  if (url.endsWith('.wasm') && !url.startsWith('http')) {
    const data = readFileSync(url.startsWith('/') ? url : resolve(url));
    return new Response(data, {
      status: 200,
      headers: { 'content-type': 'application/wasm' },
    });
  }
  return realFetch(input, init);
};

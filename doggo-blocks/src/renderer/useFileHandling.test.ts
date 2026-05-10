import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vite-plus/test';

import { useFileHandling } from './useFileHandling.js';

// Minimal window.doggo mock — only the methods useFileHandling calls
const makeDoggo = () => ({
  onMenuNewFile: vi.fn(),
  onMenuOpenFile: vi.fn(),
  onMenuSaveFile: vi.fn(),
  onMenuSaveFileAs: vi.fn(),
  onMenuOpenRecent: vi.fn(),
  onBeforeQuit: vi.fn(),
  confirmQuit: vi.fn(),
  getRecents: vi.fn().mockResolvedValue([]),
  setTitle: vi.fn(),
  openFile: vi.fn(),
  saveFile: vi.fn(),
  addRecent: vi.fn(),
  clearRecents: vi.fn(),
});

describe('useFileHandling', () => {
  let doggo: ReturnType<typeof makeDoggo>;
  let triggerBeforeQuit: () => void;

  beforeEach(() => {
    doggo = makeDoggo();
    doggo.onBeforeQuit.mockImplementation((cb: () => void) => {
      triggerBeforeQuit = cb;
    });
    Object.assign(window, { doggo });
  });

  const render = (code = '# initial') =>
    renderHook(
      ({ generatedCode }: { generatedCode: string }) =>
        useFileHandling({ current: null }, { current: null }, generatedCode),
      { initialProps: { generatedCode: code } },
    );

  it('registers an onBeforeQuit handler on mount', () => {
    render();
    expect(doggo.onBeforeQuit).toHaveBeenCalledOnce();
  });

  it('calls confirmQuit immediately when the file is clean', () => {
    render();

    act(() => {
      triggerBeforeQuit();
    });

    expect(doggo.confirmQuit).toHaveBeenCalledOnce();
  });

  it('shows confirm dialog with quit context when the file is dirty', () => {
    const { result, rerender } = render('# initial');

    act(() => {
      rerender({ generatedCode: '# changed' });
    });
    act(() => {
      triggerBeforeQuit();
    });

    expect(result.current.discardConfirmOpen).toBe(true);
    expect(result.current.discardContext).toMatchObject({
      title: 'Quit without saving?',
      confirmLabel: 'Quit',
    });
    expect(doggo.confirmQuit).not.toHaveBeenCalled();
  });

  it('calls confirmQuit when user confirms on a dirty file', () => {
    const { result, rerender } = render('# initial');

    act(() => {
      rerender({ generatedCode: '# changed' });
    });
    act(() => {
      triggerBeforeQuit();
    });
    act(() => {
      result.current.confirmDiscard();
    });

    expect(doggo.confirmQuit).toHaveBeenCalledOnce();
  });

  it('does not call confirmQuit when user cancels on a dirty file', () => {
    const { result, rerender } = render('# initial');

    act(() => {
      rerender({ generatedCode: '# changed' });
    });
    act(() => {
      triggerBeforeQuit();
    });
    act(() => {
      result.current.cancelDiscard();
    });

    expect(doggo.confirmQuit).not.toHaveBeenCalled();
  });

  it('closes the confirm dialog after cancel', () => {
    const { result, rerender } = render('# initial');

    act(() => {
      rerender({ generatedCode: '# changed' });
    });
    act(() => {
      triggerBeforeQuit();
    });
    act(() => {
      result.current.cancelDiscard();
    });

    expect(result.current.discardConfirmOpen).toBe(false);
  });
});

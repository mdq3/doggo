import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vite-plus/test';

import { Toolbar } from './Toolbar.js';

describe('Toolbar', () => {
  const defaults = {
    status: '',
    onRun: vi.fn(),
    onToggleCode: vi.fn(),
    onNew: vi.fn(),
    onOpen: vi.fn(),
    onSave: vi.fn(),
    onSaveAs: vi.fn(),
    onOpenSettings: vi.fn(),
    recents: [],
    onOpenRecent: vi.fn(),
    onClearRecents: vi.fn(),
  };

  it('renders the Run button', () => {
    render(<Toolbar {...defaults} />);
    expect(screen.getByRole('button', { name: /Run/ })).toBeInTheDocument();
  });

  it('renders the Code button', () => {
    render(<Toolbar {...defaults} />);
    expect(screen.getByRole('button', { name: /Code/ })).toBeInTheDocument();
  });

  it('calls onRun when Run is clicked', () => {
    const onRun = vi.fn();
    render(<Toolbar {...defaults} onRun={onRun} />);
    fireEvent.click(screen.getByRole('button', { name: /Run/ }));
    expect(onRun).toHaveBeenCalledOnce();
  });

  it('calls onToggleCode when Code is clicked', () => {
    const onToggleCode = vi.fn();
    render(<Toolbar {...defaults} onToggleCode={onToggleCode} />);
    fireEvent.click(screen.getByRole('button', { name: /Code/ }));
    expect(onToggleCode).toHaveBeenCalledOnce();
  });

  it('shows status text', () => {
    render(<Toolbar {...defaults} status="Running…" />);
    expect(screen.getByText('Running…')).toBeInTheDocument();
  });

  it('dropdown is not visible initially', () => {
    render(<Toolbar {...defaults} />);
    expect(screen.queryByRole('button', { name: /New/ })).toBeNull();
  });

  it('opens the dropdown when the menu button is clicked', () => {
    render(<Toolbar {...defaults} />);
    fireEvent.click(screen.getByTitle('Menu'));
    expect(screen.getByRole('button', { name: /New/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Open$/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Save$/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Settings/ })).toBeInTheDocument();
  });

  it('calls onNew and closes the menu when New is clicked', () => {
    const onNew = vi.fn();
    render(<Toolbar {...defaults} onNew={onNew} />);
    fireEvent.click(screen.getByTitle('Menu'));
    fireEvent.click(screen.getByRole('button', { name: /New/ }));
    expect(onNew).toHaveBeenCalledOnce();
    expect(screen.queryByRole('button', { name: /New/ })).toBeNull();
  });

  it('calls onOpenSettings and closes the menu when Settings is clicked', () => {
    const onOpenSettings = vi.fn();
    render(<Toolbar {...defaults} onOpenSettings={onOpenSettings} />);
    fireEvent.click(screen.getByTitle('Menu'));
    fireEvent.click(screen.getByRole('button', { name: /Settings/ }));
    expect(onOpenSettings).toHaveBeenCalledOnce();
    expect(screen.queryByRole('button', { name: /Settings/ })).toBeNull();
  });

  it('closes the menu when the overlay is clicked', () => {
    const { container } = render(<Toolbar {...defaults} />);
    fireEvent.click(screen.getByTitle('Menu'));
    expect(screen.getByRole('button', { name: /New/ })).toBeInTheDocument();
    fireEvent.click(container.querySelector('.menu-overlay')!);
    expect(screen.queryByRole('button', { name: /New/ })).toBeNull();
  });
});

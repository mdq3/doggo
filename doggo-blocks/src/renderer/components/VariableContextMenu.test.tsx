import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { VariableContextMenu } from './VariableContextMenu.js';

describe('VariableContextMenu', () => {
  const menu = { x: 100, y: 200, varId: 'id-1', varName: 'myVar' };

  it('renders a Rename button', () => {
    render(
      <VariableContextMenu menu={menu} onClose={vi.fn()} onRename={vi.fn()} onDelete={vi.fn()} />,
    );
    expect(screen.getByRole('button', { name: 'Rename' })).toBeInTheDocument();
  });

  it('renders a Delete button', () => {
    render(
      <VariableContextMenu menu={menu} onClose={vi.fn()} onRename={vi.fn()} onDelete={vi.fn()} />,
    );
    expect(screen.getByRole('button', { name: 'Delete' })).toBeInTheDocument();
  });

  it('calls onRename with the variable id and name', () => {
    const onRename = vi.fn();
    render(
      <VariableContextMenu menu={menu} onClose={vi.fn()} onRename={onRename} onDelete={vi.fn()} />,
    );
    fireEvent.click(screen.getByRole('button', { name: 'Rename' }));
    expect(onRename).toHaveBeenCalledWith('id-1', 'myVar');
  });

  it('calls onDelete with the variable id', () => {
    const onDelete = vi.fn();
    render(
      <VariableContextMenu menu={menu} onClose={vi.fn()} onRename={vi.fn()} onDelete={onDelete} />,
    );
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));
    expect(onDelete).toHaveBeenCalledWith('id-1');
  });

  it('calls onClose when the overlay is clicked', () => {
    const onClose = vi.fn();
    const { container } = render(
      <VariableContextMenu menu={menu} onClose={onClose} onRename={vi.fn()} onDelete={vi.fn()} />,
    );
    fireEvent.click(container.firstChild as Element);
    expect(onClose).toHaveBeenCalledOnce();
  });
});

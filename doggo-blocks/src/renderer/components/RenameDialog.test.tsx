import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { RenameDialog } from './RenameDialog.js';

describe('RenameDialog', () => {
  const defaults = {
    open: true,
    name: 'myVar',
    onChange: vi.fn(),
    onConfirm: vi.fn(),
    onCancel: vi.fn(),
  };

  it('renders null when open is false', () => {
    render(<RenameDialog {...defaults} open={false} />);
    expect(screen.queryByText('Rename variable')).toBeNull();
  });

  it('renders the heading', () => {
    render(<RenameDialog {...defaults} />);
    expect(screen.getByText('Rename variable')).toBeInTheDocument();
  });

  it('shows the current name in the input', () => {
    render(<RenameDialog {...defaults} />);
    expect(screen.getByRole('textbox')).toHaveValue('myVar');
  });

  it('calls onChange when the input changes', () => {
    const onChange = vi.fn();
    render(<RenameDialog {...defaults} onChange={onChange} />);
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'newName' } });
    expect(onChange).toHaveBeenCalledWith('newName');
  });

  it('calls onConfirm when Enter is pressed', () => {
    const onConfirm = vi.fn();
    render(<RenameDialog {...defaults} onConfirm={onConfirm} />);
    fireEvent.keyDown(screen.getByRole('textbox'), { key: 'Enter' });
    expect(onConfirm).toHaveBeenCalledOnce();
  });

  it('calls onCancel when Escape is pressed', () => {
    const onCancel = vi.fn();
    render(<RenameDialog {...defaults} onCancel={onCancel} />);
    fireEvent.keyDown(screen.getByRole('textbox'), { key: 'Escape' });
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it('disables the OK button when name is blank', () => {
    render(<RenameDialog {...defaults} name="" />);
    expect(screen.getByRole('button', { name: 'OK' })).toBeDisabled();
  });
});

import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { CreateVariableDialog } from './CreateVariableDialog.js';

describe('CreateVariableDialog', () => {
  const defaults = { open: true, name: '', onChange: vi.fn(), onCreate: vi.fn(), onClose: vi.fn() };

  it('renders null when open is false', () => {
    render(<CreateVariableDialog {...defaults} open={false} />);
    expect(screen.queryByText('New variable')).toBeNull();
  });

  it('renders the heading', () => {
    render(<CreateVariableDialog {...defaults} />);
    expect(screen.getByText('New variable')).toBeInTheDocument();
  });

  it('input has the correct placeholder', () => {
    render(<CreateVariableDialog {...defaults} />);
    expect(screen.getByPlaceholderText('Variable name')).toBeInTheDocument();
  });

  it('calls onChange when the input changes', () => {
    const onChange = vi.fn();
    render(<CreateVariableDialog {...defaults} onChange={onChange} />);
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'x' } });
    expect(onChange).toHaveBeenCalledWith('x');
  });

  it('calls onCreate when Enter is pressed', () => {
    const onCreate = vi.fn();
    render(<CreateVariableDialog {...defaults} name="x" onCreate={onCreate} />);
    fireEvent.keyDown(screen.getByRole('textbox'), { key: 'Enter' });
    expect(onCreate).toHaveBeenCalledOnce();
  });

  it('calls onClose when Escape is pressed', () => {
    const onClose = vi.fn();
    render(<CreateVariableDialog {...defaults} onClose={onClose} />);
    fireEvent.keyDown(screen.getByRole('textbox'), { key: 'Escape' });
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('disables the OK button when name is blank', () => {
    render(<CreateVariableDialog {...defaults} name="" />);
    expect(screen.getByRole('button', { name: 'OK' })).toBeDisabled();
  });
});

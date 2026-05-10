import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vite-plus/test';

import { ConfirmDialog } from './ConfirmDialog.js';

describe('ConfirmDialog', () => {
  const defaults = {
    open: true,
    title: 'Are you sure?',
    message: 'This cannot be undone.',
    onConfirm: vi.fn(),
    onCancel: vi.fn(),
  };

  it('renders null when open is false', () => {
    render(<ConfirmDialog {...defaults} open={false} />);
    expect(screen.queryByText('Are you sure?')).toBeNull();
  });

  it('renders the title', () => {
    render(<ConfirmDialog {...defaults} />);
    expect(screen.getByText('Are you sure?')).toBeInTheDocument();
  });

  it('renders the message', () => {
    render(<ConfirmDialog {...defaults} />);
    expect(screen.getByText('This cannot be undone.')).toBeInTheDocument();
  });

  it('defaults confirm button label to "Confirm"', () => {
    render(<ConfirmDialog {...defaults} />);
    expect(screen.getByRole('button', { name: 'Confirm' })).toBeInTheDocument();
  });

  it('uses the custom confirmLabel', () => {
    render(<ConfirmDialog {...defaults} confirmLabel="Delete" />);
    expect(screen.getByRole('button', { name: 'Delete' })).toBeInTheDocument();
  });

  it('calls onConfirm when confirm button is clicked', () => {
    const onConfirm = vi.fn();
    render(<ConfirmDialog {...defaults} onConfirm={onConfirm} />);
    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }));
    expect(onConfirm).toHaveBeenCalledOnce();
  });

  it('calls onCancel when cancel button is clicked', () => {
    const onCancel = vi.fn();
    render(<ConfirmDialog {...defaults} onCancel={onCancel} />);
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(onCancel).toHaveBeenCalledOnce();
  });
});

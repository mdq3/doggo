import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { ErrorDialog } from './ErrorDialog.js';

describe('ErrorDialog', () => {
  it('renders null when error is null', () => {
    render(<ErrorDialog error={null} onClose={vi.fn()} />);
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('renders the error title', () => {
    render(<ErrorDialog error={{ title: 'Run failed', body: 'oops' }} onClose={vi.fn()} />);
    expect(screen.getByText('Run failed')).toBeInTheDocument();
  });

  it('renders the error body', () => {
    render(
      <ErrorDialog error={{ title: 'Run failed', body: 'stack trace here' }} onClose={vi.fn()} />,
    );
    expect(screen.getByText('stack trace here')).toBeInTheDocument();
  });

  it('renders the detail line when provided', () => {
    render(
      <ErrorDialog
        error={{ title: 'Run failed', detail: 'Exit code 1', body: 'oops' }}
        onClose={vi.fn()}
      />,
    );
    expect(screen.getByText('Exit code 1')).toBeInTheDocument();
  });

  it('omits the detail line when not provided', () => {
    const { container } = render(
      <ErrorDialog error={{ title: 'Run failed', body: 'oops' }} onClose={vi.fn()} />,
    );
    expect(container.querySelector('.error-exit-code')).toBeNull();
  });

  it('calls onClose when OK is clicked', () => {
    const onClose = vi.fn();
    render(<ErrorDialog error={{ title: 'Run failed', body: 'oops' }} onClose={onClose} />);
    fireEvent.click(screen.getByRole('button', { name: 'OK' }));
    expect(onClose).toHaveBeenCalledOnce();
  });
});

import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vite-plus/test';

import { Dialog } from './Dialog.js';

describe('Dialog', () => {
  it('renders null when open is false', () => {
    render(
      <Dialog open={false} onClose={vi.fn()} buttons={null}>
        content
      </Dialog>,
    );
    expect(screen.queryByText('content')).toBeNull();
  });

  it('renders children when open is true', () => {
    render(
      <Dialog open onClose={vi.fn()} buttons={null}>
        content
      </Dialog>,
    );
    expect(screen.getByText('content')).toBeInTheDocument();
  });

  it('renders buttons inside the button container', () => {
    render(
      <Dialog open onClose={vi.fn()} buttons={<button>OK</button>}>
        content
      </Dialog>,
    );
    expect(screen.getByRole('button', { name: 'OK' })).toBeInTheDocument();
  });

  it('calls onClose when the backdrop is clicked', () => {
    const onClose = vi.fn();
    const { container } = render(
      <Dialog open onClose={onClose} buttons={null}>
        content
      </Dialog>,
    );
    fireEvent.click(container.querySelector('.dialog-backdrop')!);
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('does not call onClose when the dialog body is clicked', () => {
    const onClose = vi.fn();
    render(
      <Dialog open onClose={onClose} buttons={null}>
        content
      </Dialog>,
    );
    fireEvent.click(screen.getByText('content'));
    expect(onClose).not.toHaveBeenCalled();
  });

  it('applies an extra className to the dialog container', () => {
    const { container } = render(
      <Dialog open onClose={vi.fn()} buttons={null} className="extra">
        content
      </Dialog>,
    );
    expect(container.querySelector('.dialog.extra')).toBeInTheDocument();
  });
});

import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vite-plus/test';

import { SplashScreen } from './SplashScreen.js';

describe('SplashScreen', () => {
  it('renders the app title', () => {
    render(<SplashScreen onStart={vi.fn()} />);
    expect(screen.getByText('doggo code blocks')).toBeInTheDocument();
  });

  it('renders the Start Coding button', () => {
    render(<SplashScreen onStart={vi.fn()} />);
    expect(screen.getByRole('button', { name: 'Start Coding' })).toBeInTheDocument();
  });

  it('calls onStart when the button is clicked', () => {
    const onStart = vi.fn();
    render(<SplashScreen onStart={onStart} />);
    fireEvent.click(screen.getByRole('button', { name: 'Start Coding' }));
    expect(onStart).toHaveBeenCalledOnce();
  });
});

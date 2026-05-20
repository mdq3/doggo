import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vite-plus/test';

import { SettingsDialog } from './SettingsDialog.js';

describe('SettingsDialog', () => {
  const defaults = {
    open: true,
    hostname: 'doggo.local',
    password: 'doggo',
    onChangeHostname: vi.fn(),
    onChangePassword: vi.fn(),
    onSave: vi.fn(),
    onClose: vi.fn(),
  };

  it('renders null when open is false', () => {
    render(<SettingsDialog {...defaults} open={false} />);
    expect(screen.queryByText('Settings')).toBeNull();
  });

  it('renders the heading', () => {
    render(<SettingsDialog {...defaults} />);
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('shows the current hostname', () => {
    render(<SettingsDialog {...defaults} />);
    expect(screen.getByDisplayValue('doggo.local')).toBeInTheDocument();
  });

  it('shows the current password', () => {
    render(<SettingsDialog {...defaults} />);
    expect(screen.getByDisplayValue('doggo')).toBeInTheDocument();
  });

  it('calls onChangeHostname when hostname input changes', () => {
    const onChangeHostname = vi.fn();
    render(<SettingsDialog {...defaults} onChangeHostname={onChangeHostname} />);
    fireEvent.change(screen.getByDisplayValue('doggo.local'), { target: { value: 'robot.local' } });
    expect(onChangeHostname).toHaveBeenCalledWith('robot.local');
  });

  it('calls onChangePassword when password input changes', () => {
    const onChangePassword = vi.fn();
    render(<SettingsDialog {...defaults} onChangePassword={onChangePassword} />);
    fireEvent.change(screen.getByDisplayValue('doggo'), { target: { value: 'secret' } });
    expect(onChangePassword).toHaveBeenCalledWith('secret');
  });

  it('calls onSave when Enter is pressed in an input', () => {
    const onSave = vi.fn();
    render(<SettingsDialog {...defaults} onSave={onSave} />);
    fireEvent.keyDown(screen.getByDisplayValue('doggo.local'), { key: 'Enter' });
    expect(onSave).toHaveBeenCalledOnce();
  });

  it('calls onClose when Escape is pressed in an input', () => {
    const onClose = vi.fn();
    render(<SettingsDialog {...defaults} onClose={onClose} />);
    fireEvent.keyDown(screen.getByDisplayValue('doggo.local'), { key: 'Escape' });
    expect(onClose).toHaveBeenCalledOnce();
  });
});

interface SettingsDialogProps {
  open: boolean;
  hostname: string;
  password: string;
  onChangeHostname: (v: string) => void;
  onChangePassword: (v: string) => void;
  onSave: () => void;
  onClose: () => void;
}

export const SettingsDialog = ({
  open,
  hostname,
  password,
  onChangeHostname,
  onChangePassword,
  onSave,
  onClose,
}: SettingsDialogProps) => {
  if (!open) return null;

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') onSave();
    if (e.key === 'Escape') onClose();
  };

  return (
    <div className="dialog-overlay" onClick={onClose}>
      <div className="dialog" onClick={(e) => e.stopPropagation()}>
        <h3>Settings</h3>
        <label className="settings-label">
          Robot hostname
          <input
            autoFocus
            value={hostname}
            placeholder="doggo.local"
            onChange={(e) => onChangeHostname(e.target.value)}
            onKeyDown={handleKeyDown}
          />
        </label>
        <label className="settings-label">
          Robot password
          <input
            value={password}
            placeholder="doggo"
            onChange={(e) => onChangePassword(e.target.value)}
            onKeyDown={handleKeyDown}
          />
        </label>
        <div className="dialog-buttons">
          <button onClick={onSave}>Save</button>
          <button onClick={onClose}>Cancel</button>
        </div>
      </div>
    </div>
  );
};

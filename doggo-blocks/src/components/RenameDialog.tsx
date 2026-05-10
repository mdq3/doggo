interface RenameDialogProps {
  open: boolean;
  name: string;
  onChange: (name: string) => void;
  onConfirm: () => void;
  onCancel: () => void;
}

export const RenameDialog = ({ open, name, onChange, onConfirm, onCancel }: RenameDialogProps) => {
  if (!open) {
    return null;
  }
  return (
    <div className="dialog-overlay" onClick={onCancel}>
      <div className="dialog" onClick={(e) => e.stopPropagation()}>
        <h3>Rename variable</h3>
        <input
          autoFocus
          value={name}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              onConfirm();
            }
            if (e.key === 'Escape') {
              onCancel();
            }
          }}
        />
        <div className="dialog-buttons">
          <button onClick={onConfirm} disabled={!name.trim()}>
            OK
          </button>
          <button onClick={onCancel}>Cancel</button>
        </div>
      </div>
    </div>
  );
};

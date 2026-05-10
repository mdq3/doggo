interface CreateVariableDialogProps {
  open: boolean;
  name: string;
  onChange: (name: string) => void;
  onCreate: () => void;
  onClose: () => void;
}

export const CreateVariableDialog = ({
  open,
  name,
  onChange,
  onCreate,
  onClose,
}: CreateVariableDialogProps) => {
  if (!open) {
    return null;
  }
  return (
    <div className="dialog-overlay" onClick={onClose}>
      <div className="dialog" onClick={(e) => e.stopPropagation()}>
        <h3>New variable</h3>
        <input
          autoFocus
          placeholder="Variable name"
          value={name}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              onCreate();
            }
            if (e.key === 'Escape') {
              onClose();
            }
          }}
        />
        <div className="dialog-buttons">
          <button onClick={onCreate} disabled={!name.trim()}>
            OK
          </button>
          <button onClick={onClose}>Cancel</button>
        </div>
      </div>
    </div>
  );
};

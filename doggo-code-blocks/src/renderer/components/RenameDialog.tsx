import { Dialog } from './Dialog.js';

interface RenameDialogProps {
  open: boolean;
  name: string;
  onChange: (name: string) => void;
  onConfirm: () => void;
  onCancel: () => void;
}

export const RenameDialog = ({ open, name, onChange, onConfirm, onCancel }: RenameDialogProps) => (
  <Dialog
    open={open}
    onClose={onCancel}
    buttons={
      <>
        <button onClick={onConfirm} disabled={!name.trim()}>
          OK
        </button>
        <button onClick={onCancel}>Cancel</button>
      </>
    }
  >
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
  </Dialog>
);

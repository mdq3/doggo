import { AlertTriangle } from 'lucide-react';

import { Dialog } from './Dialog.js';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export const ConfirmDialog = ({
  open,
  title,
  message,
  confirmLabel = 'Confirm',
  onConfirm,
  onCancel,
}: ConfirmDialogProps) => (
  <Dialog
    open={open}
    onClose={onCancel}
    buttons={
      <>
        <button onClick={onConfirm}>{confirmLabel}</button>
        <button onClick={onCancel}>Cancel</button>
      </>
    }
  >
    <h3>
      <AlertTriangle size={16} style={{ color: '#fab387', flexShrink: 0 }} />
      {title}
    </h3>
    <p style={{ fontSize: 14, color: '#a6adc8' }}>{message}</p>
  </Dialog>
);

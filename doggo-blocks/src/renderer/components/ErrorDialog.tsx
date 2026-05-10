import { AlertTriangle } from 'lucide-react';

import './ErrorDialog.css';
import { Dialog } from './Dialog.js';

export interface ErrorData {
  title: string;
  detail?: string;
  body: string;
}

interface ErrorDialogProps {
  error: ErrorData | null;
  onClose: () => void;
}

export const ErrorDialog = ({ error, onClose }: ErrorDialogProps) => {
  if (!error) {
    return null;
  }
  return (
    <Dialog
      open
      onClose={onClose}
      className="error-dialog"
      buttons={<button onClick={onClose}>OK</button>}
    >
      <h3>
        <AlertTriangle size={16} style={{ color: '#f38ba8', flexShrink: 0 }} />
        {error.title}
      </h3>
      {error.detail !== undefined && <p className="error-exit-code">{error.detail}</p>}
      <pre className="error-output">{error.body || '(no output)'}</pre>
    </Dialog>
  );
};

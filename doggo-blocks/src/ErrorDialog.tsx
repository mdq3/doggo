import { AlertTriangle } from 'lucide-react';

interface ErrorDialogProps {
  error: { exitCode: number; output: string } | null;
  onClose: () => void;
}

export const ErrorDialog = ({ error, onClose }: ErrorDialogProps) => {
  if (!error) return null;
  return (
    <div className="dialog-overlay" onClick={onClose}>
      <div className="dialog error-dialog" onClick={(e) => e.stopPropagation()}>
        <h3>
          <AlertTriangle size={16} style={{ color: '#f38ba8', flexShrink: 0 }} />
          Run failed
        </h3>
        <p className="error-exit-code">Exit code {error.exitCode}</p>
        <pre className="error-output">{error.output || '(no output)'}</pre>
        <div className="dialog-buttons">
          <button onClick={onClose}>OK</button>
        </div>
      </div>
    </div>
  );
};

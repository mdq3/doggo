import './Dialog.css';

interface DialogProps {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
  buttons: React.ReactNode;
  className?: string;
}

export const Dialog = ({ open, onClose, children, buttons, className }: DialogProps) => {
  if (!open) {
    return null;
  }
  return (
    <div className="dialog-backdrop" onClick={onClose}>
      <div
        className={className ? `dialog ${className}` : 'dialog'}
        onClick={(e) => e.stopPropagation()}
      >
        {children}
        <div className="dialog-buttons">{buttons}</div>
      </div>
    </div>
  );
};

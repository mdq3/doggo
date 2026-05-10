export interface VarMenu {
  x: number;
  y: number;
  varId: string;
  varName: string;
}

interface VariableContextMenuProps {
  menu: VarMenu;
  onClose: () => void;
  onRename: (varId: string, varName: string) => void;
  onDelete: (varId: string) => void;
}

export const VariableContextMenu = ({ menu, onClose, onRename, onDelete }: VariableContextMenuProps) => (
  <>
    <div style={{ position: 'fixed', inset: 0, zIndex: 999 }} onClick={onClose} />
    <div className="context-menu" style={{ left: menu.x, top: menu.y }}>
      <button onClick={() => onRename(menu.varId, menu.varName)}>Rename</button>
      <button onClick={() => onDelete(menu.varId)}>Delete</button>
    </div>
  </>
);

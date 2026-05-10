import { Code2, FilePlus, FolderOpen, Menu, Play, Save, Settings } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

interface ToolbarProps {
  status: string;
  onRun: () => void;
  onToggleCode: () => void;
  onNew: () => void;
  onOpen: () => void;
  onSave: () => void;
  onOpenSettings: () => void;
}

export const Toolbar = ({
  status,
  onRun,
  onToggleCode,
  onNew,
  onOpen,
  onSave,
  onOpenSettings,
}: ToolbarProps) => {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!menuOpen) {
      return;
    }
    const onMouseDown = (e: MouseEvent) => {
      if (!menuRef.current?.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', onMouseDown);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('mousedown', onMouseDown);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [menuOpen]);

  const close = () => setMenuOpen(false);

  return (
    <div id="toolbar">
      <button id="btn-run" onClick={onRun}>
        <Play size={14} /> Run
      </button>
      <span id="status">{status}</span>
      <button id="btn-code" onClick={onToggleCode} title="Toggle Python code viewer">
        <Code2 size={14} /> Code
      </button>
      <div id="burger-menu" ref={menuRef}>
        <button id="btn-menu" onClick={() => setMenuOpen((o) => !o)} title="Menu">
          <Menu size={16} />
        </button>
        {menuOpen && (
          <div id="burger-dropdown">
            <button
              onClick={() => {
                onNew();
                close();
              }}
            >
              <FilePlus size={14} /> New
            </button>
            <button
              onClick={() => {
                onOpen();
                close();
              }}
            >
              <FolderOpen size={14} /> Open
            </button>
            <button
              onClick={() => {
                onSave();
                close();
              }}
            >
              <Save size={14} /> Save
            </button>
            <hr className="menu-separator" />
            <button
              onClick={() => {
                onOpenSettings();
                close();
              }}
            >
              <Settings size={14} /> Settings
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

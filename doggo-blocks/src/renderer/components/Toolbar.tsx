import {
  ChevronLeft,
  ChevronRight,
  Code2,
  FilePlus,
  FolderOpen,
  Menu,
  Play,
  Save,
  Settings,
  Trash2,
} from 'lucide-react';
import { useEffect, useState } from 'react';

interface ToolbarProps {
  status: string;
  onRun: () => void;
  onToggleCode: () => void;
  onNew: () => void;
  onOpen: () => void;
  onSave: () => void;
  onSaveAs: () => void;
  onOpenSettings: () => void;
  recents: string[];
  onOpenRecent: (filePath: string) => void;
  onClearRecents: () => void;
}

const fileName = (p: string) => p.replace(/.*[/\\]/, '');
const dirName = (p: string) => p.replace(/[/\\][^/\\]*$/, '');

export const Toolbar = ({
  status,
  onRun,
  onToggleCode,
  onNew,
  onOpen,
  onSave,
  onSaveAs,
  onOpenSettings,
  recents,
  onOpenRecent,
  onClearRecents,
}: ToolbarProps) => {
  const [menuOpen, setMenuOpen] = useState(false);
  const [panel, setPanel] = useState<'main' | 'recents'>('main');

  useEffect(() => {
    if (!menuOpen) {
      setPanel('main');
      return;
    }
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setMenuOpen(false);
      }
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
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
      <div id="burger-menu">
        <button id="btn-menu" onClick={() => setMenuOpen((o) => !o)} title="Menu">
          <Menu size={16} />
        </button>
        {menuOpen && <div className="menu-overlay" onClick={close} />}
        {menuOpen && panel === 'main' && (
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
            <button className="menu-item-chevron" onClick={() => setPanel('recents')}>
              <span className="menu-item-chevron-label">
                <FolderOpen size={14} /> Open Recent
              </span>
              <ChevronRight size={14} />
            </button>
            <button
              onClick={() => {
                onSave();
                close();
              }}
            >
              <Save size={14} /> Save
            </button>
            <button
              onClick={() => {
                onSaveAs();
                close();
              }}
            >
              <Save size={14} /> Save As…
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
        {menuOpen && panel === 'recents' && (
          <div id="burger-dropdown" className="burger-dropdown-wide">
            <button className="menu-back" onClick={() => setPanel('main')}>
              <ChevronLeft size={14} /> Back
            </button>
            <hr className="menu-separator" />
            {recents.length === 0 ? (
              <span className="recents-empty">No recent files</span>
            ) : (
              recents.map((p) => (
                <button
                  key={p}
                  className="recent-item"
                  onClick={() => {
                    onOpenRecent(p);
                    close();
                  }}
                >
                  <span className="recent-name">{fileName(p)}</span>
                  <span className="recent-dir">{dirName(p)}</span>
                </button>
              ))
            )}
            {recents.length > 0 && (
              <>
                <hr className="menu-separator" />
                <button
                  onClick={() => {
                    onClearRecents();
                    close();
                  }}
                >
                  <Trash2 size={14} /> Clear Recents
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

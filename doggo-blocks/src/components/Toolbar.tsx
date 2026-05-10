import { Code2, Play, Settings } from 'lucide-react';

interface ToolbarProps {
  status: string;
  codeOpen: boolean;
  onRun: () => void;
  onToggleCode: () => void;
  onOpenSettings: () => void;
}

export const Toolbar = ({ status, codeOpen, onRun, onToggleCode, onOpenSettings }: ToolbarProps) => (
  <div id="toolbar">
    <button id="btn-run" onClick={onRun}>
      <Play size={14} /> Run
    </button>
    <span id="status">{status}</span>
    <button id="btn-code" onClick={onToggleCode} title="Toggle Python code viewer">
      <Code2 size={14} /> Code
    </button>
    <button id="btn-settings" onClick={onOpenSettings} title="Settings">
      <Settings size={14} />
    </button>
  </div>
);

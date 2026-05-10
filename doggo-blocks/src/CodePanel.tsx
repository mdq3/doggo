import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

export const CodePanel = ({ open, code }: { open: boolean; code: string }) => (
  <div id="code-panel" className={open ? 'open' : ''}>
    <div id="code-panel-header">
      <span>Generated Python</span>
    </div>
    <SyntaxHighlighter
      language="python"
      style={vscDarkPlus}
      customStyle={{
        margin: 0,
        flex: 1,
        fontSize: '13px',
        lineHeight: '1.6',
        background: '#1e1e2e',
        minWidth: '360px',
        height: '100%',
        overflow: 'auto',
      }}
    >
      {code}
    </SyntaxHighlighter>
  </div>
);

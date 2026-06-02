import React from 'react';
import { useWorkflowStore } from '../../store/useWorkflowStore';
import {
  X,
  Copy,
  Check,
  FileJson,
  ChevronDown,
  ChevronRight,
  Braces,
} from 'lucide-react';

interface JsonTrackerProps {
  onClose: () => void;
}

/* ─── Recursive JSON Tree Node ─── */
const JsonTreeNode: React.FC<{ label: string; value: any; depth?: number }> = ({
  label,
  value,
  depth = 0,
}) => {
  const [expanded, setExpanded] = React.useState(depth < 2);

  const isObject = value !== null && typeof value === 'object';
  const isArray = Array.isArray(value);
  const entries = isObject ? Object.entries(value) : [];
  const indent = depth * 14;

  // Determine displayed value for primitives
  const renderPrimitive = () => {
    if (value === null) return <span className="text-slate-500 italic">null</span>;
    if (typeof value === 'boolean')
      return <span className="text-purple-400">{value ? 'true' : 'false'}</span>;
    if (typeof value === 'number')
      return <span className="text-amber-400">{value}</span>;
    if (typeof value === 'string') {
      const truncated = value.length > 80 ? value.slice(0, 77) + '…' : value;
      return <span className="text-emerald-400">"{truncated}"</span>;
    }
    return <span className="text-slate-400">{String(value)}</span>;
  };

  if (!isObject) {
    return (
      <div
        className="flex items-baseline gap-1.5 py-[2px] hover:bg-slate-800/30 rounded px-1 transition-colors"
        style={{ paddingLeft: indent }}
      >
        <span className="text-blue-300 font-medium shrink-0">{label}:</span>
        {renderPrimitive()}
      </div>
    );
  }

  const bracket = isArray ? ['[', ']'] : ['{', '}'];

  return (
    <div>
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 py-[2px] hover:bg-slate-800/30 rounded px-1 w-full text-left transition-colors"
        style={{ paddingLeft: indent }}
      >
        {expanded ? (
          <ChevronDown size={10} className="text-slate-500 shrink-0" />
        ) : (
          <ChevronRight size={10} className="text-slate-500 shrink-0" />
        )}
        <span className="text-blue-300 font-medium">{label}:</span>
        <span className="text-slate-500 text-[9px]">
          {bracket[0]}
          {!expanded && (
            <span className="text-slate-600">
              {' '}…{entries.length} {isArray ? 'items' : 'keys'}{' '}
            </span>
          )}
          {!expanded && bracket[1]}
        </span>
      </button>
      {expanded && (
        <div>
          {entries.map(([k, v]) => (
            <JsonTreeNode key={k} label={isArray ? `[${k}]` : k} value={v} depth={depth + 1} />
          ))}
          <div className="text-slate-500" style={{ paddingLeft: indent + 14 }}>
            {bracket[1]}
          </div>
        </div>
      )}
    </div>
  );
};

/* ─── Main JSON Tracker Component ─── */
export const JsonTracker: React.FC<JsonTrackerProps> = ({ onClose }) => {
  const nodes = useWorkflowStore((s) => s.nodes);
  const edges = useWorkflowStore((s) => s.edges);
  const workflowName = useWorkflowStore((s) => s.workflowName);
  const workflowDescription = useWorkflowStore((s) => s.workflowDescription);
  const workflowVisibility = useWorkflowStore((s) => s.workflowVisibility);
  const getWorkflowJson = useWorkflowStore((s) => s.getWorkflowJson);

  const [mode, setMode] = React.useState<'tree' | 'raw'>('tree');
  const [copied, setCopied] = React.useState(false);

  const workflowJson = React.useMemo(
    () => getWorkflowJson(),
    [getWorkflowJson, nodes, edges, workflowName, workflowDescription, workflowVisibility]
  );
  const rawJson = React.useMemo(
    () => JSON.stringify(workflowJson, null, 2),
    [workflowJson]
  );

  const handleCopy = () => {
    navigator.clipboard.writeText(rawJson);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="absolute bottom-0 left-0 right-0 h-[45%] z-30 flex flex-col border-t border-slate-800 bg-slate-950/95 backdrop-blur-xl shadow-[0_-10px_30px_-5px_rgba(0,0,0,0.6)] animate-slide-up">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-800/80 bg-slate-900/40 shrink-0">
        <div className="flex items-center gap-2">
          <FileJson className="text-primary" size={14} />
          <h3 className="text-[11px] font-bold text-white uppercase tracking-wider">
            Live Workflow JSON
          </h3>
          <span className="text-[9px] bg-primary/10 text-primary px-2 py-0.5 rounded-full border border-primary/20 font-semibold">
            {workflowJson.nodes.length} nodes · {workflowJson.edges.length} edges
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Mode toggle */}
          <div className="flex bg-slate-900 rounded-lg border border-slate-800 overflow-hidden">
            <button
              onClick={() => setMode('tree')}
              className={`px-2.5 py-1 text-[10px] font-semibold transition-colors ${
                mode === 'tree'
                  ? 'bg-primary/15 text-primary'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Braces size={11} className="inline mr-1" />
              Tree
            </button>
            <button
              onClick={() => setMode('raw')}
              className={`px-2.5 py-1 text-[10px] font-semibold transition-colors ${
                mode === 'raw'
                  ? 'bg-primary/15 text-primary'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Raw
            </button>
          </div>

          {/* Copy button */}
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-semibold bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 transition-all"
          >
            {copied ? <Check size={11} className="text-emerald-400" /> : <Copy size={11} />}
            {copied ? 'Copied!' : 'Copy'}
          </button>

          <button
            onClick={onClose}
            className="p-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800 transition-colors"
          >
            <X size={13} />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-3 font-mono text-[10.5px] leading-relaxed">
        {mode === 'tree' ? (
          <div className="space-y-0.5">
            {Object.entries(workflowJson).map(([key, val]) => (
              <JsonTreeNode key={key} label={key} value={val} depth={0} />
            ))}
          </div>
        ) : (
          <pre className="text-slate-300 whitespace-pre select-all">
            {rawJson}
          </pre>
        )}
      </div>
    </div>
  );
};

export default JsonTracker;

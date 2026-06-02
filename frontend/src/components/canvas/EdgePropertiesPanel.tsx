import React from 'react';
import { X, Trash2, GitBranch } from 'lucide-react';
import { useWorkflowStore } from '../../store/useWorkflowStore';
import type { EdgesType } from '../../types/workflow';
import { asEdgeData, asNodeData } from '../../types/flow';
import type { WFlowEdgeData } from '../../types/flow';

const EDGE_TYPES: EdgesType[] = ['linear', 'parallel', 'merge', 'if', 'switch'];

export const EdgePropertiesPanel: React.FC = () => {
  const {
    activeEdgeId,
    edges,
    nodes,
    setActiveEdgeId,
    updateEdgeProps,
    deleteEdge,
  } = useWorkflowStore();

  const edge = React.useMemo(
    () => edges.find((e) => e.id === activeEdgeId) ?? null,
    [edges, activeEdgeId]
  );

  const sourceNode = React.useMemo(
    () => (edge ? nodes.find((n) => n.id === edge.source) : null),
    [edge, nodes]
  );

  if (!edge || !activeEdgeId) return null;

  const data = asEdgeData(edge.data);
  const sourceKey = sourceNode ? asNodeData(sourceNode.data).key : '';

  const handleTypeChange = (type: EdgesType) => {
    const updates: Partial<WFlowEdgeData> = { type };
    if (type === 'if') {
      updates.decision = data.decision ?? true;
    } else if (type === 'switch') {
      updates.case = data.case ?? 'default';
    }
    updateEdgeProps(activeEdgeId, updates);
  };

  return (
    <aside className="w-[340px] h-full border-l border-border bg-card flex flex-col shadow-2xl z-40 shrink-0">
      <div className="p-4 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <GitBranch className="text-primary" size={18} />
          <div>
            <h3 className="font-bold text-sm uppercase tracking-wider">Edge</h3>
            <span className="text-xs text-muted-foreground font-mono">
              {edge.source} → {edge.target}
            </span>
          </div>
        </div>
        <button
          type="button"
          onClick={() => setActiveEdgeId(null)}
          className="p-1 rounded-lg hover:bg-accent text-muted-foreground"
        >
          <X size={14} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <div>
          <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
            Connection type
          </label>
          <select
            value={data.type}
            onChange={(e) => handleTypeChange(e.target.value as EdgesType)}
            disabled={sourceKey === 'if_node' || sourceKey === 'switch_node'}
            className="mt-1 w-full px-3 py-2.5 rounded-lg bg-background border border-border text-sm focus:outline-none focus:border-primary/50 disabled:opacity-60"
          >
            {EDGE_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
          {(sourceKey === 'if_node' || sourceKey === 'switch_node') && (
            <p className="text-xs text-muted-foreground mt-1">
              Type is fixed for control-flow source nodes.
            </p>
          )}
        </div>

        {data.type === 'if' && (
          <div>
            <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
              Branch decision
            </label>
            <div className="mt-2 flex gap-2">
              <button
                type="button"
                onClick={() => updateEdgeProps(activeEdgeId, { decision: true })}
                className={`flex-1 py-2.5 rounded-lg text-sm font-semibold border transition-all ${
                  data.decision === true
                    ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-400'
                    : 'border-border hover:bg-accent'
                }`}
              >
                True
              </button>
              <button
                type="button"
                onClick={() => updateEdgeProps(activeEdgeId, { decision: false })}
                className={`flex-1 py-2.5 rounded-lg text-sm font-semibold border transition-all ${
                  data.decision === false
                    ? 'bg-rose-500/15 border-rose-500/40 text-rose-400'
                    : 'border-border hover:bg-accent'
                }`}
              >
                False
              </button>
            </div>
          </div>
        )}

        {data.type === 'switch' && (
          <div>
            <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
              Case label
            </label>
            <input
              type="text"
              value={data.case ?? ''}
              onChange={(e) => updateEdgeProps(activeEdgeId, { case: e.target.value })}
              className="mt-1 w-full px-3 py-2.5 rounded-lg bg-background border border-border text-sm font-mono focus:outline-none focus:border-primary/50"
              placeholder="e.g. blog"
            />
          </div>
        )}
      </div>

      <div className="p-4 border-t border-border">
        <button
          type="button"
          onClick={() => {
            if (confirm('Delete this connection?')) {
              deleteEdge(activeEdgeId);
              setActiveEdgeId(null);
            }
          }}
          className="w-full flex items-center justify-center gap-1.5 py-2.5 rounded-lg bg-destructive/10 text-destructive border border-destructive/20 text-sm font-semibold hover:bg-destructive/20 transition-all"
        >
          <Trash2 size={13} />
          Delete edge
        </button>
      </div>
    </aside>
  );
};

export default EdgePropertiesPanel;

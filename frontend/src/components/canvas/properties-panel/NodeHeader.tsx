import React from "react";
import { X, ChevronDown, ChevronUp } from "lucide-react";
import { useWorkflowStore } from "../../../store/useWorkflowStore";
import type { WFlowNodeData } from "../../../types/flow";

interface NodeHeaderProps {
  nodeData: WFlowNodeData;
}

export const NodeHeader: React.FC<NodeHeaderProps> = ({ nodeData }) => {
  const { setActiveNodeId } = useWorkflowStore();
  const [showSchemaInfo, setShowSchemaInfo] = React.useState(false);

  return (
    <div className="border-b border-slate-700 p-4 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1 flex-1">
          <div className="text-sm font-semibold text-foreground">
            {nodeData.label}
          </div>
          <div className="text-xs text-slate-500">{nodeData.name}</div>
        </div>
        <button
          type="button"
          onClick={() => setActiveNodeId(null)}
          className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-slate-700 bg-slate-900/50 text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-all"
        >
          <X size={16} />
        </button>
      </div>

      {nodeData.input_model && (
        <button
          type="button"
          onClick={() => setShowSchemaInfo(!showSchemaInfo)}
          className="w-full text-left rounded-2xl border border-slate-700 bg-slate-900/50 p-3 hover:bg-slate-800/80 transition-all"
        >
          <div className="flex items-center justify-between gap-2">
            <div className="text-xs font-semibold text-slate-300">
              Schema Info
            </div>
            {showSchemaInfo ? (
              <ChevronUp size={14} />
            ) : (
              <ChevronDown size={14} />
            )}
          </div>
        </button>
      )}

      {showSchemaInfo && nodeData.input_model && (
        <div className="rounded-2xl border border-slate-700 bg-slate-900/50 p-3 text-xs text-slate-300 space-y-2">
          {nodeData.input_model.properties && (
            <div>
              <span className="font-semibold">Input fields:</span>{" "}
              {Object.keys(nodeData.input_model.properties).length}
            </div>
          )}
          {nodeData.input_model.required && (
            <div>
              <span className="font-semibold">Required:</span>{" "}
              {nodeData.input_model.required.join(", ")}
            </div>
          )}
          {nodeData.output_model && nodeData.output_model.properties && (
            <div>
              <span className="font-semibold">Output fields:</span>{" "}
              {Object.keys(nodeData.output_model.properties).length}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

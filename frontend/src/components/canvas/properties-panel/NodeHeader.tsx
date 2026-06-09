import React from "react";
import { X } from "lucide-react";
import { useWorkflowStore } from "../../../store/useWorkflowStore";
import type { WFlowNodeData } from "../../../types/flow";

interface NodeHeaderProps {
  nodeData: WFlowNodeData;
}

export const NodeHeader: React.FC<NodeHeaderProps> = ({ nodeData }) => {
  const { setActiveNodeId } = useWorkflowStore();

  return (
    <div className="border-b border-border p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1 flex-1">
          <div className="text-sm font-semibold text-foreground">
            {nodeData.label}
          </div>
          <div className="text-xs text-muted-foreground">{nodeData.name}</div>
        </div>
        <button
          type="button"
          onClick={() => setActiveNodeId(null)}
          className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-muted/50 text-muted-foreground hover:bg-accent hover:text-foreground transition-all"
        >
          <X size={16} />
        </button>
      </div>
    </div>
  );
};

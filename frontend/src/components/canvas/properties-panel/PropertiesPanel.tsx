import React from "react";
import { Trash2 } from "lucide-react";
import { useWorkflowStore } from "../../../store/useWorkflowStore";
import { asNodeData } from "../../../types/flow";
import { NodeHeader } from "./NodeHeader";
import { NodeTabs } from "./NodeTabs";
import { InputsTab } from "./InputsTab";
import { ConfigTab } from "./ConfigTab";
import type { WFlowNodeData } from "../../../types/flow";

export const PropertiesPanel: React.FC = () => {
  const { activeNodeId, nodes, deleteNode, setActiveNodeId } =
    useWorkflowStore();
  const [activeTab, setActiveTab] = React.useState<"inputs" | "config">(
    "inputs",
  );

  const activeNode = React.useMemo(() => {
    return nodes.find((n) => n.id === activeNodeId) || null;
  }, [nodes, activeNodeId]);

  if (!activeNode) return null;

  const nodeData = asNodeData(activeNode.data) as WFlowNodeData;

  return (
    <div className="flex flex-col h-full bg-card">
      {/* Header */}
      <NodeHeader nodeData={nodeData} />

      {/* Tabs */}
      <NodeTabs activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {activeTab === "inputs" && (
          <InputsTab nodeData={nodeData} nodeId={activeNode.id} />
        )}
        {activeTab === "config" && (
          <ConfigTab nodeData={nodeData} nodeId={activeNode.id} />
        )}
      </div>

      {/* Delete Button */}
      <div className="border-t border-border p-4">
        <button
          type="button"
          onClick={() => {
            deleteNode(activeNode.id);
            setActiveNodeId(null);
          }}
          className="w-full inline-flex items-center justify-center gap-2 rounded-2xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm font-semibold text-rose-200 hover:bg-rose-500/15 hover:text-white transition-all"
        >
          <Trash2 size={16} />
          Delete Node
        </button>
      </div>
    </div>
  );
};

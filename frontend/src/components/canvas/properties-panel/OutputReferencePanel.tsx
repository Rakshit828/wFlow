import React from "react";
import { HelpCircle } from "lucide-react";
import { generateOutputPath } from "./utils";
import type { Node as WorkflowNode } from "../../../types/workflow";

interface OutputReferencePanelProps {
  precedingNodes: WorkflowNode[];
}

export const OutputReferencePanel: React.FC<OutputReferencePanelProps> = ({
  precedingNodes,
}) => {
  const referenceMap = new Map<string, { label: string; path: string }>();

  const pushField = (nodeName: string, key: string, nested = false) => {
    const path = generateOutputPath(nodeName, key, nested);
    referenceMap.set(path, {
      label: `${nodeName}.${key}`,
      path,
    });
  };

  const collectProperties = (
    nodeName: string,
    schema?: Record<string, any>,
  ) => {
    if (!schema || typeof schema !== "object") return;
    if (schema.properties) {
      Object.keys(schema.properties).forEach((key) => pushField(nodeName, key));
    }
    if (schema.output?.properties) {
      Object.keys(schema.output.properties).forEach((key) =>
        pushField(nodeName, key, true),
      );
    }
  };

  precedingNodes.forEach((node) => {
    collectProperties(node.name, node.output_model);

    const configResponseOutput = node.config?.response_model?.output;
    collectProperties(node.name, configResponseOutput);
  });

  const references = Array.from(referenceMap.values());

  if (references.length === 0) {
    return (
      <div className="rounded-3xl border border-slate-700 bg-slate-950/80 p-4 text-sm text-slate-400">
        <div className="flex items-start gap-2">
          <HelpCircle size={16} className="mt-0.5 shrink-0" />
          <div>
            <div className="font-semibold text-slate-300 mb-1">
              Available outputs
            </div>
            No preceding nodes have outputs available yet. Connect nodes to
            expose their outputs.
          </div>
        </div>
      </div>
    );
  }

  const handleDragStart = (
    event: React.DragEvent<HTMLDivElement>,
    path: string,
  ) => {
    event.dataTransfer.effectAllowed = "copy";
    event.dataTransfer.setData("application/x-output-path", path);
  };

  return (
    <div className="rounded-3xl border border-slate-700 bg-slate-950/80 p-4 space-y-3">
      <div>
        <div className="text-sm font-semibold text-foreground mb-2">
          Available outputs
        </div>
        <p className="text-xs text-slate-400 mb-3">
          Drag any output reference into an input field to wire them together.
        </p>
      </div>
      <div className="grid gap-2">
        {references.map((ref) => (
          <div
            key={ref.path}
            draggable
            onDragStart={(e) => handleDragStart(e, ref.path)}
            className="rounded-2xl border border-slate-700 bg-slate-900/50 px-3 py-2 text-xs text-slate-300 font-mono hover:bg-slate-800 hover:border-indigo-500 cursor-move transition-all"
          >
            {ref.label}
          </div>
        ))}
      </div>
    </div>
  );
};

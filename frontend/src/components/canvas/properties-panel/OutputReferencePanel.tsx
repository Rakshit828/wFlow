import React from "react";
import { HelpCircle } from "lucide-react";
import { resolveSchemaDeep } from "./utils";
import type { Node as WorkflowNode } from "../../../types/workflow";

interface OutputReferencePanelProps {
  precedingNodes: WorkflowNode[];
}

export const OutputReferencePanel: React.FC<OutputReferencePanelProps> = ({
  precedingNodes,
}) => {
  const nodeGroups = new Map<string, { label: string; path: string }[]>();

  const collectPropertiesRecursive = (
    nodeName: string,
    schema: Record<string, any> | undefined | null,
    currentPath: string,
    currentLabel: string,
    pushRef: (path: string, label: string) => void,
    rootSchema: any,
  ) => {
    if (!schema || typeof schema !== "object") return;

    // Resolve references deeply
    const resolved = resolveSchemaDeep(schema, rootSchema);
    if (!resolved || typeof resolved !== "object") return;

    if (resolved.properties && typeof resolved.properties === "object") {
      Object.entries(resolved.properties).forEach(([key, propSchema]: [string, any]) => {
        const nextPath = `${currentPath}.${key}`;
        const nextLabel = `${currentLabel}.${key}`;
        
        // Push this reference path
        pushRef(nextPath, nextLabel);
        
        // Recurse into nested properties
        collectPropertiesRecursive(nodeName, propSchema, nextPath, nextLabel, pushRef, rootSchema);
      });
    }
  };

  precedingNodes.forEach((node) => {
    const refs: { label: string; path: string }[] = [];
    const pushRef = (path: string, label: string) => {
      if (!refs.some((r) => r.path === path)) {
        refs.push({ label, path });
      }
    };

    // 1. Collect from output_model
    if (node.output_model) {
      collectPropertiesRecursive(
        node.name,
        node.output_model,
        `${node.name}.outputs`,
        node.name,
        pushRef,
        node.output_model,
      );
    }

    // 2. Collect from config.response_model.output
    const configResponseOutput = node.config?.response_model?.output;
    if (configResponseOutput) {
      collectPropertiesRecursive(
        node.name,
        configResponseOutput,
        `${node.name}.outputs.output`,
        node.name,
        pushRef,
        node.config?.response_model,
      );
    }

    if (refs.length > 0) {
      nodeGroups.set(node.name, refs);
    }
  });

  const totalReferencesCount = Array.from(nodeGroups.values()).reduce(
    (acc, refs) => acc + refs.length,
    0,
  );

  if (totalReferencesCount === 0) {
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
    <div className="rounded-3xl border border-slate-700 bg-slate-950/80 p-4 space-y-4">
      <div>
        <div className="text-sm font-semibold text-foreground mb-1">
          Available outputs
        </div>
        <p className="text-xs text-slate-400">
          Drag any output reference into an input field to wire them together.
        </p>
      </div>

      <div className="space-y-4">
        {Array.from(nodeGroups.entries()).map(([nodeName, refs]) => (
          <div key={nodeName} className="space-y-2">
            <div className="text-[11px] font-semibold text-indigo-400 uppercase tracking-wider flex items-center gap-1.5 px-1">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
              {nodeName}
            </div>
            <div className="grid gap-2 pl-3 border-l border-slate-800/80 ml-1.5">
              {refs.map((ref) => (
                <div
                  key={ref.path}
                  draggable
                  onDragStart={(e) => handleDragStart(e, ref.path)}
                  className="rounded-xl border border-slate-700/60 bg-slate-900/40 px-3 py-2 text-xs text-slate-300 font-mono hover:bg-slate-800 hover:border-indigo-500 hover:text-white cursor-move transition-all flex justify-between items-center group/item"
                  title={ref.path}
                >
                  <span className="truncate">{ref.label.replace(`${nodeName}.`, "")}</span>
                  <span className="text-[9px] text-indigo-400 opacity-0 group-hover/item:opacity-100 transition-opacity font-sans select-none pointer-events-none">
                    Drag me
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

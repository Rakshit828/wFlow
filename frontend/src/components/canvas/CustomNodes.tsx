import React from "react";
import { Handle, Position } from "@xyflow/react";
import {
  Brain,
  Mail,
  FileSpreadsheet,
  FolderUp,
  GitFork,
  HelpCircle,
  ShieldCheck,
  Copy,
} from "lucide-react";
import { useWorkflowStore } from "../../store/useWorkflowStore";

// Helper to resolve Lucide Icon based on Node Key
const getNodeIcon = (key: string, size = 18) => {
  if (key.startsWith("llm."))
    return <Brain className="text-amber-400" size={size} />;
  if (key.startsWith("gmail."))
    return <Mail className="text-rose-400" size={size} />;
  if (key.startsWith("sheets."))
    return <FileSpreadsheet className="text-emerald-400" size={size} />;
  if (key.startsWith("drive."))
    return <FolderUp className="text-sky-400" size={size} />;
  if (key === "if_node" || key === "switch_node")
    return <GitFork className="text-purple-400" size={size} />;
  return <HelpCircle className="text-slate-400" size={size} />;
};

// Helper to get Node Type color accents
const getTypeStyles = (type: string) => {
  switch (type) {
    case "LLM":
      return {
        bgGlow: "rgba(245, 158, 11, 0.08)",
        borderColor: "border-amber-500/30",
        borderColorSelected:
          "border-amber-500 shadow-[0_0_15px_rgba(245,158,11,0.4)]",
        badgeBg: "bg-amber-500/10 text-amber-400 border-amber-500/20",
      };
    case "ACTION":
      return {
        bgGlow: "rgba(59, 130, 246, 0.08)",
        borderColor: "border-blue-500/30",
        borderColorSelected:
          "border-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.4)]",
        badgeBg: "bg-blue-500/10 text-blue-400 border-blue-500/20",
      };
    case "CONTROL_FLOW":
      return {
        bgGlow: "rgba(168, 85, 247, 0.08)",
        borderColor: "border-purple-500/30",
        borderColorSelected:
          "border-purple-500 shadow-[0_0_15px_rgba(168,85,247,0.4)]",
        badgeBg: "bg-purple-500/10 text-purple-400 border-purple-500/20",
      };
    default:
      return {
        bgGlow: "rgba(100, 116, 139, 0.08)",
        borderColor: "border-slate-500/30",
        borderColorSelected:
          "border-slate-500 shadow-[0_0_15px_rgba(100,116,139,0.4)]",
        badgeBg: "bg-slate-500/10 text-slate-400 border-slate-500/20",
      };
  }
};

interface CustomNodeProps {
  id: string;
  data: {
    label: string;
    key: string;
    name: string;
    type: string;
    inputs: Record<string, any>;
    config: Record<string, any>;
    outputs: Record<string, any>;
  };
  selected?: boolean;
}

export const WFlowCustomNode: React.FC<CustomNodeProps> = ({
  data,
  selected,
}) => {
  const { nodeRegistry } = useWorkflowStore();
  const spec = nodeRegistry[data.key];
  const styles = getTypeStyles(data.type);

  // Copy name to clipboard utility
  const copyName = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(data.name);
  };

  return (
    <div
      className={`relative w-[272px] rounded-xl border text-foreground transition-all duration-300 ${
        selected
          ? styles.borderColorSelected
          : `${styles.borderColor} hover:border-slate-500/40`
      }`}
      style={{
        background: "rgba(15, 23, 42, 0.85)",
        backdropFilter: "blur(12px)",
        boxShadow: selected
          ? undefined
          : "0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5)",
      }}
    >
      {/* Dynamic Background Glow Effect */}
      <div
        className="absolute inset-0 rounded-xl pointer-events-none"
        style={{ backgroundColor: styles.bgGlow }}
      />

      {/* Handles */}
      {data.name !== "start" && (
        <Handle
          type="target"
          position={Position.Left}
          id="target-left"
          className="w-2 h-2 rounded-full border-2 border-slate-900 bg-indigo-500 hover:scale-125 transition-transform"
        />
      )}

      {data.name !== "end" && (
        <Handle
          type="source"
          position={Position.Right}
          id="source-right"
          className="w-2 h-2 rounded-full border-2 border-slate-900 bg-indigo-500 hover:scale-125 transition-transform"
        />
      )}

      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-slate-800/60 border border-slate-700/50">
            {getNodeIcon(data.key)}
          </div>
          <div>
            <h4 className="font-semibold text-base leading-tight text-foreground tracking-wide">
              {data.label}
            </h4>
            <div className="flex items-center gap-1 mt-0.5 group">
              <span className="text-xs text-muted-foreground font-mono select-all">
                {data.name}
              </span>
              <button
                onClick={copyName}
                className="opacity-0 group-hover:opacity-100 hover:text-slate-200 transition-opacity p-0.5 rounded"
                title="Copy name variable"
              >
                <Copy size={8} />
              </button>
            </div>
          </div>
        </div>
        <div
          className={`px-2 py-0.5 rounded-full text-xs font-semibold border ${styles.badgeBg}`}
        >
          {data.type}
        </div>
      </div>

      {/* Node Mini-Details Body */}
      <div className="p-3 text-sm text-foreground/90 space-y-2">
        <p className="text-xs text-muted-foreground leading-snug">
          {spec?.description || "No description available"}
        </p>

        {/* Dynamic configuration preview */}
        {data.key.startsWith("llm.") && (
          <div className="flex items-center justify-between bg-muted/40 p-1.5 rounded border border-border font-mono text-xs">
            <span className="text-muted-foreground">Model:</span>
            <span className="text-amber-400 truncate max-w-[120px]">
              {data.config?.model || "default"}
            </span>
          </div>
        )}

        {data.key === "if_node" && (
          <div className="bg-slate-900/40 p-1.5 rounded border border-slate-800/40 font-mono text-[9px] space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">If:</span>
              <span className="text-purple-400 truncate max-w-[150px]">
                {data.inputs?.condition || "None"}
              </span>
            </div>
          </div>
        )}

        {data.key === "switch_node" && (
          <div className="bg-slate-900/40 p-1.5 rounded border border-slate-800/40 font-mono text-[9px] space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Match:</span>
              <span className="text-purple-400 truncate max-w-[140px]">
                {data.inputs?.value || "None"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">Cases:</span>
              <span className="text-pink-400">
                {(data.inputs?.cases as string[])?.length || 0} branches
              </span>
            </div>
          </div>
        )}

        {/* Google integration node requirements */}
        {spec?.service && spec.service.startsWith("google.") && (
          <div className="flex items-center justify-between text-[9px] text-slate-400">
            <div className="flex items-center gap-1">
              <ShieldCheck size={11} className="text-emerald-400" />
              <span>Google API Service</span>
            </div>
            <span className="text-[8px] bg-emerald-500/10 text-emerald-400 px-1 py-0.5 rounded border border-emerald-500/20">
              OAuth Connected
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
export default WFlowCustomNode;

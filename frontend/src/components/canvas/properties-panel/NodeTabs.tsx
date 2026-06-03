import React from "react";

interface NodeTabsProps {
  activeTab: "inputs" | "config";
  onTabChange: (tab: "inputs" | "config") => void;
}

export const NodeTabs: React.FC<NodeTabsProps> = ({ activeTab, onTabChange }) => {
  return (
    <div className="flex border-b border-slate-700 px-4">
      <button
        type="button"
        onClick={() => onTabChange("inputs")}
        className={`px-4 py-3 text-sm font-semibold transition-all border-b-2 ${
          activeTab === "inputs"
            ? "border-indigo-500 text-indigo-400"
            : "border-transparent text-slate-400 hover:text-slate-300"
        }`}
      >
        Inputs
      </button>
      <button
        type="button"
        onClick={() => onTabChange("config")}
        className={`px-4 py-3 text-sm font-semibold transition-all border-b-2 ${
          activeTab === "config"
            ? "border-indigo-500 text-indigo-400"
            : "border-transparent text-slate-400 hover:text-slate-300"
        }`}
      >
        Config
      </button>
    </div>
  );
};

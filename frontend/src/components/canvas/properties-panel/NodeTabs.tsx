import React from "react";

interface NodeTabsProps {
  activeTab: "inputs" | "config";
  onTabChange: (tab: "inputs" | "config") => void;
}

export const NodeTabs: React.FC<NodeTabsProps> = ({ activeTab, onTabChange }) => {
  return (
    <div className="flex border-b border-border px-4">
      <button
        type="button"
        onClick={() => onTabChange("inputs")}
        className={`px-4 py-3 text-sm font-semibold transition-all border-b-2 ${
          activeTab === "inputs"
            ? "border-primary text-primary"
            : "border-transparent text-muted-foreground hover:text-foreground"
        }`}
      >
        Inputs
      </button>
      <button
        type="button"
        onClick={() => onTabChange("config")}
        className={`px-4 py-3 text-sm font-semibold transition-all border-b-2 ${
          activeTab === "config"
            ? "border-primary text-primary"
            : "border-transparent text-muted-foreground hover:text-foreground"
        }`}
      >
        Config
      </button>
    </div>
  );
};

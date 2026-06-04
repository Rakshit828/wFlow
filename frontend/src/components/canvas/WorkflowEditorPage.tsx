import React from "react";
import { ReactFlowProvider } from "@xyflow/react";
import { useParams, useOutletContext } from "react-router-dom";
import {
  ChevronRight,
  ChevronLeft,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { FlowCanvas } from "./FlowCanvas";
import { SidebarCatalog } from "./SidebarCatalog";
import { PropertiesPanel } from "./PropertiesPanel";
import { EdgePropertiesPanel } from "./EdgePropertiesPanel";
import { JsonTracker } from "./JsonTracker";
import { useWorkflowStore } from "../../store/useWorkflowStore";

interface AppOutletContext {
  jsonOpen: boolean;
  setJsonOpen: (open: boolean) => void;
}

export const WorkflowEditorPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  // Fetch store states and actions
  const {
    activeNodeId,
    activeEdgeId,
    isLoadingWorkflow,
    workflowLoadError,
    loadWorkflowById,
    resetWorkflow,
  } = useWorkflowStore();

  // Outlet context for sharing the header's JSON drawer toggle state
  const context = useOutletContext<AppOutletContext | null>();
  const [localJsonOpen, setLocalJsonOpen] = React.useState(false);
  const jsonOpen = context ? context.jsonOpen : localJsonOpen;
  const setJsonOpen = context ? context.setJsonOpen : setLocalJsonOpen;

  // Load or reset workflow depending on id parameter
  React.useEffect(() => {
    if (id) {
      loadWorkflowById(id);
    } else {
      resetWorkflow();
    }
  }, [id, loadWorkflowById, resetWorkflow]);

  // Sidebar and Panel Resizing state
  const [sidebarWidth, setSidebarWidth] = React.useState(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("wflow-sidebar-width");
      return stored ? parseInt(stored, 10) : 310;
    }
    return 310;
  });
  const [sidebarCollapsed, setSidebarCollapsed] = React.useState(false);
  const [isResizing, setIsResizing] = React.useState(false);

  const [propertiesWidth, setPropertiesWidth] = React.useState(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("wflow-properties-width");
      return stored ? parseInt(stored, 10) : 360;
    }
    return 360;
  });
  const [propertiesCollapsed, setPropertiesCollapsed] = React.useState(false);
  const [isPanelResizing, setIsPanelResizing] = React.useState(false);

  const sidebarRef = React.useRef<HTMLDivElement>(null);
  const panelRef = React.useRef<HTMLDivElement>(null);
  const startXRef = React.useRef<number>(0);
  const startWidthRef = React.useRef<number>(sidebarWidth);
  const panelStartWidthRef = React.useRef<number>(propertiesWidth);

  // Sidebar drag handler
  React.useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      const delta = e.clientX - startXRef.current;
      const minWidth = 250;
      const maxWidth = 600;
      const newWidth = Math.max(
        minWidth,
        Math.min(maxWidth, startWidthRef.current + delta),
      );
      setSidebarWidth(newWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    document.body.style.userSelect = "none";
    document.body.style.cursor = "col-resize";

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.userSelect = "auto";
      document.body.style.cursor = "auto";
    };
  }, [isResizing]);

  const handleDividerMouseDown = (e: React.MouseEvent) => {
    startXRef.current = e.clientX;
    startWidthRef.current = sidebarWidth;
    setIsResizing(true);
  };

  React.useEffect(() => {
    if (!isResizing) {
      localStorage.setItem("wflow-sidebar-width", String(sidebarWidth));
    }
  }, [sidebarWidth, isResizing]);

  // Properties Panel drag handler
  React.useEffect(() => {
    if (!isPanelResizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      const delta = startXRef.current - e.clientX;
      const minWidth = 280;
      const maxWidth = 520;
      const newWidth = Math.max(
        minWidth,
        Math.min(maxWidth, panelStartWidthRef.current + delta),
      );
      setPropertiesWidth(newWidth);
    };

    const handleMouseUp = () => {
      setIsPanelResizing(false);
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    document.body.style.userSelect = "none";
    document.body.style.cursor = "col-resize";

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.userSelect = "auto";
      document.body.style.cursor = "auto";
    };
  }, [isPanelResizing]);

  const handlePanelDividerMouseDown = (e: React.MouseEvent) => {
    startXRef.current = e.clientX;
    panelStartWidthRef.current = propertiesWidth;
    setIsPanelResizing(true);
  };

  React.useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = localStorage.getItem("wflow-properties-width");
    if (stored) return;

    const initialWidth = Math.round(
      Math.max(320, Math.min(520, window.innerWidth / 3)),
    );
    setPropertiesWidth(initialWidth);
  }, []);

  React.useEffect(() => {
    if (!isPanelResizing) {
      localStorage.setItem("wflow-properties-width", String(propertiesWidth));
    }
  }, [propertiesWidth, isPanelResizing]);

  // If loading the workflow initially
  if (isLoadingWorkflow) {
    return (
      <div className="h-full w-full bg-background flex flex-col items-center justify-center gap-3 text-muted-foreground">
        <Loader2 className="text-primary animate-spin" size={32} />
        <p className="text-sm">Loading workflow...</p>
      </div>
    );
  }

  // If workflow load error occurred
  if (workflowLoadError) {
    return (
      <div className="h-full w-full bg-background flex flex-col items-center justify-center gap-4 text-center px-6">
        <div className="p-4 rounded-full bg-destructive/10 border border-destructive/20 text-destructive">
          <AlertCircle size={32} />
        </div>
        <div className="max-w-md">
          <h3 className="text-lg font-bold text-foreground">Error loading workflow</h3>
          <p className="text-sm text-muted-foreground mt-2">{workflowLoadError}</p>
        </div>
      </div>
    );
  }

  return (
    <ReactFlowProvider>
      <div className="flex h-full w-full relative overflow-hidden">
        {sidebarCollapsed ? (
          <div className="flex h-full items-center justify-center border-r border-border bg-card px-1 z-10 shrink-0">
            <button
              type="button"
              onClick={() => setSidebarCollapsed(false)}
              className="flex h-10 w-10 items-center justify-center rounded-full border border-border bg-background/80 text-muted-foreground hover:text-foreground hover:bg-primary/10 transition-all"
              title="Show sidebar"
            >
              <ChevronRight size={18} />
            </button>
          </div>
        ) : (
          <>
            <div
              ref={sidebarRef}
              style={{
                width: `${sidebarWidth}px`,
                minWidth: `${sidebarWidth}px`,
              }}
              className="flex h-full relative shrink-0 z-10"
            >
              <SidebarCatalog
                sidebarWidth={sidebarWidth}
                onToggleCollapse={() => setSidebarCollapsed(true)}
              />
            </div>
            <div
              onMouseDown={handleDividerMouseDown}
              className={`w-1.5 hover:w-2 bg-border hover:bg-primary/50 cursor-col-resize transition-all z-20 shrink-0 ${
                isResizing ? "bg-primary w-2" : ""
              }`}
            />
          </>
        )}

        <div
          className="flex-1 h-full flex flex-col relative"
          style={{
            marginRight:
              (activeEdgeId || activeNodeId) && !propertiesCollapsed
                ? propertiesWidth
                : 0,
          }}
        >
          <FlowCanvas />
          {jsonOpen && <JsonTracker onClose={() => setJsonOpen(false)} />}
        </div>

        {activeEdgeId || activeNodeId ? (
          propertiesCollapsed ? (
            <button
              type="button"
              onClick={() => setPropertiesCollapsed(false)}
              className="fixed right-0 top-28 z-30 m-2 flex h-11 w-11 items-center justify-center rounded-l-2xl border border-border bg-card text-muted-foreground shadow-lg shadow-black/10 hover:text-foreground hover:bg-primary/10 transition-all"
              title="Open properties panel"
            >
              <ChevronLeft size={18} />
            </button>
          ) : (
            <div
              ref={panelRef}
              style={{
                width: `${propertiesWidth}px`,
                minWidth: `${propertiesWidth}px`,
              }}
              className="fixed right-0 top-14 bottom-0 z-20 flex h-[calc(100vh-3.5rem)] shrink-0 flex-col overflow-hidden bg-slate-950 border-l border-slate-700"
            >
              <div
                onMouseDown={handlePanelDividerMouseDown}
                className={`absolute left-0 top-0 h-full cursor-col-resize bg-border transition-all z-30 ${
                  isPanelResizing ? "w-2 bg-primary" : "w-1.5"
                }`}
              />
              <div className="absolute right-14 top-4 z-10">
                <button
                  type="button"
                  onClick={() => setPropertiesCollapsed(true)}
                  className="flex h-9 w-9 items-center justify-center rounded-full border border-border bg-background/90 text-muted-foreground hover:text-foreground hover:bg-primary/10 transition-all"
                  title="Collapse panel"
                >
                  <ChevronRight size={16} />
                </button>
              </div>
              {activeEdgeId ? (
                <EdgePropertiesPanel />
              ) : (
                <PropertiesPanel />
              )}
            </div>
          )
        ) : null}
      </div>
    </ReactFlowProvider>
  );
};

export default WorkflowEditorPage;

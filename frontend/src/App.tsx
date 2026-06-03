import React from "react";
import { ReactFlowProvider } from "@xyflow/react";
import {
  Moon,
  Sun,
  Monitor,
  Zap,
  ArrowLeft,
  FileJson,
  Loader2,
  ChevronRight,
  ChevronLeft,
} from "lucide-react";
import { FlowCanvas } from "./components/canvas/FlowCanvas";
import { SidebarCatalog } from "./components/canvas/SidebarCatalog";
import { PropertiesPanel } from "./components/canvas/PropertiesPanel";
import { EdgePropertiesPanel } from "./components/canvas/EdgePropertiesPanel";
import { JsonTracker } from "./components/canvas/JsonTracker";
import { Dashboard } from "./components/dashboard/Dashboard";
import { LandingPage } from "./components/landing/LandingPage";
import { SignInPage } from "./components/auth/SignInPage";
import { useWorkflowStore } from "./store/useWorkflowStore";
import { useAuthStore } from "./store/useAuthStore";

type AppView = "dashboard" | "editor";
type PublicView = "landing" | "signin";
type ThemeMode = "light" | "dark" | "system";

function App() {
  const [publicView, setPublicView] = React.useState<PublicView>("landing");
  const [view, setView] = React.useState<AppView>("dashboard");
  const [theme, setTheme] = React.useState<ThemeMode>("system");
  const [jsonOpen, setJsonOpen] = React.useState(false);
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
  const { activeNodeId, activeEdgeId } = useWorkflowStore();
  const { status, user, checkSession } = useAuthStore();

  React.useEffect(() => {
    checkSession();
  }, [checkSession]);

  const sidebarRef = React.useRef<HTMLDivElement>(null);
  const panelRef = React.useRef<HTMLDivElement>(null);
  const startXRef = React.useRef<number>(0);
  const startWidthRef = React.useRef<number>(sidebarWidth);
  const panelStartWidthRef = React.useRef<number>(propertiesWidth);

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

  const handlePanelDividerMouseDown = (e: React.MouseEvent) => {
    startXRef.current = e.clientX;
    panelStartWidthRef.current = propertiesWidth;
    setIsPanelResizing(true);
  };

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

  const handleDividerMouseDown = (e: React.MouseEvent) => {
    startXRef.current = e.clientX;
    startWidthRef.current = sidebarWidth;
    setIsResizing(true);
  };

  // Persist sidebar width to localStorage
  React.useEffect(() => {
    if (!isResizing) {
      localStorage.setItem("wflow-sidebar-width", String(sidebarWidth));
    }
  }, [sidebarWidth, isResizing]);

  React.useEffect(() => {
    const root = document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
    } else if (theme === "light") {
      root.classList.remove("dark");
    } else {
      const prefersDark = window.matchMedia(
        "(prefers-color-scheme: dark)",
      ).matches;
      root.classList.toggle("dark", prefersDark);
    }
  }, [theme]);

  const cycleTheme = () => {
    const order: ThemeMode[] = ["dark", "light", "system"];
    const idx = order.indexOf(theme);
    setTheme(order[(idx + 1) % order.length]);
  };

  const themeIcon =
    theme === "dark" ? (
      <Moon size={14} />
    ) : theme === "light" ? (
      <Sun size={14} />
    ) : (
      <Monitor size={14} />
    );

  if (status === "loading") {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center gap-3 text-muted-foreground">
        <Loader2 className="text-primary animate-spin" size={32} />
        <p className="text-sm">Loading wFlow…</p>
      </div>
    );
  }

  if (status === "unauthenticated") {
    if (publicView === "signin") {
      return <SignInPage onBack={() => setPublicView("landing")} />;
    }
    return <LandingPage onGetStarted={() => setPublicView("signin")} />;
  }

  return (
    <div className="h-screen w-screen flex flex-col bg-background text-foreground overflow-hidden">
      <header className="h-14 flex items-center justify-between px-4 border-b border-border bg-card/80 backdrop-blur-md z-50 shrink-0">
        <div className="flex items-center gap-3">
          {view === "editor" && (
            <button
              type="button"
              onClick={() => setView("dashboard")}
              className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors mr-2"
            >
              <ArrowLeft size={16} />
              <span className="hidden sm:inline">Dashboard</span>
            </button>
          )}
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-primary/10 border border-primary/20">
              <Zap className="text-primary" size={16} />
            </div>
            <h1 className="text-base font-bold tracking-wide">
              wFlow
              <span className="text-[11px] ml-1.5 text-muted-foreground font-normal uppercase tracking-widest">
                {view === "editor" ? "Editor" : "Dashboard"}
              </span>
            </h1>
          </div>
          {user?.email && (
            <span className="hidden lg:inline text-xs text-muted-foreground truncate max-w-[180px]">
              {user.email}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {view === "editor" && (
            <button
              type="button"
              onClick={() => setJsonOpen(!jsonOpen)}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-sm font-semibold transition-all border ${
                jsonOpen
                  ? "bg-primary/10 text-primary border-primary/30"
                  : "bg-card text-muted-foreground border-border hover:text-foreground"
              }`}
            >
              <FileJson size={14} />
              JSON
            </button>
          )}
          <button
            type="button"
            onClick={cycleTheme}
            className="p-2 rounded-lg bg-card text-muted-foreground hover:text-foreground border border-border hover:border-primary/30 transition-all"
            title={`Theme: ${theme}`}
          >
            {themeIcon}
          </button>
        </div>
      </header>

      <main className="flex-1 overflow-hidden relative">
        {view === "dashboard" ? (
          <Dashboard onOpenEditor={() => setView("editor")} />
        ) : (
          <ReactFlowProvider>
            <div className="flex h-full w-full">
              {sidebarCollapsed ? (
                <div className="flex h-full items-center justify-center border-r border-border bg-card px-1">
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
                    className="flex h-full relative shrink-0"
                  >
                    <SidebarCatalog
                      sidebarWidth={sidebarWidth}
                      onToggleCollapse={() => setSidebarCollapsed(true)}
                    />
                  </div>
                  <div
                    onMouseDown={handleDividerMouseDown}
                    className={`w-1.5 hover:w-2 bg-border hover:bg-primary/50 cursor-col-resize transition-all ${
                      isResizing ? "bg-primary w-2" : ""
                    }`}
                  />
                </>
              )}

              <div
                className="flex-1 flex flex-col relative"
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
                    className="fixed right-0 top-20 z-50 m-2 flex h-11 w-11 items-center justify-center rounded-l-2xl border border-border bg-card text-muted-foreground shadow-lg shadow-black/10 hover:text-foreground hover:bg-primary/10 transition-all"
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
                    className="fixed right-0 top-14 bottom-0 z-40 flex h-[calc(100vh-3.5rem)] shrink-0 flex-col overflow-hidden bg-slate-950 border-l border-slate-700"
                  >
                    <div
                      onMouseDown={handlePanelDividerMouseDown}
                      className={`absolute left-0 top-0 h-full cursor-col-resize bg-border transition-all ${
                        isPanelResizing ? "w-2 bg-primary" : "w-1.5"
                      }`}
                    />
                    <div className="absolute right-4 top-4 z-10">
                      <button
                        type="button"
                        onClick={() => setPropertiesCollapsed(true)}
                        className="h-9 w-9 rounded-lg border border-border bg-background/90 text-muted-foreground hover:text-foreground hover:bg-primary/10 transition-all"
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
        )}
      </main>
    </div>
  );
}

export default App;

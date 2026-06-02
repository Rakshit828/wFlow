import React from 'react';
import { ReactFlowProvider } from '@xyflow/react';
import {
  Moon,
  Sun,
  Monitor,
  Zap,
  ArrowLeft,
  FileJson,
} from 'lucide-react';
import { FlowCanvas } from './components/canvas/FlowCanvas';
import { SidebarCatalog } from './components/canvas/SidebarCatalog';
import { PropertiesPanel } from './components/canvas/PropertiesPanel';
import { EdgePropertiesPanel } from './components/canvas/EdgePropertiesPanel';
import { JsonTracker } from './components/canvas/JsonTracker';
import { Dashboard } from './components/dashboard/Dashboard';
import { useWorkflowStore } from './store/useWorkflowStore';

type AppView = 'dashboard' | 'editor';
type ThemeMode = 'light' | 'dark' | 'system';

function App() {
  const [view, setView] = React.useState<AppView>('dashboard');
  const [theme, setTheme] = React.useState<ThemeMode>('dark');
  const [jsonOpen, setJsonOpen] = React.useState(false);
  const { activeNodeId, activeEdgeId } = useWorkflowStore();

  React.useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else if (theme === 'light') {
      root.classList.remove('dark');
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      root.classList.toggle('dark', prefersDark);
    }
  }, [theme]);

  const cycleTheme = () => {
    const order: ThemeMode[] = ['dark', 'light', 'system'];
    const idx = order.indexOf(theme);
    setTheme(order[(idx + 1) % order.length]);
  };

  const themeIcon =
    theme === 'dark' ? (
      <Moon size={14} />
    ) : theme === 'light' ? (
      <Sun size={14} />
    ) : (
      <Monitor size={14} />
    );

  return (
    <div className="h-screen w-screen flex flex-col bg-background text-foreground overflow-hidden">
      <header className="h-14 flex items-center justify-between px-4 border-b border-border bg-card/80 backdrop-blur-md z-50 shrink-0">
        <div className="flex items-center gap-3">
          {view === 'editor' && (
            <button
              onClick={() => setView('dashboard')}
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
                {view === 'editor' ? 'Editor' : 'Dashboard'}
              </span>
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {view === 'editor' && (
            <button
              onClick={() => setJsonOpen(!jsonOpen)}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-sm font-semibold transition-all border ${
                jsonOpen
                  ? 'bg-primary/10 text-primary border-primary/30'
                  : 'bg-card text-muted-foreground border-border hover:text-foreground'
              }`}
            >
              <FileJson size={14} />
              JSON
            </button>
          )}
          <button
            onClick={cycleTheme}
            className="p-2 rounded-lg bg-card text-muted-foreground hover:text-foreground border border-border hover:border-primary/30 transition-all"
            title={`Theme: ${theme}`}
          >
            {themeIcon}
          </button>
        </div>
      </header>

      <main className="flex-1 overflow-hidden">
        {view === 'dashboard' ? (
          <Dashboard onOpenEditor={() => setView('editor')} />
        ) : (
          <ReactFlowProvider>
            <div className="flex h-full w-full">
              <SidebarCatalog />
              <div className="flex-1 flex flex-col relative">
                <FlowCanvas />
                {jsonOpen && <JsonTracker onClose={() => setJsonOpen(false)} />}
              </div>
              {activeEdgeId ? (
                <EdgePropertiesPanel />
              ) : (
                activeNodeId && <PropertiesPanel />
              )}
            </div>
          </ReactFlowProvider>
        )}
      </main>
    </div>
  );
}

export default App;

import React from 'react';
import {
  Brain,
  Mail,
  FileSpreadsheet,
  FolderUp,
  GitFork,
  HelpCircle,
  Sparkles,
  PlaySquare,
  Wrench
} from 'lucide-react';
import { NODE_SPEC_CATALOG } from '../../types/workflow';
import type { AppNodeSpec } from '../../types/workflow';

const getCategoryIcon = (category: string) => {
  switch (category) {
    case 'LLM':
      return <Sparkles className="text-amber-400" size={16} />;
    case 'ACTION':
      return <Wrench className="text-blue-400" size={16} />;
    case 'CONTROL_FLOW':
      return <GitFork className="text-purple-400" size={16} />;
    default:
      return <HelpCircle className="text-muted-foreground" size={16} />;
  }
};

const getCategoryName = (category: string) => {
  switch (category) {
    case 'LLM': return 'AI LLM Providers';
    case 'ACTION': return 'Google Cloud Services';
    case 'CONTROL_FLOW': return 'Logical Gate Routing';
    default: return 'Custom Nodes';
  }
};

export const SidebarCatalog: React.FC = () => {
  const categories = React.useMemo(() => {
    const groups: Record<string, AppNodeSpec[]> = {};
    Object.values(NODE_SPEC_CATALOG).forEach(spec => {
      const type = spec.type;
      if (!groups[type]) groups[type] = [];
      groups[type].push(spec);
    });
    return groups;
  }, []);

  const onDragStart = (event: React.DragEvent, nodeKey: string) => {
    event.dataTransfer.setData('application/reactflow-nodekey', nodeKey);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <aside className="w-[300px] h-full border-r border-border bg-card flex flex-col select-none shrink-0">
      <div className="p-4 border-b border-border bg-muted/30">
        <h3 className="font-bold text-base text-foreground uppercase tracking-wider flex items-center gap-2">
          <PlaySquare className="text-primary" size={18} />
          Nodes catalog
        </h3>
        <p className="text-sm text-muted-foreground mt-1.5 leading-snug">
          Drag and drop nodes onto the canvas to build your workflow.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        {Object.entries(categories).map(([category, specs]) => (
          <div key={category} className="space-y-2.5">
            <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-widest flex items-center gap-1.5 px-1">
              {getCategoryIcon(category)}
              {getCategoryName(category)}
            </h4>

            <div className="space-y-2">
              {specs.map(spec => (
                <div
                  key={spec.key}
                  draggable
                  onDragStart={(e) => onDragStart(e, spec.key)}
                  className="group flex flex-col p-3 rounded-xl border border-border bg-background/60 hover:bg-accent/50 hover:border-primary/30 cursor-grab active:cursor-grabbing transition-all duration-200"
                >
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded bg-muted border border-border text-foreground">
                      {spec.key.startsWith('gmail.') && <Mail size={15} className="text-rose-400" />}
                      {spec.key.startsWith('sheets.') && <FileSpreadsheet size={15} className="text-emerald-400" />}
                      {spec.key.startsWith('drive.') && <FolderUp size={15} className="text-sky-400" />}
                      {spec.key.startsWith('llm.') && <Brain size={15} className="text-amber-400" />}
                      {spec.type === 'CONTROL_FLOW' && <GitFork size={15} className="text-purple-400" />}
                    </div>
                    <span className="text-sm font-semibold text-foreground tracking-wide group-hover:text-primary transition-colors">
                      {spec.name}
                    </span>
                  </div>
                  <span className="text-xs text-muted-foreground mt-2 leading-snug">
                    {spec.description}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
};
export default SidebarCatalog;

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

// Helper to resolve catalog category icons
const getCategoryIcon = (category: string) => {
  switch (category) {
    case 'LLM':
      return <Sparkles className="text-amber-400" size={14} />;
    case 'ACTION':
      return <Wrench className="text-blue-400" size={14} />;
    case 'CONTROL_FLOW':
      return <GitFork className="text-purple-400" size={14} />;
    default:
      return <HelpCircle className="text-slate-400" size={14} />;
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
  // Group specifications by node type
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
    <aside className="w-[300px] h-full border-r border-slate-800 bg-slate-950 flex flex-col select-none">
      {/* Title */}
      <div className="p-4 border-b border-slate-800 bg-slate-900/40">
        <h3 className="font-bold text-sm text-white uppercase tracking-wider flex items-center gap-2">
          <PlaySquare className="text-indigo-400" size={16} />
          Nodes Catalog
        </h3>
        <p className="text-[10px] text-slate-400 mt-1">
          Drag and drop nodes onto the canvas to construct your automation graph.
        </p>
      </div>

      {/* Nodes List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        {Object.entries(categories).map(([category, specs]) => (
          <div key={category} className="space-y-2.5">
            <h4 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1.5 px-1">
              {getCategoryIcon(category)}
              {getCategoryName(category)}
            </h4>

            <div className="space-y-2">
              {specs.map(spec => (
                <div
                  key={spec.key}
                  draggable
                  onDragStart={(e) => onDragStart(e, spec.key)}
                  className="group flex flex-col p-3 rounded-xl border border-slate-800/80 bg-slate-900/40 hover:bg-slate-900/80 hover:border-slate-700/80 cursor-grab active:cursor-grabbing transition-all duration-200"
                >
                  <div className="flex items-center gap-2">
                    <div className="p-1 rounded bg-slate-800 border border-slate-700/40 text-slate-300">
                      {spec.key.startsWith('gmail.') && <Mail size={14} className="text-rose-400" />}
                      {spec.key.startsWith('sheets.') && <FileSpreadsheet size={14} className="text-emerald-400" />}
                      {spec.key.startsWith('drive.') && <FolderUp size={14} className="text-sky-400" />}
                      {spec.key.startsWith('llm.') && <Brain size={14} className="text-amber-400" />}
                      {spec.type === 'CONTROL_FLOW' && <GitFork size={14} className="text-purple-400" />}
                    </div>
                    <span className="text-xs font-semibold text-white tracking-wide group-hover:text-indigo-300 transition-colors">
                      {spec.name}
                    </span>
                  </div>
                  <span className="text-[9.5px] text-slate-400 mt-1.5 leading-snug">
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

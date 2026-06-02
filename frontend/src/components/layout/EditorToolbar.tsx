import React from 'react';
import { Save, Loader2, Check, AlertCircle, Pencil } from 'lucide-react';
import { useWorkflowStore } from '../../store/useWorkflowStore';
import { cn } from '../../lib/utils';

export const EditorToolbar: React.FC = () => {
  const {
    workflowName,
    workflowDescription,
    workflowVisibility,
    isDirty,
    saveStatus,
    saveError,
    setMetadata,
    saveWorkflow,
  } = useWorkflowStore();

  const [editingMeta, setEditingMeta] = React.useState(false);
  const [draftName, setDraftName] = React.useState(workflowName);
  const [draftDesc, setDraftDesc] = React.useState(workflowDescription);
  const [draftVisibility, setDraftVisibility] = React.useState(workflowVisibility);

  React.useEffect(() => {
    setDraftName(workflowName);
    setDraftDesc(workflowDescription);
    setDraftVisibility(workflowVisibility);
  }, [workflowName, workflowDescription, workflowVisibility]);

  const applyMeta = () => {
    setMetadata({
      name: draftName.trim() || workflowName,
      description: draftDesc,
      visibility: draftVisibility,
    });
    setEditingMeta(false);
  };

  const handleSave = async () => {
    await saveWorkflow();
  };

  return (
    <div className="absolute top-3 left-1/2 -translate-x-1/2 z-20 flex flex-col items-center gap-2 pointer-events-none">
      <div className="pointer-events-auto flex items-center gap-2 px-3 py-1.5 rounded-xl bg-card/90 backdrop-blur-md border border-border shadow-lg">
        {editingMeta ? (
          <div className="flex items-center gap-2">
            <input
              value={draftName}
              onChange={(e) => setDraftName(e.target.value)}
              className="w-40 px-2 py-1 rounded-lg bg-background border border-border text-xs"
              placeholder="Workflow name"
            />
            <select
              value={draftVisibility}
              onChange={(e) => setDraftVisibility(e.target.value as 'public' | 'private')}
              className="px-2 py-1 rounded-lg bg-background border border-border text-xs"
            >
              <option value="private">Private</option>
              <option value="public">Public</option>
            </select>
            <button
              type="button"
              onClick={applyMeta}
              className="px-2 py-1 rounded-lg bg-primary text-primary-foreground text-xs font-semibold"
            >
              OK
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setEditingMeta(true)}
            className="flex items-center gap-1.5 text-xs text-foreground hover:text-primary transition-colors"
          >
            <span className="font-semibold max-w-[180px] truncate">{workflowName}</span>
            <Pencil size={11} className="text-muted-foreground" />
            {isDirty && (
              <span className="text-[9px] text-amber-400 font-medium">unsaved</span>
            )}
          </button>
        )}

        <div className="w-px h-5 bg-border" />

        <button
          type="button"
          onClick={handleSave}
          disabled={saveStatus === 'saving'}
          className={cn(
            'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all',
            saveStatus === 'saved'
              ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
              : 'bg-primary text-primary-foreground hover:bg-primary/90 shadow-md shadow-primary/20'
          )}
        >
          {saveStatus === 'saving' ? (
            <Loader2 size={13} className="animate-spin" />
          ) : saveStatus === 'saved' ? (
            <Check size={13} />
          ) : (
            <Save size={13} />
          )}
          {saveStatus === 'saving' ? 'Saving…' : saveStatus === 'saved' ? 'Saved' : 'Save'}
        </button>
      </div>

      {saveStatus === 'error' && saveError && (
        <div className="pointer-events-auto flex items-center gap-1.5 px-3 py-1 rounded-lg bg-destructive/10 border border-destructive/30 text-destructive text-[10px]">
          <AlertCircle size={12} />
          {saveError}
          <span className="text-muted-foreground ml-1">— sign in with Google if needed</span>
        </div>
      )}
    </div>
  );
};

export default EditorToolbar;

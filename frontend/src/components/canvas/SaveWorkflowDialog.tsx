import React from 'react';
import { X, Save, Loader2, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useWorkflowStore } from '../../store/useWorkflowStore';

interface SaveWorkflowDialogProps {
  open: boolean;
  onClose: () => void;
}

export const SaveWorkflowDialog: React.FC<SaveWorkflowDialogProps> = ({ open, onClose }) => {
  const navigate = useNavigate();
  const {
    workflowName,
    workflowDescription,
    workflowVisibility,
    setMetadata,
    saveWorkflow,
    saveStatus,
    saveError,
  } = useWorkflowStore();

  const [name, setName] = React.useState(workflowName);
  const [description, setDescription] = React.useState(workflowDescription);
  const [visibility, setVisibility] = React.useState<'public' | 'private'>(workflowVisibility);

  React.useEffect(() => {
    if (open) {
      setName(workflowName);
      setDescription(workflowDescription);
      setVisibility(workflowVisibility);
      useWorkflowStore.setState({ saveStatus: 'idle', saveError: null });
    }
  }, [open, workflowName, workflowDescription, workflowVisibility]);

  if (!open) return null;

  const handleConfirm = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedName = name.trim();
    if (!trimmedName) return;

    setMetadata({
      name: trimmedName,
      description: description.trim(),
      visibility,
    });

    const ok = await saveWorkflow();
    if (ok) {
      const newId = useWorkflowStore.getState().workflowId;
      if (newId) {
        navigate(`/workflow/${newId}`, { replace: true });
      }
      onClose();
    }
  };

  const saving = saveStatus === 'saving';

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <button
        type="button"
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
        disabled={saving}
        aria-label="Close dialog"
      />
      <form
        onSubmit={handleConfirm}
        className="relative w-full max-w-md rounded-2xl bg-card border border-border shadow-2xl p-6 animate-fade-in-up"
      >
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-primary/10 border border-primary/20">
              <Save className="text-primary" size={18} />
            </div>
            <h2 className="text-base font-bold">Save workflow</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={saving}
            className="p-1.5 rounded-lg hover:bg-accent text-muted-foreground disabled:opacity-50"
          >
            <X size={16} />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
              Name
            </label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              disabled={saving}
              placeholder="My workflow"
              className="mt-1 w-full px-3 py-2.5 rounded-xl bg-background border border-border text-sm focus:outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/10 disabled:opacity-60"
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              disabled={saving}
              placeholder="What does this workflow do?"
              className="mt-1 w-full px-3 py-2.5 rounded-xl bg-background border border-border text-sm resize-none focus:outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/10 disabled:opacity-60"
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
              Visibility
            </label>
            <select
              value={visibility}
              onChange={(e) => setVisibility(e.target.value as 'public' | 'private')}
              disabled={saving}
              className="mt-1 w-full px-3 py-2.5 rounded-xl bg-background border border-border text-sm focus:outline-none focus:border-primary/50 disabled:opacity-60"
            >
              <option value="private">Private</option>
              <option value="public">Public</option>
            </select>
          </div>

          {saveStatus === 'error' && saveError && (
            <div className="flex items-start gap-2 px-3 py-2.5 rounded-xl bg-destructive/10 border border-destructive/30 text-destructive text-sm">
              <AlertCircle size={16} className="shrink-0 mt-0.5" />
              <span>{saveError}</span>
            </div>
          )}
        </div>

        <div className="flex gap-2 mt-6">
          <button
            type="button"
            onClick={onClose}
            disabled={saving}
            className="flex-1 py-2.5 rounded-xl border border-border text-sm font-medium hover:bg-accent transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving || !name.trim()}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20 disabled:opacity-60"
          >
            {saving ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Saving…
              </>
            ) : (
              'Confirm'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default SaveWorkflowDialog;

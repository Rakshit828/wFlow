import React from 'react';
import { X, Workflow } from 'lucide-react';
import { useWorkflowStore } from '../../store/useWorkflowStore';

interface CreateDialogProps {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export const CreateDialog: React.FC<CreateDialogProps> = ({ open, onClose, onCreated }) => {
  const { resetWorkflow, setMetadata } = useWorkflowStore();
  const [name, setName] = React.useState('New Workflow');
  const [description, setDescription] = React.useState(
    'Configure your custom automation workflow here.'
  );
  const [visibility, setVisibility] = React.useState<'public' | 'private'>('private');

  if (!open) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    resetWorkflow();
    setMetadata({
      name: name.trim() || 'New AI Pipeline',
      description: description.trim(),
      visibility,
    });
    onCreated();
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <button
        type="button"
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
        aria-label="Close dialog"
      />
      <form
        onSubmit={handleSubmit}
        className="relative w-full max-w-md rounded-2xl bg-card border border-border shadow-2xl p-6 animate-fade-in-up"
      >
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-primary/10 border border-primary/20">
              <Workflow className="text-primary" size={18} />
            </div>
            <h2 className="text-base font-bold">Create workflow</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-accent text-muted-foreground"
          >
            <X size={16} />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wide">
              Name
            </label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="mt-1 w-full px-3 py-2.5 rounded-xl bg-background border border-border text-sm focus:outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/10"
            />
          </div>
          <div>
            <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wide">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="mt-1 w-full px-3 py-2.5 rounded-xl bg-background border border-border text-sm resize-none focus:outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/10"
            />
          </div>
          <div>
            <label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wide">
              Visibility
            </label>
            <select
              value={visibility}
              onChange={(e) => setVisibility(e.target.value as 'public' | 'private')}
              className="mt-1 w-full px-3 py-2.5 rounded-xl bg-background border border-border text-sm focus:outline-none focus:border-primary/50"
            >
              <option value="private">Private</option>
              <option value="public">Public</option>
            </select>
          </div>
        </div>

        <div className="flex gap-2 mt-6">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 py-2.5 rounded-xl border border-border text-sm font-medium hover:bg-accent transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="flex-1 py-2.5 rounded-xl bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20"
          >
            Open editor
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateDialog;

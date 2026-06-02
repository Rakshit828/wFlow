import React from 'react';
import { Mail, FileSpreadsheet, FolderUp, ExternalLink } from 'lucide-react';
import { googleNewScopeUrl } from '../../api/auth';
import { NODE_SPEC_CATALOG } from '../../types/workflow';
import { useAuthStore } from '../../store/useAuthStore';

const GOOGLE_SCOPE_GROUPS = [
  {
    id: 'gmail',
    label: 'Gmail',
    icon: Mail,
    scopes: ['gmail.send', 'gmail.compose', 'gmail.readonly'],
  },
  {
    id: 'sheets',
    label: 'Google Sheets',
    icon: FileSpreadsheet,
    scopes: ['sheets.fullaccess', 'sheets.readonly'],
  },
  {
    id: 'drive',
    label: 'Google Drive',
    icon: FolderUp,
    scopes: ['drive.fullaccess', 'drive.file'],
  },
];

export const Integrations: React.FC = () => {
  const { user } = useAuthStore();
  const email = user?.email ?? '';

  const googleNodes = Object.values(NODE_SPEC_CATALOG).filter(
    (s) => s.service?.startsWith('google.')
  );

  const handleConnectScopes = (scopes: string[]) => {
    if (!email) return;
    window.location.href = googleNewScopeUrl(scopes, email);
  };

  return (
    <section className="max-w-6xl mx-auto px-6 pb-10">
      <h2 className="text-sm font-bold text-foreground mb-1">Google integrations</h2>
      <p className="text-sm text-muted-foreground mb-4">
        Grant additional permissions for Gmail, Sheets, and Drive nodes in your workflows.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {GOOGLE_SCOPE_GROUPS.map((group) => (
          <button
            key={group.id}
            type="button"
            onClick={() => handleConnectScopes(group.scopes)}
            className="flex items-center justify-between gap-2 px-4 py-3 rounded-xl border border-border bg-card hover:border-primary/30 hover:bg-accent/50 text-left transition-all"
          >
            <span className="flex items-center gap-2 text-sm font-medium">
              <group.icon size={16} className="text-primary" />
              {group.label}
            </span>
            <ExternalLink size={14} className="text-muted-foreground shrink-0" />
          </button>
        ))}
      </div>

      <div className="mt-4 p-4 rounded-xl bg-muted/30 border border-border">
        <p className="text-xs text-muted-foreground mb-2 font-semibold uppercase tracking-wide">
          Nodes using Google ({googleNodes.length})
        </p>
        <div className="flex flex-wrap gap-1.5">
          {googleNodes.map((n) => (
            <span
              key={n.key}
              className="text-xs px-2 py-0.5 rounded-full bg-card border border-border text-muted-foreground"
            >
              {n.name}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Integrations;

import React from 'react';
import { Mail, FileSpreadsheet, FolderUp, LogIn, ExternalLink } from 'lucide-react';
import { redirectToGoogleLogin, googleNewScopeUrl } from '../../api/auth';
import { NODE_SPEC_CATALOG } from '../../types/workflow';

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
  const [email, setEmail] = React.useState('');

  const googleNodes = Object.values(NODE_SPEC_CATALOG).filter(
    (s) => s.service?.startsWith('google.')
  );

  const handleConnectScopes = (scopes: string[]) => {
    if (!email.trim()) {
      alert('Enter the Google account email used for wFlow.');
      return;
    }
    window.location.href = googleNewScopeUrl(scopes, email.trim());
  };

  return (
    <section className="max-w-6xl mx-auto px-6 pb-10">
      <h2 className="text-sm font-bold text-foreground mb-1">Integrations</h2>
      <p className="text-xs text-muted-foreground mb-4">
        Sign in with Google, then grant scopes required by action nodes in your workflows.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-5 rounded-2xl bg-card border border-border">
          <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-3">
            Account
          </h3>
          <p className="text-xs text-muted-foreground mb-4 leading-relaxed">
            Login stores a secure session cookie. Required to save workflows and connect Google services.
          </p>
          <button
            type="button"
            onClick={() => redirectToGoogleLogin()}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary/90 transition-all"
          >
            <LogIn size={15} />
            Sign in with Google
          </button>
        </div>

        <div className="p-5 rounded-2xl bg-card border border-border">
          <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-3">
            Additional scopes
          </h3>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="your@gmail.com"
            className="w-full mb-3 px-3 py-2 rounded-xl bg-background border border-border text-xs focus:outline-none focus:border-primary/50"
          />
          <div className="space-y-2">
            {GOOGLE_SCOPE_GROUPS.map((group) => (
              <button
                key={group.id}
                type="button"
                onClick={() => handleConnectScopes(group.scopes)}
                className="w-full flex items-center justify-between gap-2 px-3 py-2 rounded-xl border border-border hover:border-primary/30 hover:bg-accent/50 text-left transition-all"
              >
                <span className="flex items-center gap-2 text-xs font-medium">
                  <group.icon size={14} className="text-primary" />
                  {group.label}
                </span>
                <ExternalLink size={12} className="text-muted-foreground shrink-0" />
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-4 p-4 rounded-xl bg-muted/30 border border-border">
        <p className="text-[10px] text-muted-foreground mb-2 font-semibold uppercase tracking-wide">
          Nodes requiring Google permissions ({googleNodes.length})
        </p>
        <div className="flex flex-wrap gap-1.5">
          {googleNodes.map((n) => (
            <span
              key={n.key}
              className="text-[9px] px-2 py-0.5 rounded-full bg-card border border-border text-muted-foreground"
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

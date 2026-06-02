import React from 'react';
import {
  Zap,
  GitBranch,
  Sparkles,
  Mail,
  FileSpreadsheet,
  ArrowRight,
  Workflow,
} from 'lucide-react';

interface LandingPageProps {
  onGetStarted: () => void;
}

const features = [
  {
    icon: GitBranch,
    title: 'Visual workflow builder',
    description:
      'Drag LLM, Google, and control-flow nodes onto a canvas. Connect them with linear, parallel, merge, if, and switch edges.',
  },
  {
    icon: Sparkles,
    title: 'AI-native pipelines',
    description:
      'Chain Groq and Gemini models with structured outputs, references between nodes, and live JSON tracking.',
  },
  {
    icon: Mail,
    title: 'Google integrations',
    description:
      'Automate Gmail, Sheets, and Drive actions inside the same workflow graph you design visually.',
  },
  {
    icon: Workflow,
    title: 'Production-ready JSON',
    description:
      'Every connection updates a backend-compatible workflow document you can save, share, and run when execution is enabled.',
  },
];

export const LandingPage: React.FC<LandingPageProps> = ({ onGetStarted }) => {
  return (
    <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-[400px] h-[400px] bg-indigo-500/10 rounded-full blur-3xl" />
      </div>

      <header className="relative z-10 flex items-center justify-between px-6 py-5 max-w-6xl mx-auto">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-xl bg-primary/10 border border-primary/20">
            <Zap className="text-primary" size={22} />
          </div>
          <span className="text-xl font-bold tracking-tight">wFlow</span>
        </div>
        <button
          type="button"
          onClick={onGetStarted}
          className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors"
        >
          Sign in
        </button>
      </header>

      <main className="relative z-10 max-w-6xl mx-auto px-6 pb-20">
        <section className="pt-12 pb-20 text-center">
          <p className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-semibold uppercase tracking-wider mb-6">
            AI workflow automation
          </p>
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight leading-tight max-w-3xl mx-auto">
            Build complex AI pipelines{' '}
            <span className="text-primary">without writing JSON by hand</span>
          </h1>
          <p className="mt-6 text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            wFlow is a visual editor for designing multi-step automations: LLM chains,
            quality gates, branching logic, and Google Workspace actions — all in one graph.
          </p>
          <button
            type="button"
            onClick={onGetStarted}
            className="mt-10 inline-flex items-center gap-2 px-8 py-3.5 rounded-xl bg-primary text-primary-foreground text-base font-semibold hover:bg-primary/90 shadow-xl shadow-primary/25 hover:scale-[1.02] active:scale-[0.98] transition-all"
          >
            Get started
            <ArrowRight size={18} />
          </button>
        </section>

        <section className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {features.map((f) => (
            <div
              key={f.title}
              className="p-6 rounded-2xl bg-card border border-border hover:border-primary/30 transition-colors"
            >
              <div className="p-2.5 rounded-lg bg-primary/10 border border-primary/20 w-fit mb-4">
                <f.icon className="text-primary" size={20} />
              </div>
              <h3 className="text-lg font-semibold mb-2">{f.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{f.description}</p>
            </div>
          ))}
        </section>

        <section className="mt-16 p-8 rounded-2xl bg-card/80 border border-border text-center">
          <FileSpreadsheet className="mx-auto text-primary mb-4" size={32} />
          <h2 className="text-2xl font-bold mb-2">Ready to automate?</h2>
          <p className="text-muted-foreground mb-6 max-w-lg mx-auto">
            Sign in with Google to access your workflow dashboard and start building.
          </p>
          <button
            type="button"
            onClick={onGetStarted}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-primary text-primary-foreground font-semibold hover:bg-primary/90 transition-all"
          >
            Get started
            <ArrowRight size={16} />
          </button>
        </section>
      </main>
    </div>
  );
};

export default LandingPage;

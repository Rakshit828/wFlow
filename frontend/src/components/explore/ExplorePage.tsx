import React from "react";
import { useNavigate } from "react-router-dom";
import {
  Search,
  Star,
  Globe,
  Lock,
  ChevronLeft,
  ChevronRight,
  Compass,
  LayoutGrid,
  List,
  Loader2,
  RefreshCw,
  ArrowUpRight,
  AlertCircle,
  Workflow,
  User,
} from "lucide-react";
import {
  fetchWorkflows,
  searchWorkflows,
  starWorkflow,
} from "../../api/workflows";
import type { WorkflowListItem, PaginationMeta } from "../../types/workflow";

/* ─── Gradient Card Background Patterns ─── */
const cardGradients = [
  "from-violet-500/10 via-fuchsia-500/5 to-transparent",
  "from-sky-500/10 via-cyan-500/5 to-transparent",
  "from-emerald-500/10 via-teal-500/5 to-transparent",
  "from-rose-500/10 via-pink-500/5 to-transparent",
  "from-amber-500/10 via-orange-500/5 to-transparent",
  "from-indigo-500/10 via-purple-500/5 to-transparent",
];

const accentColors = [
  {
    border: "border-violet-500/20",
    dot: "bg-violet-500",
    text: "text-violet-400",
  },
  { border: "border-sky-500/20", dot: "bg-sky-500", text: "text-sky-400" },
  {
    border: "border-emerald-500/20",
    dot: "bg-emerald-500",
    text: "text-emerald-400",
  },
  { border: "border-rose-500/20", dot: "bg-rose-500", text: "text-rose-400" },
  {
    border: "border-amber-500/20",
    dot: "bg-amber-500",
    text: "text-amber-400",
  },
  {
    border: "border-indigo-500/20",
    dot: "bg-indigo-500",
    text: "text-indigo-400",
  },
];

type ViewMode = "grid" | "list";

export const ExplorePage: React.FC = () => {
  const navigate = useNavigate();
  const [workflows, setWorkflows] = React.useState<WorkflowListItem[]>([]);
  const [pagination, setPagination] = React.useState<PaginationMeta | null>(
    null,
  );
  const [loading, setLoading] = React.useState(false);
  const [searchQuery, setSearchQuery] = React.useState("");
  const [debouncedQuery, setDebouncedQuery] = React.useState("");
  const [page, setPage] = React.useState(1);
  const [viewMode, setViewMode] = React.useState<ViewMode>("grid");
  const [loadError, setLoadError] = React.useState<string | null>(null);

  // Debounce search input
  React.useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery);
      setPage(1);
    }, 400);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Ref guard: track last-fetched params to avoid duplicate requests
  const lastFetchedRef = React.useRef<{ query: string; page: number } | null>(
    null,
  );
  const isFetchingRef = React.useRef(false);

  const loadData = React.useCallback(
    async (force = false) => {
      if (isFetchingRef.current) return;

      if (
        !force &&
        lastFetchedRef.current &&
        lastFetchedRef.current.query === debouncedQuery &&
        lastFetchedRef.current.page === page
      ) {
        return;
      }

      isFetchingRef.current = true;
      setLoading(true);
      setLoadError(null);

      try {
        const result = debouncedQuery
          ? await searchWorkflows(debouncedQuery, page, 10, true)
          : await fetchWorkflows(page, 10, true);
        setWorkflows(result.data.data);
        setPagination(result.data.pagination);
        lastFetchedRef.current = { query: debouncedQuery, page };
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to load workflows";
        setLoadError(message);
        setWorkflows([]);
        setPagination(null);
      } finally {
        setLoading(false);
        isFetchingRef.current = false;
      }
    },
    [page, debouncedQuery],
  );

  React.useEffect(() => {
    loadData();
  }, [loadData]);

  const handleOpenWorkflow = (workflow: WorkflowListItem) => {
    navigate(`/workflow/${workflow.workflow_id}`);
  };

  const handleStar = async (
    e: React.MouseEvent | React.KeyboardEvent,
    workflowId: string,
  ) => {
    e.stopPropagation();
    try {
      const result = await starWorkflow(workflowId);
      setWorkflows((prev) =>
        prev.map((w) =>
          w.workflow_id === workflowId ? { ...w, stars: result.data.stars } : w,
        ),
      );
    } catch { }
  };

  return (
    <div className="h-full overflow-y-auto">
      {/* ─── Hero Section ─── */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-violet-500/5 via-transparent to-transparent pointer-events-none" />
        <div className="absolute top-0 left-1/3 w-96 h-96 bg-violet-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute top-10 right-1/3 w-72 h-72 bg-fuchsia-500/5 rounded-full blur-3xl pointer-events-none" />

        <div className="relative max-w-6xl mx-auto px-6 pt-12 pb-8">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div>
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2.5 rounded-xl bg-violet-500/10 border border-violet-500/20 shadow-lg shadow-violet-500/5">
                  <Compass className="text-violet-400" size={22} />
                </div>
                <div>
                  <h1 className="text-2xl font-bold tracking-tight">
                    Explore Workflows
                  </h1>
                  <p className="text-sm text-muted-foreground mt-0.5">
                    Discover community-built AI automation pipelines. Star, fork,
                    and learn from others.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ─── Controls Bar ─── */}
      <div className="max-w-6xl mx-auto px-6 pb-6">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 mb-6">
          {/* Search */}
          <div className="relative flex-1">
            <Search
              size={15}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none"
            />
            <input
              id="explore-search"
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search all workflows..."
              className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-card border border-border text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-violet-500/50 focus:ring-2 focus:ring-violet-500/10 transition-all"
            />
          </div>

          {/* View toggle */}
          <div className="flex bg-card rounded-xl border border-border overflow-hidden shrink-0">
            <button
              onClick={() => setViewMode("grid")}
              className={`p-2.5 transition-colors ${viewMode === "grid"
                  ? "bg-violet-500/10 text-violet-400"
                  : "text-muted-foreground hover:text-foreground"
                }`}
              title="Grid view"
            >
              <LayoutGrid size={15} />
            </button>
            <button
              onClick={() => setViewMode("list")}
              className={`p-2.5 transition-colors ${viewMode === "list"
                  ? "bg-violet-500/10 text-violet-400"
                  : "text-muted-foreground hover:text-foreground"
                }`}
              title="List view"
            >
              <List size={15} />
            </button>
          </div>

          {/* Refresh */}
          <button
            onClick={() => loadData(true)}
            disabled={loading}
            className="p-2.5 rounded-xl bg-card border border-border text-muted-foreground hover:text-foreground hover:border-violet-500/30 transition-all disabled:opacity-50 shrink-0"
          >
            <RefreshCw size={15} className={loading ? "animate-spin" : ""} />
          </button>
        </div>

        {loadError && (
          <div className="flex items-center gap-2 mb-5 px-4 py-2.5 rounded-xl bg-destructive/10 border border-destructive/30 text-destructive text-sm">
            <AlertCircle size={16} />
            <span>{loadError}</span>
          </div>
        )}

        {/* ─── Loading State ─── */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="text-violet-400 animate-spin" size={28} />
              <span className="text-sm text-muted-foreground">
                Discovering workflows…
              </span>
            </div>
          </div>
        )}

        {/* ─── Grid View ─── */}
        {!loading && viewMode === "grid" && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {workflows.map((w, idx) => {
              const gradient = cardGradients[idx % cardGradients.length];
              const accent = accentColors[idx % accentColors.length];
              return (
                <button
                  key={w.workflow_id}
                  onClick={() => handleOpenWorkflow(w)}
                  className={`group relative text-left p-5 rounded-2xl bg-card border ${accent.border} hover:border-violet-500/30 transition-all duration-300 hover:shadow-lg hover:shadow-violet-500/5 hover:-translate-y-0.5`}
                >
                  {/* Gradient overlay */}
                  <div
                    className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${gradient} pointer-events-none opacity-60 group-hover:opacity-100 transition-opacity`}
                  />

                  <div className="relative">
                    {/* Header row */}
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2.5">
                        <div
                          className={`w-2 h-2 rounded-full ${accent.dot} shadow-sm`}
                        />
                        <h3 className="font-semibold text-sm text-foreground group-hover:text-violet-400 transition-colors leading-tight line-clamp-1">
                          {w.name}
                        </h3>
                      </div>
                      <ArrowUpRight
                        size={14}
                        className="text-muted-foreground opacity-0 group-hover:opacity-100 group-hover:text-violet-400 transition-all -translate-x-1 group-hover:translate-x-0 shrink-0"
                      />
                    </div>

                    {/* Description */}
                    <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2 mb-4">
                      {w.description}
                    </p>

                    {/* Footer metadata */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3 text-xs text-muted-foreground">
                        {w.visibility === "public" ? (
                          <span className="flex items-center gap-1">
                            <Globe size={10} className="text-emerald-400" />
                            Public
                          </span>
                        ) : (
                          <span className="flex items-center gap-1">
                            <Lock size={10} className="text-amber-400" />
                            Private
                          </span>
                        )}
                        <span className="flex items-center gap-1">
                          <User size={10} />
                          {w.created_by}
                        </span>
                      </div>

                      <span
                        role="button"
                        tabIndex={0}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleStar(e, w.workflow_id);
                        }}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" || e.key === " ") {
                            e.preventDefault();
                            e.stopPropagation();
                            handleStar(e, w.workflow_id);
                          }
                        }}
                        className="flex items-center gap-1 text-xs text-muted-foreground hover:text-amber-400 transition-colors cursor-pointer"
                      >
                        <Star
                          size={11}
                          className={
                            w.stars > 0 ? "text-amber-400 fill-amber-400" : ""
                          }
                        />
                        {w.stars}
                      </span>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        )}

        {/* ─── List View ─── */}
        {!loading && viewMode === "list" && (
          <div className="space-y-2">
            {workflows.map((w, idx) => {
              const accent = accentColors[idx % accentColors.length];
              return (
                <button
                  key={w.workflow_id}
                  onClick={() => handleOpenWorkflow(w)}
                  className={`group w-full text-left flex items-center gap-4 p-4 rounded-xl bg-card border ${accent.border} hover:border-violet-500/30 transition-all hover:shadow-md hover:shadow-violet-500/5`}
                >
                  <div
                    className={`w-1.5 h-8 rounded-full ${accent.dot} shrink-0`}
                  />
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-sm text-foreground group-hover:text-violet-400 transition-colors truncate">
                      {w.name}
                    </h3>
                    <p className="text-sm text-muted-foreground truncate mt-0.5">
                      {w.description}
                    </p>
                  </div>
                  <div className="flex items-center gap-4 shrink-0 text-xs text-muted-foreground">
                    {w.visibility === "public" ? (
                      <span className="flex items-center gap-1">
                        <Globe size={10} className="text-emerald-400" />
                        Public
                      </span>
                    ) : (
                      <span className="flex items-center gap-1">
                        <Lock size={10} className="text-amber-400" />
                        Private
                      </span>
                    )}
                    <span className="flex items-center gap-1">
                      <User size={10} />
                      {w.created_by}
                    </span>
                    <span
                      role="button"
                      tabIndex={0}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleStar(e, w.workflow_id);
                      }}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          e.stopPropagation();
                          handleStar(e, w.workflow_id);
                        }
                      }}
                      className="flex items-center gap-1 hover:text-amber-400 transition-colors cursor-pointer"
                    >
                      <Star
                        size={11}
                        className={
                          w.stars > 0 ? "text-amber-400 fill-amber-400" : ""
                        }
                      />
                      {w.stars}
                    </span>
                    <ArrowUpRight
                      size={13}
                      className="text-muted-foreground group-hover:text-violet-400 transition-colors"
                    />
                  </div>
                </button>
              );
            })}
          </div>
        )}

        {/* ─── Empty State ─── */}
        {!loading && workflows.length === 0 && (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="p-4 rounded-2xl bg-muted/50 mb-4">
              <Workflow size={32} className="text-muted-foreground" />
            </div>
            <h3 className="text-base font-semibold text-foreground mb-1">
              No workflows found
            </h3>
            <p className="text-sm text-muted-foreground mb-6 max-w-md">
              {searchQuery
                ? `No workflows match "${searchQuery}". Try a different search term.`
                : "No community workflows are available yet. Be the first to share one!"}
            </p>
          </div>
        )}

        {/* ─── Pagination ─── */}
        {pagination && pagination.total_pages > 1 && (
          <div className="flex items-center justify-center gap-3 mt-8 mb-6">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={!pagination.has_previous}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-card border border-border text-sm text-foreground hover:bg-accent disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              <ChevronLeft size={14} />
              Previous
            </button>
            <div className="flex items-center gap-1">
              {Array.from(
                { length: Math.min(pagination.total_pages, 5) },
                (_, i) => {
                  const pageNum = i + 1;
                  return (
                    <button
                      key={pageNum}
                      onClick={() => setPage(pageNum)}
                      className={`w-9 h-9 rounded-lg text-sm font-medium transition-all ${page === pageNum
                          ? "bg-violet-500 text-white shadow-md shadow-violet-500/20"
                          : "bg-card border border-border text-muted-foreground hover:text-foreground hover:bg-accent"
                        }`}
                    >
                      {pageNum}
                    </button>
                  );
                },
              )}
            </div>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={!pagination.has_next}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-card border border-border text-sm text-foreground hover:bg-accent disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              Next
              <ChevronRight size={14} />
            </button>
          </div>
        )}

        {/* Footer stats */}
        {pagination && (
          <div className="text-center text-sm text-muted-foreground pb-4">
            Showing {workflows.length} of {pagination.total} workflows · Page{" "}
            {pagination.page} of {pagination.total_pages}
          </div>
        )}
      </div>
    </div>
  );
};

export default ExplorePage;

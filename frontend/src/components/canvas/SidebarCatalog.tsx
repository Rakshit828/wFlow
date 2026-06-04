import React from "react";
import {
  Mail,
  FileSpreadsheet,
  FolderUp,
  GitFork,
  Sparkles,
  PlaySquare,
  Wrench,
  ChevronLeft,
  ChevronRight,
  Search,
  Cpu,
  Layers,
  Webhook,
  GripVertical,
  X,
  Package,
} from "lucide-react";
import { useWorkflowStore } from "../../store/useWorkflowStore";
import {
  fetchRegisteredNodes,
  searchRegisteredNodes,
} from "../../api/workflows";
import type { NodesRegistryListItem } from "../../types/workflow";

const getCategoryIcon = (type: string, service?: string | null) => {
  const svc = service?.toLowerCase() || "";
  if (svc.includes("gmail")) {
    return <Mail className="text-rose-400" size={15} />;
  }
  if (svc.includes("sheets")) {
    return <FileSpreadsheet className="text-emerald-400" size={15} />;
  }
  if (svc.includes("drive")) {
    return <FolderUp className="text-sky-400" size={15} />;
  }

  switch (type) {
    case "LLM":
      return <Sparkles className="text-amber-400" size={15} />;
    case "CONTROL_FLOW":
      return <GitFork className="text-purple-400" size={15} />;
    case "TRANSFORM":
      return <Layers className="text-teal-400" size={15} />;
    case "API":
      return <Webhook className="text-indigo-400" size={15} />;
    case "DATA_SOURCE":
      return <Cpu className="text-blue-400" size={15} />;
    default:
      return <Wrench className="text-slate-400" size={15} />;
  }
};

const getTypeColor = (type: string): string => {
  switch (type) {
    case "LLM":
      return "text-amber-400 bg-amber-400/10 border-amber-400/20";
    case "CONTROL_FLOW":
      return "text-purple-400 bg-purple-400/10 border-purple-400/20";
    case "ACTION":
      return "text-blue-400 bg-blue-400/10 border-blue-400/20";
    case "TRANSFORM":
      return "text-teal-400 bg-teal-400/10 border-teal-400/20";
    case "API":
      return "text-indigo-400 bg-indigo-400/10 border-indigo-400/20";
    case "DATA_SOURCE":
      return "text-cyan-400 bg-cyan-400/10 border-cyan-400/20";
    case "TRIGGER":
      return "text-orange-400 bg-orange-400/10 border-orange-400/20";
    default:
      return "text-slate-400 bg-slate-400/10 border-slate-400/20";
  }
};

const getTypeNameLabel = (type: string) => {
  switch (type) {
    case "LLM":
      return "Language Model";
    case "CONTROL_FLOW":
      return "Control Flow";
    case "ACTION":
      return "Integration";
    case "TRANSFORM":
      return "Transform";
    case "API":
      return "External API";
    case "DATA_SOURCE":
      return "Data Source";
    case "TRIGGER":
      return "Trigger";
    default:
      return type;
  }
};

/* Skeleton loading card */
const SkeletonCard: React.FC<{ index: number }> = ({ index }) => (
  <div
    className="flex flex-col p-3 rounded-xl border border-border bg-background/30"
    style={{ animationDelay: `${index * 80}ms` }}
  >
    <div className="flex items-center gap-2">
      <div className="w-8 h-8 rounded skeleton-shimmer shrink-0" />
      <div className="flex-1 space-y-1.5">
        <div className="h-3.5 w-3/4 skeleton-shimmer" />
        <div className="h-2.5 w-1/3 skeleton-shimmer" />
      </div>
    </div>
    <div className="mt-2.5 space-y-1">
      <div className="h-2.5 w-full skeleton-shimmer" />
      <div className="h-2.5 w-2/3 skeleton-shimmer" />
    </div>
  </div>
);

/* Node card component */
const NodeCard: React.FC<{
  node: NodesRegistryListItem;
  index: number;
  fontScale: number;
  onDragStart: (e: React.DragEvent, key: string) => void;
}> = ({ node, index, fontScale, onDragStart }) => {
  const [isDragging, setIsDragging] = React.useState(false);

  // Derive pixel sizes from fontScale so all text in the card scales together.
  // Base sizes (at fontScale=1): name=14px, description=11px, badge=9px, service=10px
  const nameSize = Math.round(14 * fontScale);
  const descSize = Math.round(11 * fontScale);
  const badgeSize = Math.round(9 * fontScale);
  const serviceSize = Math.round(10 * fontScale);

  return (
    <div
      draggable
      onDragStart={(e) => {
        setIsDragging(true);
        onDragStart(e, node.fn_key);
      }}
      onDragEnd={() => setIsDragging(false)}
      className={`animate-catalog-card group flex flex-col p-3 rounded-xl border bg-background/50 cursor-grab active:cursor-grabbing transition-all duration-200 ${
        isDragging
          ? "drag-active border-primary/40 bg-primary/5 scale-[0.98] opacity-80"
          : "border-border hover:bg-accent/40 hover:border-primary/20 hover:shadow-lg hover:shadow-black/10"
      }`}
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <div className="p-1.5 rounded-lg bg-muted/80 border border-border/50 text-foreground shrink-0 group-hover:border-primary/20 transition-colors">
            {getCategoryIcon(node.type, node.service)}
          </div>
          <div className="min-w-0 flex-1">
            <span
              className="font-semibold text-foreground tracking-wide group-hover:text-primary transition-colors block truncate"
              style={{ fontSize: `${nameSize}px` }}
            >
              {node.name}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <span
            className="px-1.5 py-0.5 rounded-md bg-slate-800/80 text-slate-400 font-medium border border-slate-700/50"
            style={{ fontSize: `${serviceSize}px` }}
          >
            {node.service}
          </span>
          <GripVertical
            size={12}
            className="text-muted-foreground/40 group-hover:text-muted-foreground transition-colors"
          />
        </div>
      </div>

      <p
        className="text-muted-foreground mt-2 leading-snug line-clamp-2"
        style={{ fontSize: `${descSize}px` }}
      >
        {node.description}
      </p>

      <div className="flex items-center gap-1.5 mt-2">
        <span
          className={`px-1.5 py-0.5 rounded-md font-semibold border ${getTypeColor(node.type)}`}
          style={{ fontSize: `${badgeSize}px` }}
        >
          {getTypeNameLabel(node.type)}
        </span>
        {node.valid_permissions && node.valid_permissions.length > 0 && (
          <span
            className="px-1 py-0.5 rounded bg-slate-900/50 text-slate-500 font-mono"
            style={{ fontSize: `${badgeSize}px` }}
          >
            {node.valid_permissions.length} perm
            {node.valid_permissions.length > 1 ? "s" : ""}
          </span>
        )}
      </div>
    </div>
  );
};

/* Pagination component */
const PaginationBar: React.FC<{
  page: number;
  totalPages: number;
  total?: number;
  onPrev: () => void;
  onNext: () => void;
}> = ({ page, totalPages, total, onPrev, onNext }) => {
  if (totalPages <= 1) return null;
  return (
    <div className="mt-3 pt-3 border-t border-border flex items-center justify-between shrink-0">
      <button
        onClick={onPrev}
        disabled={page === 1}
        className="p-1.5 rounded-lg border border-border hover:bg-accent text-muted-foreground hover:text-foreground disabled:opacity-30 disabled:pointer-events-none transition-all hover:scale-105 active:scale-95"
      >
        <ChevronLeft size={14} />
      </button>
      <div className="flex flex-col items-center">
        <span className="text-[11px] text-muted-foreground font-semibold">
          {page} / {totalPages}
        </span>
        {total !== undefined && (
          <span className="text-[9px] text-muted-foreground/60">
            {total} total
          </span>
        )}
      </div>
      <button
        onClick={onNext}
        disabled={page === totalPages}
        className="p-1.5 rounded-lg border border-border hover:bg-accent text-muted-foreground hover:text-foreground disabled:opacity-30 disabled:pointer-events-none transition-all hover:scale-105 active:scale-95"
      >
        <ChevronRight size={14} />
      </button>
    </div>
  );
};

interface NodesCacheEntry {
  data: NodesRegistryListItem[];
  pagination: {
    total_pages: number;
    total: number;
  };
}

// Module-level caches and promises to survive React Strict Mode mount/unmount/remount
const allNodesCache = new Map<number, NodesCacheEntry>();
const allNodesPromises = new Map<number, Promise<NodesCacheEntry>>();

const exploreNodesCache = new Map<string, NodesCacheEntry>();
const exploreNodesPromises = new Map<string, Promise<NodesCacheEntry>>();

export const SidebarCatalog: React.FC<{
  sidebarWidth: number;
  onToggleCollapse: () => void;
}> = ({ sidebarWidth, onToggleCollapse }) => {
  const { addRegistryItems } = useWorkflowStore();
  const [activeTab, setActiveTab] = React.useState<"all" | "explore">("all");

  // fontScale: 250px (min) = 0.85, 310px (default) = 1, 600px (max) = 1.35
  // Used ONLY for NodeCard text — not for headers or tab labels.
  const fontScale = Math.max(
    0.85,
    Math.min(1.35, (sidebarWidth - 250) / 350 + 0.85),
  );

  // All Nodes Tab State
  const [allNodes, setAllNodes] = React.useState<NodesRegistryListItem[]>([]);
  const [allPage, setAllPage] = React.useState(1);
  const [allTotalPages, setAllTotalPages] = React.useState(1);
  const [allTotal, setAllTotal] = React.useState(0);
  const [allLoading, setAllLoading] = React.useState(false);
  const [allError, setAllError] = React.useState<string | null>(null);

  // Explore Tab State
  const [exploreNodes, setExploreNodes] = React.useState<
    NodesRegistryListItem[]
  >([]);
  const [selectedType, setSelectedType] = React.useState<string>("ACTION");
  const [searchService, setSearchService] = React.useState("");
  const [debouncedService, setDebouncedService] = React.useState("");
  const [explorePage, setExplorePage] = React.useState(1);
  const [exploreTotalPages, setExploreTotalPages] = React.useState(1);
  const [exploreTotal, setExploreTotal] = React.useState(0);
  const [exploreLoading, setExploreLoading] = React.useState(false);
  const [exploreError, setExploreError] = React.useState<string | null>(null);

  const [contentKey, setContentKey] = React.useState(0);

  const PAGE_SIZE = 6;

  React.useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedService(searchService);
      setExplorePage(1);
    }, 400);
    return () => clearTimeout(timer);
  }, [searchService]);

  // Ref guards: track last-fetched params
  const lastAllRef = React.useRef<{ page: number } | null>(null);
  const lastExploreRef = React.useRef<{ type: string; service: string; page: number } | null>(null);

  const loadAllNodes = React.useCallback(
    async (page: number) => {
      // 1. Check if cached
      const cached = allNodesCache.get(page);
      if (cached) {
        setAllNodes(cached.data);
        setAllTotalPages(cached.pagination.total_pages);
        setAllTotal(cached.pagination.total);
        addRegistryItems(cached.data);
        setContentKey((k) => k + 1);
        lastAllRef.current = { page };
        return;
      }

      // 2. Check if a promise is already in flight for this page
      let promise = allNodesPromises.get(page);
      if (!promise) {
        // Create the promise and cache it
        promise = (async () => {
          const res = await fetchRegisteredNodes(page, PAGE_SIZE);
          const entry: NodesCacheEntry = {
            data: res.data,
            pagination: {
              total_pages: res.pagination.total_pages,
              total: res.pagination.total,
            },
          };
          allNodesCache.set(page, entry);
          return entry;
        })();
        allNodesPromises.set(page, promise);

        // Clean up the promise map when it resolves or rejects
        promise.finally(() => {
          allNodesPromises.delete(page);
        });
      }

      setAllLoading(true);
      setAllError(null);
      try {
        const res = await promise;
        setAllNodes(res.data);
        setAllTotalPages(res.pagination.total_pages);
        setAllTotal(res.pagination.total);
        addRegistryItems(res.data);
        setContentKey((k) => k + 1);
        lastAllRef.current = { page };
      } catch (err) {
        setAllError(
          err instanceof Error ? err.message : "Failed to fetch nodes",
        );
      } finally {
        setAllLoading(false);
      }
    },
    [addRegistryItems],
  );

  const loadExploreNodes = React.useCallback(
    async (type: string, service: string, page: number) => {
      const cacheKey = `${type}:${service}:${page}`;

      // 1. Check if cached
      const cached = exploreNodesCache.get(cacheKey);
      if (cached) {
        setExploreNodes(cached.data);
        setExploreTotalPages(cached.pagination.total_pages);
        setExploreTotal(cached.pagination.total);
        addRegistryItems(cached.data);
        setContentKey((k) => k + 1);
        lastExploreRef.current = { type, service, page };
        return;
      }

      // 2. Check if a promise is already in flight for this key
      let promise = exploreNodesPromises.get(cacheKey);
      if (!promise) {
        promise = (async () => {
          const res = await searchRegisteredNodes(
            type,
            service || undefined,
            page,
            PAGE_SIZE,
          );
          const entry: NodesCacheEntry = {
            data: res.data,
            pagination: {
              total_pages: res.pagination.total_pages,
              total: res.pagination.total,
            },
          };
          exploreNodesCache.set(cacheKey, entry);
          return entry;
        })();
        exploreNodesPromises.set(cacheKey, promise);

        promise.finally(() => {
          exploreNodesPromises.delete(cacheKey);
        });
      }

      setExploreLoading(true);
      setExploreError(null);
      try {
        const res = await promise;
        setExploreNodes(res.data);
        setExploreTotalPages(res.pagination.total_pages);
        setExploreTotal(res.pagination.total);
        addRegistryItems(res.data);
        setContentKey((k) => k + 1);
        lastExploreRef.current = { type, service, page };
      } catch (err) {
        setExploreError(
          err instanceof Error ? err.message : "Failed to explore nodes",
        );
      } finally {
        setExploreLoading(false);
      }
    },
    [addRegistryItems],
  );

  React.useEffect(() => {
    if (activeTab === "all") {
      loadAllNodes(allPage);
    }
  }, [activeTab, allPage, loadAllNodes]);

  React.useEffect(() => {
    if (activeTab === "explore") {
      loadExploreNodes(selectedType, debouncedService, explorePage);
    }
  }, [
    activeTab,
    selectedType,
    debouncedService,
    explorePage,
    loadExploreNodes,
  ]);

  const onDragStart = (event: React.DragEvent, nodeKey: string) => {
    event.dataTransfer.setData("application/reactflow-nodekey", nodeKey);
    event.dataTransfer.effectAllowed = "move";
  };

  const renderError = (error: string) => (
    <div className="flex-1 flex items-center justify-center p-4 text-center animate-content-switch">
      <div className="text-xs text-destructive bg-destructive/10 border border-destructive/20 p-3.5 rounded-xl leading-normal max-w-full">
        <p className="font-semibold mb-1">Connection Error</p>
        <p className="text-destructive/80">{error}</p>
      </div>
    </div>
  );

  const renderEmpty = (message: string) => (
    <div className="flex-1 flex flex-col items-center justify-center p-6 text-center animate-content-switch">
      <Package size={32} className="text-muted-foreground/30 mb-3" />
      <p className="text-xs text-muted-foreground leading-relaxed">{message}</p>
    </div>
  );

  const renderLoading = () => (
    <div className="flex-1 flex flex-col min-h-0 animate-content-switch">
      <div className="flex-1 overflow-y-auto space-y-3 pr-1">
        {Array.from({ length: PAGE_SIZE }).map((_, i) => (
          <SkeletonCard key={i} index={i} />
        ))}
      </div>
    </div>
  );

  return (
    <aside className="w-full h-full border-r border-border bg-card flex flex-col select-none shrink-0 overflow-hidden">
      {/* Title Header — fixed size, no fontScale */}
      <div className="p-4 border-b border-border bg-muted/20">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-base text-foreground uppercase tracking-wider flex items-center gap-2">
            <PlaySquare className="text-primary" size={18} />
            Nodes catalog
          </h3>
          <div className="flex items-center gap-2">
            {allTotal > 0 && (
              <span className="animate-badge text-[10px] font-bold px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20">
                {allTotal}
              </span>
            )}
            <button
              type="button"
              onClick={onToggleCollapse}
              className="h-9 w-9 place-items-center rounded-lg border border-border bg-background/80 text-muted-foreground hover:text-foreground hover:bg-primary/10 transition-all"
              title="Collapse sidebar"
            >
              <ChevronLeft size={16} />
            </button>
          </div>
        </div>
        <p className="text-[11px] text-muted-foreground mt-1.5 leading-snug">
          Drag and drop nodes onto the canvas to construct your workflow.
        </p>
      </div>

      {/* Tab Headers — fixed size, no fontScale */}
      <div className="flex border-b border-border text-xs font-bold bg-muted/10 shrink-0 relative">
        <button
          onClick={() => setActiveTab("all")}
          className={`flex-1 py-3 text-center uppercase tracking-wider transition-all border-b-2 tab-indicator ${
            activeTab === "all"
              ? "text-primary border-primary bg-background/20"
              : "text-muted-foreground border-transparent hover:text-foreground"
          }`}
        >
          All Nodes
        </button>
        <button
          onClick={() => setActiveTab("explore")}
          className={`flex-1 py-3 text-center uppercase tracking-wider transition-all border-b-2 tab-indicator ${
            activeTab === "explore"
              ? "text-primary border-primary bg-background/20"
              : "text-muted-foreground border-transparent hover:text-foreground"
          }`}
        >
          Explore
        </button>
      </div>

      {/* Content Area */}
      <div className="flex-1 flex flex-col min-h-0">
        {activeTab === "all" ? (
          <div
            className="flex-1 flex flex-col min-h-0 p-4"
            key={`all-${contentKey}`}
          >
            {allLoading ? (
              renderLoading()
            ) : allError ? (
              renderError(allError)
            ) : allNodes.length === 0 ? (
              renderEmpty("No nodes registered in backend registry.")
            ) : (
              <div className="flex-1 overflow-y-auto space-y-2.5 pr-1 animate-content-switch">
                {allNodes.map((node, i) => (
                  <NodeCard
                    key={node.fn_key}
                    node={node}
                    index={i}
                    fontScale={fontScale}
                    onDragStart={onDragStart}
                  />
                ))}
              </div>
            )}

            {!allLoading && !allError && (
              <PaginationBar
                page={allPage}
                totalPages={allTotalPages}
                total={allTotal}
                onPrev={() => setAllPage((p) => Math.max(1, p - 1))}
                onNext={() => setAllPage((p) => Math.min(allTotalPages, p + 1))}
              />
            )}
          </div>
        ) : (
          <div
            className="flex-1 flex flex-col min-h-0 p-4 animate-content-switch"
            key={`explore-${contentKey}`}
          >
            {/* Search Header — fixed size, no fontScale */}
            <div className="space-y-3 mb-4 shrink-0">
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                  Node Type
                </label>
                <select
                  value={selectedType}
                  onChange={(e) => {
                    setSelectedType(e.target.value);
                    setExplorePage(1);
                  }}
                  className="w-full text-xs rounded-lg bg-background border border-border px-2.5 py-2 text-foreground focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all"
                >
                  <option value="ACTION">Action / Integrations</option>
                  <option value="LLM">AI Language Models (LLM)</option>
                  <option value="CONTROL_FLOW">Logical Control Flow</option>
                  <option value="TRANSFORM">Data Transformations</option>
                  <option value="API">External APIs</option>
                  <option value="DATA_SOURCE">Data Sources</option>
                  <option value="TRIGGER">Event Triggers</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                  Filter by Service
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={searchService}
                    onChange={(e) => setSearchService(e.target.value)}
                    placeholder="e.g. google.gmail, groq"
                    className="w-full text-xs rounded-lg bg-background border border-border pl-8 pr-8 py-2 text-foreground focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 transition-all"
                  />
                  <Search
                    className="absolute left-2.5 top-2.5 text-muted-foreground/60"
                    size={13}
                  />
                  {searchService && (
                    <button
                      type="button"
                      onClick={() => setSearchService("")}
                      className="absolute right-2 top-2 p-0.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                    >
                      <X size={12} />
                    </button>
                  )}
                </div>
                {debouncedService && (
                  <p className="text-[9px] text-muted-foreground/60 mt-0.5 animate-tooltip">
                    Filtering by "{debouncedService}" · {exploreTotal} result
                    {exploreTotal !== 1 ? "s" : ""}
                  </p>
                )}
              </div>
            </div>

            {exploreLoading ? (
              renderLoading()
            ) : exploreError ? (
              renderError(exploreError)
            ) : exploreNodes.length === 0 ? (
              renderEmpty(
                `No matching nodes for type "${getTypeNameLabel(selectedType)}"${debouncedService ? ` and service "${debouncedService}"` : ""}.`,
              )
            ) : (
              <div className="flex-1 overflow-y-auto space-y-2.5 pr-1 animate-content-switch">
                {exploreNodes.map((node, i) => (
                  <NodeCard
                    key={node.fn_key}
                    node={node}
                    index={i}
                    fontScale={fontScale}
                    onDragStart={onDragStart}
                  />
                ))}
              </div>
            )}

            {!exploreLoading && !exploreError && (
              <PaginationBar
                page={explorePage}
                totalPages={exploreTotalPages}
                total={exploreTotal}
                onPrev={() => setExplorePage((p) => Math.max(1, p - 1))}
                onNext={() =>
                  setExplorePage((p) => Math.min(exploreTotalPages, p + 1))
                }
              />
            )}
          </div>
        )}
      </div>
    </aside>
  );
};

export default SidebarCatalog;

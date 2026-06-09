import React from "react";
import type { NodeFullResponse as WorkflowNode } from "../../../types/workflow";
import { X, Plus, Zap, Copy, Check } from "lucide-react";

// ─── Constants ────────────────────────────────────────────────────────────────

const OPERATORS = [
  { label: "equals", value: "==" },
  { label: "not equals", value: "!=" },
  { label: "greater than", value: ">" },
  { label: "greater than or equal", value: ">=" },
  { label: "less than", value: "<" },
  { label: "less than or equal", value: "<=" },
  { label: "contains", value: "contains" },
  { label: "not contains", value: "not contains" },
];

// ─── Types ────────────────────────────────────────────────────────────────────

type ConditionJoiner = "and" | "or";

/** Internal row – adds a stable `id` that never appears in the output string */
type ConditionRow = {
  id: string;
  key: string;
  operator: string;
  value: string;
  joiner?: ConditionJoiner;
};

interface ConditionBuilderProps {
  current: string;
  precedingNodes: WorkflowNode[];
  onChange: (condition: string) => void;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

let _id = 0;
const uid = () => `cr-${++_id}`;

const escapeRe = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

const parseConditionString = (condition: string): ConditionRow[] => {
  const trimmed = (condition ?? "").trim();
  if (!trimmed) return [{ id: uid(), key: "", operator: "==", value: "" }];

  const tokens = trimmed.split(/\s+(and|or)\s+/i).filter(Boolean);
  const rows: ConditionRow[] = [];

  for (let i = 0; i < tokens.length; i += 2) {
    const segment = (tokens[i] ?? "").trim();
    const nextJoiner = (
      tokens[i + 1] as ConditionJoiner | undefined
    )?.toLowerCase() as ConditionJoiner | undefined;

    const matched = OPERATORS.find((op) =>
      new RegExp(`\\s*${escapeRe(op.value)}\\s*`, "i").test(segment),
    );

    if (!matched) {
      rows.push({
        id: uid(),
        key: segment,
        operator: "==",
        value: "",
        joiner: nextJoiner,
      });
      continue;
    }

    const parts = segment.split(
      new RegExp(`\\s*${escapeRe(matched.value)}\\s*`, "i"),
    );
    rows.push({
      id: uid(),
      key: (parts[0] ?? "").trim(),
      operator: matched.value,
      value: (parts[1] ?? "").trim(),
      joiner: nextJoiner,
    });
  }

  return rows.length > 0
    ? rows
    : [{ id: uid(), key: "", operator: "==", value: "" }];
};

const buildConditionString = (rows: ConditionRow[]): string =>
  rows
    .map((row, i) => {
      const expr =
        `${row.key.trim()} ${row.operator} ${row.value.trim()}`.trim();
      const joiner = row.joiner
        ? ` ${row.joiner} `
        : i < rows.length - 1
          ? " and "
          : "";
      return `${expr}${joiner}`;
    })
    .join("");

// ─── Main component ───────────────────────────────────────────────────────────

export const ConditionBuilder: React.FC<ConditionBuilderProps> = ({
  current,
  precedingNodes,
  onChange,
}) => {
  const [rows, setRows] = React.useState<ConditionRow[]>(() =>
    parseConditionString(current),
  );
  const [copied, setCopied] = React.useState(false);

  // Sync when `current` prop changes from outside
  React.useEffect(() => {
    setRows(parseConditionString(current));
  }, [current]);

  // ── Mutation helpers ────────────────────────────────────────────────────────
  //
  // IMPORTANT: field edits must NOT call renderRows / rebuild the row list.
  // We update the row data and re-emit onChange, but React reconciles the
  // existing <input> DOM nodes in-place (because key={row.id} is stable),
  // so focus is never stolen.

  const patchRow = (id: string, patch: Partial<ConditionRow>) => {
    setRows((prev) => {
      const next = prev.map((r) => (r.id === id ? { ...r, ...patch } : r));
      onChange(buildConditionString(next));
      return next;
    });
  };

  const addRow = () => {
    setRows((prev) => {
      const withJoiner = prev.map((r, i) =>
        i === prev.length - 1 && !r.joiner
          ? { ...r, joiner: "and" as ConditionJoiner }
          : r,
      );
      const next = [
        ...withJoiner,
        { id: uid(), key: "", operator: "==", value: "" },
      ];
      onChange(buildConditionString(next));
      return next;
    });
  };

  const removeRow = (id: string) => {
    setRows((prev) => {
      const idx = prev.findIndex((r) => r.id === id);
      let next = prev.filter((r) => r.id !== id);

      if (next.length === 0) {
        return [{ id: uid(), key: "", operator: "==", value: "" }];
      }
      // carry the removed row's joiner up to its predecessor
      if (idx > 0) {
        next = next.map((r, i) =>
          i === idx - 1 ? { ...r, joiner: prev[idx].joiner } : r,
        );
      }
      // last row never has a joiner
      next[next.length - 1] = { ...next[next.length - 1], joiner: undefined };
      onChange(buildConditionString(next));
      return next;
    });
  };

  const handleDrop = (
    e: React.DragEvent<HTMLInputElement>,
    id: string,
    field: "key" | "value",
  ) => {
    e.preventDefault();
    const path = e.dataTransfer.getData("application/x-output-path");
    if (path) patchRow(id, { [field]: path });
  };

  const copyExpr = () => {
    const expr = buildConditionString(rows);
    navigator.clipboard?.writeText(expr);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };

  const isEmpty = rows.length === 1 && !rows[0].key && !rows[0].value;

  return (
    <div className="rounded-2xl border border-border bg-card shadow-2xl overflow-hidden">
      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-muted/10">
        <div className="flex items-center gap-2.5">
          <span className="flex items-center justify-center w-6 h-6 rounded-md bg-primary/10 border border-primary/20">
            <Zap size={12} className="text-primary" strokeWidth={2.5} />
          </span>
          <div>
            <p className="text-[13px] font-semibold text-foreground leading-none">
              Condition builder
            </p>
            <p className="text-[11px] text-muted-foreground mt-0.5 leading-none">
              Build expressions · drag node outputs into fields
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={addRow}
          className="
            flex items-center gap-1.5
            rounded-lg border border-border bg-muted/50
            px-2.5 py-1.5
            text-[11px] font-medium text-foreground
            hover:bg-accent hover:border-muted-foreground hover:text-foreground
            active:scale-95 transition-all duration-100 cursor-pointer
          "
        >
          <Plus size={11} strokeWidth={2.5} />
          Add rule
        </button>
      </div>

      {/* ── Rows ────────────────────────────────────────────────────────────── */}
      <div className="px-3 pt-3 pb-1 flex flex-col gap-1">
        {rows.map((row, index) => (
          <React.Fragment key={row.id}>
            <ConditionRowCard
              row={row}
              canRemove={rows.length > 1}
              onPatch={(patch) => patchRow(row.id, patch)}
              onRemove={() => removeRow(row.id)}
              onDrop={handleDrop}
            />

            {/* joiner between rows */}
            {index < rows.length - 1 && (
              <JoinerBar
                value={row.joiner ?? "and"}
                onChange={(v) => patchRow(row.id, { joiner: v })}
              />
            )}
          </React.Fragment>
        ))}
      </div>

      {/* ── Expression preview ──────────────────────────────────────────────── */}
      <div className="mx-3 mt-2 mb-3 rounded-xl border border-border bg-muted/20 overflow-hidden">
        <div className="flex items-center justify-between px-3 py-1.5 border-b border-border">
          <span className="text-[9px] font-bold uppercase tracking-[0.12em] text-muted-foreground">
            Expression
          </span>
          <button
            type="button"
            onClick={copyExpr}
            disabled={isEmpty}
            className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground disabled:opacity-30 disabled:pointer-events-none transition-colors cursor-pointer"
          >
            {copied ? (
              <>
                <Check size={10} className="text-emerald-500" />
                <span className="text-emerald-500">Copied</span>
              </>
            ) : (
              <>
                <Copy size={10} />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
        <div className="px-3 py-2 font-mono text-[11px] leading-relaxed min-h-[32px] break-all">
          {isEmpty ? (
            <span className="text-muted-foreground/60 italic">No conditions yet…</span>
          ) : (
            <ExprTokens rows={rows} />
          )}
        </div>
      </div>

      {/* ── Preceding node outputs ──────────────────────────────────────────── */}
      {precedingNodes.length > 0 && (
        <div className="mx-3 mb-3 rounded-xl border border-border bg-muted/20 overflow-hidden">
          <div className="px-3 py-1.5 border-b border-border">
            <span className="text-[9px] font-bold uppercase tracking-[0.12em] text-muted-foreground">
              Node outputs
            </span>
            <span className="ml-2 text-[10px] text-muted-foreground">
              drag into any field
            </span>
          </div>
          <div className="p-2 flex flex-wrap gap-1.5">
            {precedingNodes.map((node) => (
              <NodeChip key={node.name} name={node.name} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// ─── ConditionRowCard ─────────────────────────────────────────────────────────

interface ConditionRowCardProps {
  row: ConditionRow;
  canRemove: boolean;
  onPatch: (patch: Partial<ConditionRow>) => void;
  onRemove: () => void;
  onDrop: (
    e: React.DragEvent<HTMLInputElement>,
    id: string,
    field: "key" | "value",
  ) => void;
}

const ConditionRowCard: React.FC<ConditionRowCardProps> = ({
  row,
  canRemove,
  onPatch,
  onRemove,
  onDrop,
}) => {
  const [dropField, setDropField] = React.useState<"key" | "value" | null>(
    null,
  );

  const inputCls = (field: "key" | "value") =>
    [
      "w-full rounded-lg px-2.5 py-[7px]",
      "border bg-background text-[12px] text-foreground",
      "font-mono placeholder:text-muted-foreground",
      "outline-none transition-all duration-100",
      "focus:ring-1",
      dropField === field
        ? "border-primary/70 ring-primary/20 bg-primary/5"
        : "border-border hover:border-muted-foreground focus:border-primary focus:ring-primary/15",
    ].join(" ");

  return (
    <div className="grid grid-cols-[1fr_auto_1fr_auto] items-center gap-2 px-2 py-2 rounded-xl bg-muted/40 hover:bg-muted/60 transition-colors group">
      {/* Field */}
      <input
        value={row.key}
        onChange={(e) => onPatch({ key: e.target.value })}
        onDrop={(e) => {
          onDrop(e, row.id, "key");
          setDropField(null);
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setDropField("key");
        }}
        onDragLeave={() => setDropField(null)}
        placeholder="field"
        autoComplete="off"
        spellCheck={false}
        className={inputCls("key")}
      />

      {/* Operator */}
      <select
        value={row.operator}
        onChange={(e) => onPatch({ operator: e.target.value })}
        className="
          rounded-lg border border-border bg-background
          px-2 py-[7px] text-[11px] font-semibold text-primary
          outline-none cursor-pointer
          hover:border-muted-foreground focus:border-primary
          focus:ring-1 focus:ring-primary/15
          transition-all duration-100
        "
      >
        {OPERATORS.map((op) => (
          <option key={op.value} value={op.value}>
            {op.label}
          </option>
        ))}
      </select>

      {/* Value */}
      <input
        value={row.value}
        onChange={(e) => onPatch({ value: e.target.value })}
        onDrop={(e) => {
          onDrop(e, row.id, "value");
          setDropField(null);
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setDropField("value");
        }}
        onDragLeave={() => setDropField(null)}
        placeholder="value"
        autoComplete="off"
        spellCheck={false}
        className={inputCls("value")}
      />

      {/* Remove */}
      <button
        type="button"
        onClick={onRemove}
        disabled={!canRemove}
        aria-label="Remove rule"
        className="
          flex items-center justify-center w-7 h-7 rounded-lg
          border border-transparent text-transparent
          group-hover:border-border group-hover:text-muted-foreground
          hover:!border-destructive/40 hover:!bg-destructive/10 hover:!text-destructive
          disabled:!opacity-0 disabled:pointer-events-none
          active:scale-90 transition-all duration-100 cursor-pointer
        "
      >
        <X size={12} strokeWidth={2.5} />
      </button>
    </div>
  );
};

// ─── JoinerBar ────────────────────────────────────────────────────────────────

const JoinerBar: React.FC<{
  value: ConditionJoiner;
  onChange: (v: ConditionJoiner) => void;
}> = ({ value, onChange }) => (
  <div className="flex items-center gap-2 pl-4 py-[3px]">
    <div className="w-px h-4 bg-border" />
    <div className="flex rounded-md border border-border bg-background p-[2px] gap-[2px]">
      {(["and", "or"] as ConditionJoiner[]).map((opt) => {
        const active = value === opt;
        return (
          <button
            key={opt}
            type="button"
            onClick={() => onChange(opt)}
            className={[
              "rounded px-2.5 py-[2px] text-[10px] font-bold tracking-widest uppercase cursor-pointer",
              "border transition-all duration-100",
              active && opt === "and"
                ? "bg-primary/15 text-primary border-primary/25"
                : active && opt === "or"
                  ? "bg-amber-500/15 text-amber-600 border-amber-500/25 dark:text-amber-300"
                  : "text-muted-foreground border-transparent hover:text-foreground",
            ].join(" ")}
          >
            {opt}
          </button>
        );
      })}
    </div>
  </div>
);

// ─── ExprTokens ───────────────────────────────────────────────────────────────

const ExprTokens: React.FC<{ rows: ConditionRow[] }> = ({ rows }) => (
  <>
    {rows.map((row, i) => (
      <React.Fragment key={row.id}>
        <span className="text-sky-400 italic">
          {row.key || <em className="opacity-25 not-italic">_</em>}
        </span>
        <span className="text-violet-400 font-bold mx-1">{row.operator}</span>
        <span className="text-emerald-400">
          {row.value || <em className="opacity-25 not-italic">_</em>}
        </span>
        {i < rows.length - 1 && (
          <span className="mx-1.5 text-[9px] font-extrabold tracking-[0.1em] uppercase text-amber-400">
            {row.joiner ?? "and"}
          </span>
        )}
      </React.Fragment>
    ))}
  </>
);

// ─── NodeChip ─────────────────────────────────────────────────────────────────

const NodeChip: React.FC<{ name: string }> = ({ name }) => (
  <div
    draggable
    onDragStart={(e) =>
      e.dataTransfer.setData("application/x-output-path", name)
    }
    className="
      flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg
      border border-border bg-muted/60
      text-[11px] font-mono text-foreground/80
      cursor-grab active:cursor-grabbing
      hover:border-primary/35 hover:bg-primary/5 hover:text-primary
      select-none transition-all duration-100
    "
  >
    <span className="text-[9px] text-muted-foreground leading-none">⠿</span>
    {name}
  </div>
);

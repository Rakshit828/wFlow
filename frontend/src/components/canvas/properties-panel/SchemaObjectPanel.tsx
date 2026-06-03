import React from "react";
import { Check, Copy } from "lucide-react";
import { jsonSchemaToObject } from "../../../lib/jsonSchemaToObj";

interface SchemaObjectPanelProps {
  title: string;
  description?: string;
  schema: Record<string, any> | null | undefined;
}

export const SchemaObjectPanel: React.FC<SchemaObjectPanelProps> = ({
  title,
  description,
  schema,
}) => {
  const [copied, setCopied] = React.useState(false);

  const schemaPreview = React.useMemo(() => {
    if (!schema) {
      return "// No schema available.";
    }

    try {
      const objectSchema = jsonSchemaToObject(schema);
      return JSON.stringify(objectSchema, null, 2);
    } catch (error) {
      return `// Unable to convert schema: ${
        error instanceof Error ? error.message : String(error)
      }`;
    }
  }, [schema]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(schemaPreview);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };

  return (
    <div className="rounded-3xl border border-slate-700 bg-slate-950/80 p-4 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-foreground">{title}</div>
          {description ? (
            <p className="text-xs text-slate-400 mt-1">{description}</p>
          ) : null}
        </div>
        <button
          type="button"
          onClick={handleCopy}
          className="inline-flex items-center gap-2 rounded-2xl border border-slate-700 bg-slate-900/90 px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-800 transition-all"
        >
          {copied ? <Check size={14} /> : <Copy size={14} />}
          {copied ? "Copied" : "Copy schema"}
        </button>
      </div>
      <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/90 p-3 text-xs text-slate-200 font-mono leading-relaxed">
        <pre className="whitespace-pre-wrap wrap-break-word">
          {schemaPreview}
        </pre>
      </div>
    </div>
  );
};

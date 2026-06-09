import React from "react";
import * as jsf from "json-schema-faker";
import { Copy, Check } from "lucide-react";

interface SchemaExamplePanelProps {
  title: string;
  schema: Record<string, any> | null | undefined;
  description?: string;
}

const normalizeSchemaForExample = (schema: Record<string, any>) => {
  const normalized = { ...schema };
  if (!normalized.type && normalized.properties) {
    normalized.type = "object";
  }
  return normalized;
};

const isEmptyObject = (value: unknown) => {
  return (
    value &&
    typeof value === "object" &&
    !Array.isArray(value) &&
    Object.keys(value).length === 0
  );
};

const buildSampleFromSchema = (schema: Record<string, any>): unknown => {
  if (!schema || typeof schema !== "object") return null;
  if (Array.isArray(schema.enum) && schema.enum.length > 0) {
    return schema.enum[0];
  }

  const type = schema.type ?? (schema.properties ? "object" : "string");

  switch (type) {
    case "string":
      if (schema.const !== undefined) return schema.const;
      if (schema.default !== undefined) return schema.default;
      if (schema.format === "date-time") return new Date().toISOString();
      if (schema.format === "email") return "user@example.com";
      return schema.examples?.[0] ?? schema.example ?? "string";
    case "integer":
    case "number":
      return schema.default ?? schema.examples?.[0] ?? 0;
    case "boolean":
      return schema.default ?? true;
    case "array": {
      const itemSchema = schema.items ?? { type: "string" };
      return [buildSampleFromSchema(itemSchema)];
    }
    case "object": {
      const props = schema.properties ?? {};
      const result: Record<string, unknown> = {};
      Object.entries(props).forEach(([key, propSchema]) => {
        result[key] = buildSampleFromSchema(propSchema as Record<string, any>);
      });
      return result;
    }
    default:
      return null;
  }
};

export const SchemaExamplePanel: React.FC<SchemaExamplePanelProps> = ({
  title,
  schema,
  description,
}) => {
  const [copied, setCopied] = React.useState(false);
  const [sample, setSample] = React.useState<unknown>(null);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);

  React.useEffect(() => {
    let isMounted = true;

    if (!schema || typeof schema !== "object") {
      setSample(null);
      setErrorMessage(null);
      return;
    }

    const normalized = normalizeSchemaForExample(schema);
    setSample(null);
    setErrorMessage(null);

    jsf
      .generate(normalized)
      .then((generated) => {
        if (!isMounted) return;
        if (isEmptyObject(generated) && normalized.properties) {
          setSample(buildSampleFromSchema(normalized));
        } else {
          setSample(generated);
        }
      })
      .catch((error) => {
        if (isMounted) {
          if (normalized.properties) {
            setSample(buildSampleFromSchema(normalized));
          } else {
            setErrorMessage(
              error?.message ||
                "Unable to generate an example from this schema.",
            );
          }
        }
      });

    return () => {
      isMounted = false;
    };
  }, [schema]);

  const sampleJson = errorMessage
    ? `// ${errorMessage}`
    : sample
      ? JSON.stringify(sample, null, 2)
      : "// Generating example...";

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(sampleJson);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };

  return (
    <div className="rounded-2xl border border-border bg-card/50 p-4 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-foreground">{title}</div>
          {description && (
            <p className="text-xs text-muted-foreground mt-1">{description}</p>
          )}
        </div>
        <button
          type="button"
          onClick={handleCopy}
          className="inline-flex items-center gap-2 rounded-2xl border border-border bg-muted px-3 py-2 text-xs font-semibold text-foreground hover:bg-accent transition-all cursor-pointer"
        >
          {copied ? <Check size={14} /> : <Copy size={14} />}
          {copied ? "Copied" : "Copy JSON"}
        </button>
      </div>
      <div className="overflow-x-auto rounded-xl border border-border bg-muted/30 p-3 text-xs text-foreground font-mono leading-relaxed">
        <pre className="whitespace-pre-wrap wrap-break-word">{sampleJson}</pre>
      </div>
    </div>
  );
};

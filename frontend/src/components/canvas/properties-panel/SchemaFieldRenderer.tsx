import React from "react";
import {
  parseInputArrayString,
  safeParseJson,
  serializeInputValue,
} from "./utils";

interface SchemaFieldRendererProps {
  fieldKey: string;
  schema: Record<string, any>;
  value: unknown;
  onChange: (value: unknown) => void;
  onDropReference?: (path: string) => void;
}

export const SchemaFieldRenderer: React.FC<SchemaFieldRendererProps> = ({
  fieldKey,
  schema,
  value,
  onChange,
  onDropReference,
}) => {
  const schemaType = schema?.type || "string";
  const title = schema?.title || fieldKey;
  const description = schema?.description;
  const isTextarea =
    schemaType === "string" &&
    (schema.format === "textarea" || schema.maxLength > 120);
  const serializedValue = serializeInputValue(value);

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const path = event.dataTransfer.getData("application/x-output-path");
    if (path && onDropReference) {
      onDropReference(path);
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    if (onDropReference) {
      event.preventDefault();
      event.dataTransfer.dropEffect = "copy";
    }
  };

  const renderField = () => {
    if (Array.isArray(schema.enum) && schema.enum.length > 0) {
      return (
        <select
          value={value == null ? "" : String(value)}
          onChange={(e) => onChange(e.target.value)}
          className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors"
        >
          <option value="">Select option...</option>
          {schema.enum.map((option: string) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      );
    }

    if (schemaType === "boolean") {
      return (
        <select
          value={value === true ? "true" : value === false ? "false" : ""}
          onChange={(e) => onChange(e.target.value === "true")}
          className="w-full rounded-lg bg-background border border-border px-2 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors"
        >
          <option value="">Select value...</option>
          <option value="true">True</option>
          <option value="false">False</option>
        </select>
      );
    }

    if (schemaType === "integer" || schemaType === "number") {
      return (
        <input
          type="number"
          value={value == null ? "" : String(value)}
          onChange={(e) => {
            const nextValue = e.target.value;
            onChange(
              nextValue === ""
                ? undefined
                : schemaType === "integer"
                  ? parseInt(nextValue, 10)
                  : parseFloat(nextValue),
            );
          }}
          className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors"
        />
      );
    }

    if (schemaType === "array" && schema.items?.type === "string") {
      return (
        <div className="space-y-1">
          <input
            type="text"
            value={Array.isArray(value) ? value.join(", ") : serializedValue}
            onChange={(e) => onChange(parseInputArrayString(e.target.value))}
            placeholder="Comma-separated values"
            className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors"
          />
          {onDropReference && (
            <div className="text-[11px] text-slate-500">
              Drag output paths here to add references.
            </div>
          )}
        </div>
      );
    }

    if (schemaType === "object" || schema.properties) {
      return (
        <div className="space-y-1">
          <textarea
            value={serializedValue}
            onChange={(e) => onChange(safeParseJson(e.target.value))}
            rows={4}
            placeholder="Enter JSON object or drop a reference path"
            className="w-full rounded-lg bg-background border border-border p-2.5 text-xs text-foreground focus:outline-none focus:border-indigo-500 transition-colors font-mono resize-y"
          />
          {onDropReference && (
            <div className="text-[11px] text-slate-500">
              Drop an output path to populate the field.
            </div>
          )}
        </div>
      );
    }

    if (isTextarea) {
      return (
        <textarea
          value={serializedValue}
          onChange={(e) => onChange(e.target.value)}
          rows={4}
          placeholder={`Enter ${title.toLowerCase()}...`}
          className="w-full rounded-lg bg-background border border-border p-2.5 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors font-sans leading-normal resize-y"
        />
      );
    }

    return (
      <input
        type="text"
        value={serializedValue}
        onChange={(e) => onChange(e.target.value)}
        placeholder={`Enter ${title.toLowerCase()}...`}
        className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors"
      />
    );
  };

  return (
    <div onDrop={handleDrop} onDragOver={handleDragOver} className="space-y-1">
      <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide flex justify-between items-center">
        <span>{title}</span>
        {description && (
          <span className="text-[10px] text-slate-500 font-normal normal-case italic">
            {description}
          </span>
        )}
      </label>
      {renderField()}
    </div>
  );
};

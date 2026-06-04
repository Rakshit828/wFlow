import React from "react";
import { JsonSchemaParser } from "../../../lib/jsonSchemaParser";
import { safeParseJson, serializeInputValue } from "./utils";

interface SchemaFieldRendererProps {
  fieldKey: string;
  schema: Record<string, any>;
  value: unknown;
  onChange: (value: unknown) => void;
  onDropReference?: (path: string) => void;
  rootSchema?: Record<string, any>;
  required?: boolean;
  depth?: number;
  disabled?: boolean;
}

const DEFAULT_FIELD_STYLES =
  "w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors";

const titleForField = (schema: Record<string, any>, fieldKey: string) => {
  if (schema.title) return schema.title;
  return fieldKey;
};

const isObjectValue = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

const isArrayValue = (value: unknown): value is unknown[] =>
  Array.isArray(value);

const getRepresentativeText = (value: unknown) => {
  if (value == null) return "";
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
};

const buildDefaultValue = (
  schema: Record<string, any>,
  parser: JsonSchemaParser,
): unknown => {
  const parsed = parser.parseField(schema);
  switch (parsed.type) {
    case "object":
      return {};
    case "array":
      return [];
    case "boolean":
      return false;
    case "integer":
    case "number":
      return 0;
    case "enum":
      return Array.isArray(parsed.enumValues) && parsed.enumValues.length > 0
        ? parsed.enumValues[0]
        : "";
    case "const":
      return parsed.constValue ?? "";
    default:
      return "";
  }
};

const findSelectedOption = (
  value: unknown,
  options: Record<string, any>[],
): number => {
  if (value == null) return 0;
  return (
    options.findIndex((option) => {
      if (typeof option.const !== "undefined") {
        return value === option.const;
      }
      if (Array.isArray(option.enum) && option.enum.includes(value)) {
        return true;
      }
      if (typeof value === "boolean" && option.type === "boolean") return true;
      if (
        (typeof value === "number" || typeof value === "string") &&
        option.type === typeof value
      )
        return true;
      if (
        isObjectValue(value) &&
        (option.type === "object" || option.properties)
      )
        return true;
      if (Array.isArray(value) && option.type === "array") return true;
      return false;
    }) ?? 0
  );
};

const getOptionLabel = (option: Record<string, any>, index: number) => {
  if (option.title) return option.title;
  if (option.description) return `${option.type || "option"} ${index + 1}`;
  return option.type ? String(option.type) : `Option ${index + 1}`;
};

export const SchemaFieldRenderer: React.FC<SchemaFieldRendererProps> = ({
  fieldKey,
  schema,
  value,
  onChange,
  onDropReference,
  rootSchema,
  required = false,
  depth = 0,
  disabled = false,
}) => {
  const parser = React.useMemo(
    () => new JsonSchemaParser(rootSchema ?? schema ?? {}),
    [rootSchema, schema],
  );

  const parsed = React.useMemo(
    () => parser.parseField(schema ?? {}),
    [parser, schema],
  );

  const isAutofilled = Boolean(
    schema["x-autofilled"] === true ||
      schema["x-autofillled"] === true ||
      (parsed as any)["x-autofilled"] === true ||
      (parsed as any)["x-autofillled"] === true,
  );

  // Early return if autofilled - completely avoid in frontend
  if (isAutofilled) {
    return null;
  }

  const title = titleForField(schema, fieldKey);
  const description = schema.description as string | undefined;
  const isTechnical = Boolean(
    schema["x-technical"] === true || (parsed as any)["x-technical"] === true,
  );
  const isReadOnly = Boolean(
    disabled ||
      schema.readOnly === true ||
      (parsed as any).readOnly === true
  );
  const isDeprecated = Boolean(
    schema.deprecated === true ||
      (parsed as any).deprecated === true
  );

  const displayDescription = description || schema["x-comment"];

  // Default value and reset logic
  const defaultValue = schema.default !== undefined ? schema.default : parsed.default;
  const hasDefault = defaultValue !== undefined;
  const isDifferentFromDefault = hasDefault && value !== undefined && value !== defaultValue;

  // Examples logic
  const examples = Array.isArray(schema.examples)
    ? schema.examples
    : Array.isArray(parsed.examples)
      ? parsed.examples
      : null;

  // Range constraints
  const minVal = schema.minimum !== undefined ? schema.minimum : parsed.minimum;
  const maxVal = schema.maximum !== undefined ? schema.maximum : parsed.maximum;
  const hasRange = minVal !== undefined || maxVal !== undefined;

  // Pattern regex validation
  const patternStr = schema.pattern || parsed.pattern;
  const patternRegex = React.useMemo(() => {
    if (patternStr) {
      try {
        return new RegExp(patternStr);
      } catch {
        return null;
      }
    }
    return null;
  }, [patternStr]);

  const isPatternInvalid = React.useMemo(() => {
    if (patternRegex && typeof value === "string" && value !== "") {
      return !patternRegex.test(value);
    }
    return false;
  }, [patternRegex, value]);

  // Style helper
  const getFieldStyles = (extra = "") => {
    let styles = `${DEFAULT_FIELD_STYLES} ${extra}`;
    if (isPatternInvalid) {
      styles += " border-rose-500/50 focus:border-rose-500 bg-rose-500/5";
    }
    if (isReadOnly) {
      styles += " bg-slate-900 cursor-not-allowed opacity-60";
    }
    return styles.trim();
  };

  const [selectedVariant, setSelectedVariant] = React.useState(0);

  React.useEffect(() => {
    if (schema.anyOf || schema.oneOf) {
      const options = (schema.anyOf ?? schema.oneOf) as Record<string, any>[];
      const index = findSelectedOption(value, options);
      setSelectedVariant(index >= 0 ? index : 0);
    }
  }, [schema.anyOf, schema.oneOf, value]);

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    if (!onDropReference || isReadOnly) return;
    event.preventDefault();
    const path = event.dataTransfer.getData("application/x-output-path");
    if (!path) return;

    if (parsed.type === "array") {
      const nextArray = isArrayValue(value) ? [...value] : [];
      nextArray.push(path);
      onChange(nextArray);
      return;
    }

    onChange(path);
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    if (!onDropReference || isReadOnly) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
  };

  const getInputType = () => {
    const fmt = schema.format || parsed.format;
    switch (fmt) {
      case "date-time":
        return "datetime-local";
      case "date":
        return "date";
      case "time":
        return "time";
      case "email":
        return "email";
      case "uri":
      case "url":
        return "url";
      case "password":
        return "password";
      default:
        return "text";
    }
  };

  const renderPrimitive = (): React.ReactNode => {
    if (parsed.type === "const") {
      return (
        <input
          type="text"
          value={String(parsed.constValue ?? "")}
          readOnly
          className={getFieldStyles("bg-slate-900 cursor-not-allowed")}
        />
      );
    }

    if (parsed.type === "enum" && Array.isArray(parsed.enumValues)) {
      return (
        <select
          value={value == null ? "" : String(value)}
          onChange={(e) => onChange(e.target.value)}
          disabled={isReadOnly}
          className={getFieldStyles()}
        >
          <option value="">Select option...</option>
          {parsed.enumValues.map((option) => (
            <option key={String(option)} value={String(option)}>
              {String(option)}
            </option>
          ))}
        </select>
      );
    }

    if (parsed.type === "boolean") {
      return (
        <select
          value={value === true ? "true" : value === false ? "false" : ""}
          onChange={(e) => onChange(e.target.value === "true")}
          disabled={isReadOnly}
          className={getFieldStyles()}
        >
          <option value="">Select value...</option>
          <option value="true">True</option>
          <option value="false">False</option>
        </select>
      );
    }

    if (parsed.type === "integer" || parsed.type === "number") {
      return (
        <input
          type="number"
          value={value == null ? "" : String(value)}
          min={minVal}
          max={maxVal}
          disabled={isReadOnly}
          onChange={(e) => {
            const nextValue = e.target.value;
            onChange(
              nextValue === ""
                ? undefined
                : parsed.type === "integer"
                  ? parseInt(nextValue, 10)
                  : parseFloat(nextValue),
            );
          }}
          className={getFieldStyles()}
        />
      );
    }

    const schemaType = schema.type;
    if (
      Array.isArray(schemaType) &&
      schemaType.includes("string") &&
      schemaType.includes("null")
    ) {
      return (
        <input
          type="text"
          value={value == null ? "" : String(value)}
          disabled={isReadOnly}
          onChange={(e) =>
            onChange(e.target.value === "" ? null : e.target.value)
          }
          className={getFieldStyles()}
        />
      );
    }

    if (parsed.type === "array") {
      return renderArray();
    }

    if (parsed.type === "object") {
      return renderObject();
    }

    if (parsed.type === "anyOf" || parsed.type === "oneOf") {
      return renderUnion();
    }

    if (parsed.type === "allOf") {
      return renderAllOf();
    }

    const isTextarea =
      typeof schema.maxLength === "number" && schema.maxLength > 120;

    const fmt = schema.format || parsed.format;

    if (fmt === "color") {
      return (
        <div className="flex items-center gap-2 w-full">
          <input
            type="color"
            value={value == null ? "#000000" : String(value)}
            disabled={isReadOnly}
            onChange={(e) => onChange(e.target.value)}
            className="w-10 h-8 rounded border border-slate-700 bg-transparent p-0.5 cursor-pointer disabled:cursor-not-allowed disabled:opacity-60"
          />
          <input
            type="text"
            value={value == null ? "" : String(value)}
            disabled={isReadOnly}
            onChange={(e) => onChange(e.target.value)}
            className={getFieldStyles("font-mono")}
            placeholder="#000000"
          />
        </div>
      );
    }

    if (
      isTextarea ||
      fmt === "textarea" ||
      parsed.type === "unknown"
    ) {
      return (
        <textarea
          value={getRepresentativeText(value)}
          disabled={isReadOnly}
          onChange={(e) => onChange(safeParseJson(e.target.value))}
          rows={4}
          className={getFieldStyles("font-mono resize-y")}
          placeholder="Enter JSON here or paste a value"
        />
      );
    }

    return (
      <input
        type={getInputType()}
        value={value == null ? "" : String(value)}
        disabled={isReadOnly}
        minLength={schema.minLength}
        maxLength={schema.maxLength}
        onChange={(e) => onChange(e.target.value)}
        className={getFieldStyles()}
        placeholder={defaultValue !== undefined ? `Default: ${defaultValue}` : `Enter ${title.toLowerCase()}...`}
      />
    );
  };

  const renderObject = (): React.ReactNode => {
    const properties = parsed.properties ?? {};
    const nestedValue = isObjectValue(value) ? value : {};

    if (Object.keys(properties).length === 0) {
      return (
        <textarea
          value={getRepresentativeText(value)}
          disabled={isReadOnly}
          onChange={(e) => onChange(safeParseJson(e.target.value))}
          rows={4}
          className={getFieldStyles("font-mono resize-y")}
          placeholder="Enter object JSON..."
        />
      );
    }

    return (
      <div className="space-y-4 rounded-2xl border border-slate-700 bg-slate-950/80 p-4">
        {Object.entries(properties).map(([propKey, propSchema]) => {
          let parsedSub: any = undefined;
          try {
            parsedSub = parser.parseField(propSchema as any);
          } catch {
            parsedSub = undefined;
          }
          if (
            (propSchema as any)["x-autofilled"] === true ||
            (propSchema as any)["x-autofillled"] === true ||
            (parsedSub && (parsedSub["x-autofilled"] === true || parsedSub["x-autofillled"] === true))
          )
            return null;
          return (
            <SchemaFieldRenderer
              key={propKey}
              fieldKey={propKey}
              schema={propSchema as Record<string, any>}
              value={(nestedValue as Record<string, unknown>)[propKey]}
              onChange={(next) =>
                onChange({
                  ...nestedValue,
                  [propKey]: next,
                })
              }
              onDropReference={onDropReference}
              rootSchema={rootSchema}
              required={
                Array.isArray(schema.required) &&
                schema.required.includes(propKey)
              }
              depth={depth + 1}
              disabled={isReadOnly}
            />
          );
        })}
      </div>
    );
  };

  const renderArray = (): React.ReactNode => {
    const listValue = isArrayValue(value) ? value : [];
    const itemsSchema = parsed.items || schema.items || {};
    const singleItemSchema = Array.isArray(itemsSchema)
      ? itemsSchema[0]
      : itemsSchema;

    const updateItem = (index: number, next: unknown) => {
      const nextArray = [...listValue];
      nextArray[index] = next;
      onChange(nextArray);
    };

    const removeItem = (index: number) => {
      const nextArray = [...listValue];
      nextArray.splice(index, 1);
      onChange(nextArray);
    };

    return (
      <div className="space-y-3">
        {listValue.map((item, index) => (
          <div
            key={index}
            className="rounded-2xl border border-slate-700 bg-slate-900/70 p-3"
          >
            <div className="flex items-center justify-between gap-3 mb-3">
              <div className="text-sm font-semibold text-foreground">
                Item {index + 1}
              </div>
              <button
                type="button"
                onClick={() => removeItem(index)}
                disabled={isReadOnly}
                className="rounded-xl px-2 py-1 text-xs font-semibold text-rose-300 hover:text-rose-100 hover:bg-rose-500/10 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-transparent"
              >
                Remove
              </button>
            </div>
            <SchemaFieldRenderer
              fieldKey={`${fieldKey}[${index}]`}
              schema={singleItemSchema as Record<string, any>}
              value={item}
              onChange={(next) => updateItem(index, next)}
              onDropReference={onDropReference}
              rootSchema={rootSchema}
              depth={depth + 1}
              disabled={isReadOnly}
            />
          </div>
        ))}
        <button
          type="button"
          onClick={() =>
            onChange([
              ...listValue,
              buildDefaultValue(
                singleItemSchema as Record<string, any>,
                parser,
              ),
            ])
          }
          disabled={isReadOnly}
          className="rounded-2xl border border-slate-700 bg-slate-900/80 px-3 py-2 text-sm font-semibold text-slate-200 hover:bg-slate-900 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          Add item
        </button>
      </div>
    );
  };

  const renderUnion = (): React.ReactNode => {
    const options = (schema.anyOf ?? schema.oneOf) as Record<string, any>[];
    if (!Array.isArray(options) || options.length === 0) {
      return renderPrimitive();
    }

    const currentOption = options[selectedVariant] as Record<string, any>;

    return (
      <div className="space-y-3">
        <div className="grid gap-2 sm:grid-cols-[1fr_auto] items-center">
          <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Variant
          </label>
          <select
            value={selectedVariant}
            onChange={(e) => setSelectedVariant(Number(e.target.value))}
            disabled={isReadOnly}
            className={getFieldStyles()}
          >
            {options.map((option, idx) => (
              <option key={idx} value={idx}>
                {getOptionLabel(option, idx)}
              </option>
            ))}
          </select>
        </div>
        <SchemaFieldRenderer
          fieldKey={fieldKey}
          schema={currentOption}
          value={value}
          onChange={onChange}
          onDropReference={onDropReference}
          rootSchema={rootSchema}
          depth={depth + 1}
          disabled={isReadOnly}
        />
      </div>
    );
  };

  const renderAllOf = (): React.ReactNode => {
    const options = schema.allOf as Record<string, any>[];
    if (!Array.isArray(options) || options.length === 0) {
      return renderPrimitive();
    }

    return (
      <div className="space-y-4">
        {options.map((option, index) => (
          <div
            key={index}
            className="rounded-2xl border border-slate-700 bg-slate-900/70 p-3"
          >
            <SchemaFieldRenderer
              fieldKey={`${fieldKey} (part ${index + 1})`}
              schema={option}
              value={value}
              onChange={onChange}
              onDropReference={onDropReference}
              rootSchema={rootSchema}
              depth={depth + 1}
              disabled={isReadOnly}
            />
          </div>
        ))}
      </div>
    );
  };

  const renderField = (): React.ReactNode => {
    if (parsed.type === "object") return renderObject();
    if (parsed.type === "array") return renderArray();
    if (parsed.type === "anyOf" || parsed.type === "oneOf")
      return renderUnion();
    if (parsed.type === "allOf") return renderAllOf();
    return renderPrimitive();
  };

  return (
    <div
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      className={depth > 0 ? "space-y-2" : "space-y-3"}
    >
      <div className="flex items-center justify-between gap-3">
        <div className="flex flex-col w-full">
          <div className="flex items-center flex-wrap gap-1">
            <label className={`text-sm font-semibold text-foreground ${isDeprecated ? "line-through text-slate-500 decoration-amber-500/30" : ""}`}>
              {title}
            </label>
            {required ? (
              <span className="rounded bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-400 border border-amber-500/20">
                Required
              </span>
            ) : null}
            {isTechnical ? (
              <span className="rounded bg-indigo-500/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-indigo-400 border border-indigo-500/20">
                Technical
              </span>
            ) : null}
            {isDeprecated ? (
              <span className="rounded bg-rose-500/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-rose-400 border border-rose-500/20 animate-pulse">
                Deprecated
              </span>
            ) : null}
            {isReadOnly ? (
              <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-400 border border-slate-700">
                Read-only
              </span>
            ) : null}
            {hasRange && (
              <span className="text-[10px] text-slate-500 font-mono">
                ({minVal !== undefined ? `min: ${minVal}` : ""}
                {minVal !== undefined && maxVal !== undefined ? ", " : ""}
                {maxVal !== undefined ? `max: ${maxVal}` : ""})
              </span>
            )}
            {isDifferentFromDefault && (
              <button
                type="button"
                onClick={() => onChange(defaultValue)}
                className="text-[10px] text-indigo-400 hover:text-indigo-300 font-semibold hover:underline transition-all cursor-pointer border border-indigo-500/20 bg-indigo-500/5 hover:bg-indigo-500/10 px-1.5 py-0.2 rounded ml-1"
                title={`Reset to default: ${serializeInputValue(defaultValue)}`}
              >
                Reset
              </button>
            )}
          </div>
          {displayDescription ? (
            <p className="text-xs text-slate-400 mt-1">{displayDescription}</p>
          ) : null}
          {examples && examples.length > 0 && !isReadOnly && (
            <div className="flex flex-wrap items-center gap-1.5 mt-1.5 text-xs text-slate-400">
              <span className="text-[10px] text-slate-500">Pills:</span>
              {examples.map((ex: any, idx: number) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => onChange(ex)}
                  className="px-1.5 py-0.5 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 text-[10px] cursor-pointer hover:border-slate-500 transition-all"
                >
                  {typeof ex === "object" ? JSON.stringify(ex) : String(ex)}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
      {renderField()}
      {schema.maxLength && typeof value === "string" && (
        <div className="text-[10px] text-right text-slate-500 mt-0.5 pr-1">
          {value.length} / {schema.maxLength} characters
        </div>
      )}
      {isPatternInvalid && (
        <p className="text-[11px] text-rose-400 mt-1 font-mono pl-1">
          Must match regex pattern: {patternStr}
        </p>
      )}
    </div>
  );
};

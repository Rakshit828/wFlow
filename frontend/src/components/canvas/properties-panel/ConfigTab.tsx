import React from "react";
import { useWorkflowStore } from "../../../store/useWorkflowStore";
import { OutputSchemaTree } from "./OutputSchemaTree";
import { SchemaFieldRenderer } from "./SchemaFieldRenderer";
import {
  buildResponseModelSchema,
  parseFieldsFromConfig,
  resolveSchemaDeep,
} from "./utils";
import { JsonSchemaParser } from "../../../lib/jsonSchemaParser";
import type { WFlowNodeData } from "../../../types/flow";

const RESPONSE_FIELD_TYPES = [
  { value: "string", label: "String" },
  { value: "number", label: "Number" },
  { value: "integer", label: "Integer" },
  { value: "boolean", label: "Boolean" },
  { value: "array", label: "Array" },
  { value: "object", label: "Object" },
];

interface ConfigTabProps {
  nodeData: WFlowNodeData;
  nodeId: string;
}

const resolveSchemaRef = (
  schema: Record<string, any> | null,
  rootSchema: Record<string, any> | null = null,
): Record<string, any> | null => {
  if (!schema || typeof schema !== "object") return null;

  const ref = schema.$ref;
  if (typeof ref !== "string" || !ref.startsWith("#/")) {
    return schema;
  }

  if (!rootSchema || typeof rootSchema !== "object") return schema;

  const path = ref.slice(2).split("/");
  let current: any = rootSchema;

  for (const step of path) {
    if (current && typeof current === "object" && step in current) {
      current = current[step];
    } else {
      return schema;
    }
  }

  return typeof current === "object" && current !== null
    ? { ...current, ...schema, $ref: undefined }
    : schema;
};

const normalizeConfigSchema = (
  schema: Record<string, any> | null,
  rootSchema: Record<string, any> | null = null,
) => {
  if (!schema) return null;
  const resolved = resolveSchemaRef(schema, rootSchema);
  const normalized = { ...resolved };

  if (!normalized.type) {
    normalized.type = normalized.properties ? "object" : "string";
  }

  if (!normalized.$defs && rootSchema?.$defs) {
    normalized.$defs = rootSchema.$defs;
  }
  if (!normalized.definitions && rootSchema?.definitions) {
    normalized.definitions = rootSchema.definitions;
  }

  return normalized;
};

export const ConfigTab: React.FC<ConfigTabProps> = ({ nodeData, nodeId }) => {
  const { updateNodeConfig } = useWorkflowStore();
  const [responseFields, setResponseFields] = React.useState<
    {
      name: string;
      type: string;
    }[]
  >([]);

  const nodeIdRef = React.useRef(nodeId);

  const [techOpen, setTechOpen] = React.useState(false);

  React.useEffect(() => {
    if (nodeId !== nodeIdRef.current) {
      nodeIdRef.current = nodeId;
      setResponseFields(parseFieldsFromConfig(nodeData.config));
      return;
    }

    if (responseFields.length === 0) {
      const parsedFields = parseFieldsFromConfig(nodeData.config);
      if (parsedFields.length > 0) {
        setResponseFields(parsedFields);
      }
    }
  }, [nodeId, nodeData.config, responseFields.length]);

  const configSchema = React.useMemo(() => {
    const normalized = normalizeConfigSchema(
      nodeData.input_model?.config ??
        nodeData.input_model?.properties?.config ??
        null,
      nodeData.input_model ?? null,
    );
    return resolveSchemaDeep(normalized, nodeData.input_model ?? null);
  }, [nodeData.input_model]);

  const handleConfigChange = (fieldKey: string, value: unknown) => {
    updateNodeConfig(nodeId, { [fieldKey]: value });
  };

  const configFields: {
    visible: Array<{
      fieldKey: string;
      schema: Record<string, any>;
      required: boolean;
    }>;
    technical: Array<{
      fieldKey: string;
      schema: Record<string, any>;
      required: boolean;
    }>;
  } = React.useMemo(() => {
    const visible: any[] = [];
    const technical: any[] = [];
    if (!configSchema?.properties) return { visible, technical };
    const required = Array.isArray(configSchema.required)
      ? configSchema.required
      : [];

    const parser = new JsonSchemaParser(
      nodeData.input_model ?? configSchema ?? {},
    );

    Object.entries(configSchema.properties).forEach(
      ([fieldKey, fieldSchema]) => {
        const schemaObj = fieldSchema as Record<string, any>;
        const resolved = resolveSchemaDeep(
          schemaObj,
          nodeData.input_model ?? configSchema ?? {},
        );
        const parsed = parser.parseField(schemaObj as any) as Record<
          string,
          any
        >;

        const isAutofilled = Boolean(
          schemaObj["x-autofilled"] === true ||
          schemaObj["x-autofillled"] === true ||
          parsed["x-autofilled"] === true ||
          parsed["x-autofillled"] === true ||
          (resolved && (resolved["x-autofilled"] === true || resolved["x-autofillled"] === true))
        );
        if (isAutofilled) return; // remove whole branch if this property itself is autofilled

        const isTechnical = Boolean(
          parsed["x-technical"] === true || schemaObj["x-technical"] === true,
        );

        const entry = {
          fieldKey,
          schema: schemaObj,
          required: required.includes(fieldKey),
        };

        if (isTechnical) technical.push(entry);
        else visible.push(entry);
      },
    );

    return { visible, technical };
  }, [configSchema, nodeData.input_model]);

  const getFieldTypeLabel = (schema: Record<string, any>) => {
    if (!schema) return "any";
    if (typeof schema.type === "string") return schema.type;
    if (Array.isArray(schema.type)) return schema.type.join(" | ");
    if (schema.enum) return `enum[${schema.enum.join(", ")}]`;
    if (schema.properties) return "object";
    if (schema.items) return "array";
    return "any";
  };

  const syncResponseFields = (fields: { name: string; type: string }[]) => {
    setResponseFields(fields);
    updateNodeConfig(nodeId, {
      response_model: buildResponseModelSchema(fields),
    });
  };

  const addField = () => {
    syncResponseFields([...responseFields, { name: "", type: "string" }]);
  };

  const updateField = (
    index: number,
    field: { name: string; type: string },
  ) => {
    const next = [...responseFields];
    next[index] = field;
    syncResponseFields(next);
  };

  const removeField = (index: number) => {
    const next = responseFields.filter((_, i) => i !== index);
    syncResponseFields(next);
  };

  const hasResponseBuilder =
    nodeData.key.startsWith("llm.") || !!nodeData.config?.response_model;

  return (
    <div className="space-y-6">
      {hasResponseBuilder ? (
        <div className="space-y-4 rounded-2xl border border-border bg-card/50 p-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="space-y-1">
              <div className="text-sm font-semibold text-foreground">
                Output schema
              </div>
              <p className="text-xs text-muted-foreground max-w-prose">
                Define the output fields this LLM node will expose to later
                nodes. Add each field name and choose its data type from the
                dropdown.
              </p>
            </div>
            <button
              type="button"
              onClick={addField}
              className="inline-flex items-center gap-2 rounded-2xl border border-primary bg-primary/10 px-4 py-2 text-sm font-semibold text-primary hover:bg-primary hover:text-primary-foreground transition-all cursor-pointer"
            >
              Add
            </button>
          </div>

          {responseFields.length === 0 ? (
            <div className="rounded-2xl border border-border bg-muted/40 p-4 text-sm text-muted-foreground">
              No output fields configured yet. Add fields to shape the node
              response.
            </div>
          ) : (
            <div className="rounded-2xl border border-border bg-muted/20 overflow-hidden">
              <div className="grid gap-0 lg:grid-cols-[1.7fr_1fr_auto] bg-muted/50 px-4 py-2 text-[11px] uppercase tracking-wide text-muted-foreground border-b border-border">
                <div>Field name</div>
                <div>Data type</div>
                <div className="text-right">Remove</div>
              </div>

              <div className="divide-y divide-border">
                {responseFields.map((field, index) => (
                  <div
                    key={`output-field-${index}`}
                    className="grid gap-3 lg:grid-cols-[1.7fr_1fr_auto] items-center px-4 py-3"
                  >
                    <input
                      type="text"
                      value={field.name}
                      onChange={(e) =>
                        updateField(index, { ...field, name: e.target.value })
                      }
                      placeholder="e.g. summary"
                      className="w-full bg-background border border-border rounded px-2 py-1.5 text-sm text-foreground outline-none focus:border-primary focus:bg-background transition-all"
                    />
                    <select
                      value={field.type}
                      onChange={(e) =>
                        updateField(index, { ...field, type: e.target.value })
                      }
                      className="w-full bg-background border border-border rounded px-2 py-1.5 text-sm text-foreground outline-none focus:border-primary focus:bg-background transition-all"
                    >
                      {RESPONSE_FIELD_TYPES.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      onClick={() => removeField(index)}
                      className="h-8 px-2 text-sm text-rose-400 hover:text-rose-600 hover:bg-rose-500/10 rounded transition-all cursor-pointer"
                      title="Remove field"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : null}

      {!hasResponseBuilder && nodeData.output_model ? (
        <div className="space-y-4">
          <div className="rounded-2xl border border-border bg-card/50 p-4 space-y-3">
            <div className="text-sm font-semibold text-foreground">
              Node output schema
            </div>
            <div className="text-xs text-muted-foreground">
              The output format of this node.
            </div>
            <OutputSchemaTree
              schema={nodeData.output_model}
              basePath={`${nodeData.name}.outputs`}
            />
          </div>
        </div>
      ) : null}

      <div className="space-y-4">
        <div>
          <div className="text-sm font-semibold text-foreground">
            Config schema
          </div>
          <p className="text-xs text-muted-foreground">
            Parameters and configuration options for this node.
          </p>
        </div>
        {!configFields ||
        (configFields.visible.length === 0 &&
          configFields.technical.length === 0) ? (
          <div className="rounded border border-border bg-muted/40 p-4 text-sm text-muted-foreground">
            This node has no config schema defined.
          </div>
        ) : (
          <div className="rounded border border-border bg-muted/20 overflow-hidden">
            <div className="grid gap-0 lg:grid-cols-[1.5fr_1fr_auto] bg-muted/50 px-4 py-2 text-[11px] uppercase tracking-wide text-muted-foreground border-b border-border">
              <div>Parameter</div>
              <div>Type</div>
              <div className="text-right">Required</div>
            </div>
            <div className="divide-y divide-border">
              {configFields.visible.map((field) => (
                <div
                  key={field.fieldKey}
                  className="grid gap-3 lg:grid-cols-[1.5fr_1fr_auto] items-center px-4 py-3"
                >
                  <div>
                    <div className="text-sm font-semibold text-foreground">
                      {field.fieldKey}
                    </div>
                    {field.schema.description ? (
                      <div className="text-[11px] text-muted-foreground mt-1">
                        {field.schema.description}
                      </div>
                    ) : null}
                  </div>
                  <div className="text-sm text-foreground/80">
                    {getFieldTypeLabel(field.schema)}
                  </div>
                  <div className="text-right">
                    {field.required ? (
                      <span className="text-[11px] font-semibold text-amber-500">
                        Yes
                      </span>
                    ) : (
                      <span className="text-[11px] text-muted-foreground">No</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="rounded-2xl border border-border bg-card/50 p-4 space-y-4">
        <div>
          <div className="text-sm font-semibold text-foreground">
            Config values
          </div>
          <p className="text-xs text-muted-foreground">
            Edit the actual values for each config field here.
          </p>
        </div>
        {(!configFields || configFields.visible.length === 0) &&
        configFields.technical.length === 0 ? (
          <div className="rounded-2xl border border-border bg-muted/40 p-4 text-sm text-muted-foreground">
            No editable config values available for this node.
          </div>
        ) : (
          <div className="space-y-4">
            {configFields.visible.map((field) => (
              <SchemaFieldRenderer
                key={field.fieldKey}
                fieldKey={field.fieldKey}
                schema={field.schema}
                value={nodeData.config[field.fieldKey]}
                onChange={(value) => handleConfigChange(field.fieldKey, value)}
                rootSchema={nodeData.input_model ?? undefined}
              />
            ))}
          </div>
        )}
      </div>

      {/* Technical fields block (advanced users) */}
      {configFields.technical && configFields.technical.length > 0 ? (
        <div className="rounded-xl border border-border bg-card/50 p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-semibold text-foreground">
                Technical configuration
              </div>
              <p className="text-xs text-muted-foreground">
                Advanced options for technical users. These values are optional
                and may be autofilled by the system.
              </p>
            </div>
            <div className="text-sm">
              <button
                type="button"
                onClick={() => setTechOpen((s) => !s)}
                className="cursor-pointer px-2 py-1 rounded text-muted-foreground hover:text-foreground bg-transparent border border-transparent hover:border-border transition-all"
              >
                {techOpen ? "Hide" : "Show"}
              </button>
            </div>
          </div>

          {techOpen && (
            <div className="mt-3 space-y-3 px-4">
              {configFields.technical.map((field: any) => (
                <SchemaFieldRenderer
                  key={field.fieldKey}
                  fieldKey={field.fieldKey}
                  schema={field.schema}
                  value={nodeData.config[field.fieldKey]}
                  onChange={(value) =>
                    handleConfigChange(field.fieldKey, value)
                  }
                  rootSchema={nodeData.input_model ?? undefined}
                />
              ))}
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
};

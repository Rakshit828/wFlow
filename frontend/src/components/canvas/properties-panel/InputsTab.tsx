import React from "react";
import { useWorkflowStore } from "../../../store/useWorkflowStore";
import { OutputReferencePanel } from "./OutputReferencePanel";

import { SchemaFieldRenderer } from "./SchemaFieldRenderer";
import { resolveSchemaDeep } from "./utils";
import type { WFlowNodeData } from "../../../types/flow";
import type { Node as WorkflowNode } from "../../../types/workflow";

interface InputsTabProps {
  nodeData: WFlowNodeData;
  nodeId: string;
}

const removeConfigProperty = (schema: Record<string, any> | null) => {
  if (!schema) return null;
  const normalized = { ...schema };
  if (normalized.properties && normalized.properties.config) {
    normalized.properties = { ...normalized.properties };
    delete normalized.properties.config;
  }
  return normalized;
};

export const InputsTab: React.FC<InputsTabProps> = ({ nodeData, nodeId }) => {
  const { updateNodeInputs, getPrecedingNodes } = useWorkflowStore();
  const precedingNodes = getPrecedingNodes(nodeId) as WorkflowNode[];

  const inputSchema = React.useMemo(() => {
    const raw = removeConfigProperty(nodeData.input_model ?? null);
    return resolveSchemaDeep(raw, nodeData.input_model ?? null);
  }, [nodeData.input_model]);

  const inputFields = React.useMemo(() => {
    if (!inputSchema?.properties) return [];
    const required = Array.isArray(inputSchema.required)
      ? inputSchema.required
      : [];

    return Object.entries(inputSchema.properties).map(
      ([fieldKey, fieldSchema]) => ({
        fieldKey,
        schema: fieldSchema as Record<string, any>,
        required: required.includes(fieldKey),
      }),
    );
  }, [inputSchema]);

  const handleInputChange = (fieldKey: string, value: unknown) => {
    updateNodeInputs(nodeId, { [fieldKey]: value });
  };

  const getFieldTypeLabel = (schema: Record<string, any>) => {
    if (!schema) return "any";
    if (typeof schema.type === "string") return schema.type;
    if (Array.isArray(schema.type)) return schema.type.join(" | ");
    if (schema.enum) return `enum[${schema.enum.join(", ")}]`;
    if (schema.properties) return "object";
    if (schema.items) return "array";
    return "any";
  };

  return (
    <div className="space-y-6">
      <div className="rounded-3xl border border-slate-700 bg-slate-950/80 p-4 space-y-4">
        <div className="flex items-center justify-between gap-2">
          <div>
            <div className="text-sm font-semibold text-foreground">
              Input schema
            </div>
            <p className="text-xs text-slate-400">
              Fields declared by the backend schema and their expected types.
            </p>
          </div>
          <span className="text-xs text-slate-500">
            {inputFields.length} field{inputFields.length === 1 ? "" : "s"}
          </span>
        </div>

        {inputFields.length === 0 ? (
          <div className="rounded border border-slate-700 bg-slate-900/80 p-4 text-sm text-slate-400">
            This node has no input schema defined.
          </div>
        ) : (
          <div className="rounded border border-slate-700 bg-slate-950/80 overflow-hidden">
            <div className="grid gap-0 lg:grid-cols-[1.5fr_1fr_auto] bg-slate-900/50 px-4 py-2 text-[11px] uppercase tracking-wide text-slate-500 border-b border-slate-700">
              <div>Field name</div>
              <div>Type</div>
              <div className="text-right">Required</div>
            </div>
            <div className="divide-y divide-slate-700">
              {inputFields.map((field) => (
                <div
                  key={field.fieldKey}
                  className="grid gap-3 lg:grid-cols-[1.5fr_1fr_auto] items-center px-4 py-3"
                >
                  <div>
                    <div className="text-sm font-semibold text-foreground">
                      {field.fieldKey}
                    </div>
                    {field.schema.description ? (
                      <div className="text-[11px] text-slate-500 mt-1">
                        {field.schema.description}
                      </div>
                    ) : null}
                  </div>
                  <div className="text-sm text-slate-300">
                    {getFieldTypeLabel(field.schema)}
                  </div>
                  <div className="text-right">
                    {field.required ? (
                      <span className="text-[11px] font-semibold text-amber-300">
                        Yes
                      </span>
                    ) : (
                      <span className="text-[11px] text-slate-500">No</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="rounded-3xl border border-slate-700 bg-slate-950/80 p-4 space-y-4">
        <div>
          <div className="text-sm font-semibold text-foreground">
            Input values
          </div>
          <p className="text-xs text-slate-400">
            Edit the actual values for each input field here.
          </p>
        </div>

        {inputFields.length === 0 ? (
          <div className="rounded-2xl border border-slate-700 bg-slate-900/80 p-4 text-sm text-slate-400">
            No editable inputs available for this node.
          </div>
        ) : (
          <div className="space-y-4">
            {inputFields.map((field) => (
              <SchemaFieldRenderer
                key={field.fieldKey}
                fieldKey={field.fieldKey}
                schema={field.schema}
                value={nodeData.inputs[field.fieldKey]}
                onChange={(value) => handleInputChange(field.fieldKey, value)}
                onDropReference={(path) =>
                  handleInputChange(field.fieldKey, path)
                }
              />
            ))}
          </div>
        )}
      </div>

      <OutputReferencePanel precedingNodes={precedingNodes} />
    </div>
  );
};

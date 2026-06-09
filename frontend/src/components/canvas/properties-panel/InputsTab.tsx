import React from "react";
import { useWorkflowStore } from "../../../store/useWorkflowStore";
import { OutputReferencePanel } from "./OutputReferencePanel";
import { ConditionBuilder } from "./ConditionBuilder";

import { SchemaFieldRenderer } from "./SchemaFieldRenderer";
import { resolveSchemaDeep } from "./utils";
import { JsonSchemaParser } from "../../../lib/jsonSchemaParser";
import type { WFlowNodeData } from "../../../types/flow";
import type { NodeFullResponse as WorkflowNode } from "../../../types/workflow";

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
  const [techOpen, setTechOpen] = React.useState(false);

  const inputSchema = React.useMemo(() => {
    const raw = removeConfigProperty(nodeData.input_model ?? null);
    return resolveSchemaDeep(raw, nodeData.input_model ?? null);
  }, [nodeData.input_model]);

  const inputFields: {
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
    if (!inputSchema?.properties) return { visible, technical };
    const required = Array.isArray(inputSchema.required)
      ? inputSchema.required
      : [];

    const parser = new JsonSchemaParser(
      nodeData.input_model ?? inputSchema ?? {},
    );

    Object.entries(inputSchema.properties).forEach(
      ([fieldKey, fieldSchema]) => {
        const schemaObj = fieldSchema as Record<string, any>;
        const resolved = resolveSchemaDeep(
          schemaObj,
          nodeData.input_model ?? inputSchema ?? {},
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
          (resolved &&
            (resolved["x-autofilled"] === true ||
              resolved["x-autofillled"] === true)),
        );
        if (isAutofilled) return;

        const isTechnical = Boolean(
          parsed["x-technical"] === true || schemaObj["x-technical"] === true,
        );

        const entry = {
          fieldKey,
          schema: schemaObj,
          required: required.includes(fieldKey),
        };

        if (isTechnical) {
          technical.push(entry);
        } else {
          visible.push(entry);
        }
      },
    );

    return { visible, technical };
  }, [inputSchema, nodeData.input_model]);

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

  const isIfNode = nodeData.key === "if_node";
  const conditionField = inputFields.visible.find(
    (field) => field.fieldKey === "condition",
  );
  const visibleValueFields =
    isIfNode && conditionField
      ? inputFields.visible.filter((field) => field.fieldKey !== "condition")
      : inputFields.visible;

  const totalFieldsCount =
    (inputFields.visible?.length ?? 0) + (inputFields.technical?.length ?? 0);

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-border bg-card/50 p-4 space-y-4">
        <div className="flex items-center justify-between gap-2">
          <div>
            <div className="text-sm font-semibold text-foreground">
              Input schema
            </div>
            <p className="text-xs text-muted-foreground">
              Fields declared by the backend schema and their expected types.
            </p>
          </div>
          <span className="text-xs text-muted-foreground">
            {totalFieldsCount} field{totalFieldsCount === 1 ? "" : "s"}
          </span>
        </div>

        {totalFieldsCount === 0 ? (
          <div className="rounded border border-border bg-muted/40 p-4 text-sm text-muted-foreground">
            This node has no input schema defined.
          </div>
        ) : (
          <div className="rounded border border-border bg-muted/20 overflow-hidden">
            <div className="grid gap-0 lg:grid-cols-[1.5fr_1fr_auto] bg-muted/50 px-4 py-2 text-[11px] uppercase tracking-wide text-muted-foreground border-b border-border">
              <div>Field name</div>
              <div>Type</div>
              <div className="text-right">Required</div>
            </div>
            <div className="divide-y divide-border">
              {inputFields.visible.map((field) => (
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
            Input values
          </div>
          <p className="text-xs text-muted-foreground">
            Edit the actual values for each input field here.
          </p>
        </div>

        {inputFields.visible.length === 0 &&
          inputFields.technical.length === 0 ? (
          <div className="rounded-xl border border-border bg-muted/40 p-4 text-sm text-muted-foreground">
            No editable inputs available for this node.
          </div>
        ) : (
          <div className="space-y-4">
            {isIfNode && conditionField ? (
              <ConditionBuilder
                current={String(nodeData.inputs.condition ?? "")}
                precedingNodes={precedingNodes}
                onChange={(value) => handleInputChange("condition", value)}
              />
            ) : null}
            {visibleValueFields.map((field) => (
              <SchemaFieldRenderer
                key={field.fieldKey}
                fieldKey={field.fieldKey}
                schema={field.schema}
                value={nodeData.inputs[field.fieldKey]}
                onChange={(value) => handleInputChange(field.fieldKey, value)}
                onDropReference={(path) =>
                  handleInputChange(field.fieldKey, path)
                }
                rootSchema={nodeData.input_model ?? undefined}
              />
            ))}
          </div>
        )}
      </div>

      {/* Technical input fields block */}
      {inputFields.technical && inputFields.technical.length > 0 ? (
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
              {inputFields.technical.map((field) => (
                <SchemaFieldRenderer
                  fieldKey={field.fieldKey}
                  schema={field.schema}
                  value={nodeData.inputs[field.fieldKey]}
                  onChange={(value) => handleInputChange(field.fieldKey, value)}
                  onDropReference={(path) =>
                    handleInputChange(field.fieldKey, path)
                  }
                  rootSchema={nodeData.input_model ?? undefined}
                />
              ))}
            </div>
          )}
        </div>
      ) : null}

      <OutputReferencePanel precedingNodes={precedingNodes} />
    </div>
  );
};

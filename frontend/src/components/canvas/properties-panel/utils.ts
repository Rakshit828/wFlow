type ResponseField = { name: string; type: string };

export const getNodeTypeColor = (type: string): string => {
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

export const getTypeLabel = (type: string): string => {
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

export const parseFieldsFromConfig = (config: any): ResponseField[] => {
  const responseModel = config?.response_model as
    | Record<string, any>
    | undefined;
  const output = responseModel?.output;
  if (!output || typeof output !== "object" || !output.properties) {
    return [];
  }
  return Object.entries(output.properties).map(([fieldName, fieldSchema]) => {
    if (
      fieldSchema &&
      typeof fieldSchema === "object" &&
      typeof (fieldSchema as any).type === "string"
    ) {
      return { name: fieldName, type: (fieldSchema as any).type };
    }
    if (typeof fieldSchema === "string") {
      return {
        name: fieldName,
        type: fieldSchema === "str" ? "string" : fieldSchema,
      };
    }
    return { name: fieldName, type: "string" };
  });
};

export const buildResponseModelSchema = (fields: ResponseField[]) => {
  const properties: Record<string, any> = {};
  fields.forEach((field) => {
    if (!field.name.trim()) return;
    if (field.type === "array") {
      properties[field.name] = { type: "array", items: { type: "string" } };
    } else if (field.type === "object") {
      properties[field.name] = { type: "object", properties: {} };
    } else {
      properties[field.name] = { type: field.type };
    }
  });
  return {
    output: {
      type: "object",
      properties,
    },
  };
};

export const generateOutputPath = (
  nodeName: string,
  fieldKey: string,
  isNested = false,
): string => {
  if (isNested) {
    return `${nodeName}.outputs.output.${fieldKey}`;
  }
  return `${nodeName}.outputs.${fieldKey}`;
};

export const serializeInputValue = (value: unknown): string => {
  if (value == null) return "";
  if (typeof value === "string") return value;
  if (typeof value === "boolean" || typeof value === "number")
    return String(value);
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
};

export const parseInputArrayString = (value: string): string[] => {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
};

export const safeParseJson = (value: string): unknown => {
  try {
    return JSON.parse(value);
  } catch {
    return value;
  }
};

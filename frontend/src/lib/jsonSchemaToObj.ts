/**
 * jsonSchemaToObject.ts
 * Full-fledged JSON Schema → descriptive JS object converter (runtime).
 *
 * Supports:
 *  - Primitive types: string, number, integer, boolean, null
 *  - object  (with properties)
 *  - array   (with items / prefixItems / contains)
 *  - enum / const
 *  - $ref    (local #/$defs and recursive)
 *  - anyOf / oneOf / allOf / not
 *  - if / then / else
 *  - Required fields, defaults, titles
 *  - Nullable shorthands
 *  - Circular-reference guard
 */

// ─── Types ────────────────────────────────────────────────────────────────────

export type SchemaValue =
  | string                        // e.g. "string", "integer", 'literal["a","b"]'
  | SchemaObject
  | SchemaArray
  | null;

export interface SchemaObject {
  [key: string]: SchemaValue;
}

export type SchemaArray = SchemaValue[];

// ─── Options ──────────────────────────────────────────────────────────────────

export interface ConvertOptions {
  /**
   * When true, required fields are annotated with "(required)" suffix.
   * Default: true
   */
  annotateRequired?: boolean;

  /**
   * When true, default values are shown as "(default: <value>)" suffix.
   * Default: true
   */
  annotateDefaults?: boolean;

  /**
   * When true, field titles from the schema are preserved as comments in the key.
   * Default: false
   */
  annotateTitle?: boolean;

  /**
   * Max depth to recurse before emitting "...".
   * Default: 20
   */
  maxDepth?: number;
}

const DEFAULT_OPTIONS: Required<ConvertOptions> = {
  annotateRequired: true,
  annotateDefaults: true,
  annotateTitle: false,
  maxDepth: 20,
};

// ─── Main entry ───────────────────────────────────────────────────────────────

/**
 * Convert a JSON Schema object into a descriptive JS object whose values
 * describe the expected data type / shape of each field.
 *
 * @param schema   - The root JSON Schema (plain JS object).
 * @param options  - Optional conversion options.
 * @returns        A plain JS object that mirrors the schema's shape.
 */
export function jsonSchemaToObject(
  schema: Record<string, unknown>,
  options: ConvertOptions = {}
): SchemaValue {
  const opts: Required<ConvertOptions> = { ...DEFAULT_OPTIONS, ...options };
  const visiting = new Set<string>(); // circular-ref guard (tracks $def names)
  return convertSchema(schema, schema, opts, visiting, 0, []);
}

// ─── Core recursive converter ─────────────────────────────────────────────────

function convertSchema(
  schema: unknown,
  root: Record<string, unknown>,
  opts: Required<ConvertOptions>,
  visiting: Set<string>,
  depth: number,
  requiredFields: string[]
): SchemaValue {
  if (depth > opts.maxDepth) return "...";
  if (schema === true) return "any";
  if (schema === false) return "never";
  if (schema == null || typeof schema !== "object" || Array.isArray(schema)) {
    return "unknown";
  }

  const s = schema as Record<string, unknown>;

  // ── $ref ──────────────────────────────────────────────────────────────────
  if ("$ref" in s) {
    return resolveRef(s["$ref"] as string, root, opts, visiting, depth);
  }

  // ── const ─────────────────────────────────────────────────────────────────
  if ("const" in s) {
    return `literal[${JSON.stringify(s["const"])}]`;
  }

  // ── enum ──────────────────────────────────────────────────────────────────
  if ("enum" in s && Array.isArray(s["enum"])) {
    const values = (s["enum"] as unknown[]).map((v) => JSON.stringify(v)).join(", ");
    return `literal[${values}]`;
  }

  // ── Composition keywords ───────────────────────────────────────────────────
  if ("anyOf" in s && Array.isArray(s["anyOf"])) {
    return composeUnion(s["anyOf"] as unknown[], "anyOf", root, opts, visiting, depth);
  }
  if ("oneOf" in s && Array.isArray(s["oneOf"])) {
    return composeUnion(s["oneOf"] as unknown[], "oneOf", root, opts, visiting, depth);
  }
  if ("allOf" in s && Array.isArray(s["allOf"])) {
    return composeAllOf(s["allOf"] as unknown[], root, opts, visiting, depth);
  }
  if ("not" in s) {
    const inner = convertSchema(s["not"], root, opts, visiting, depth + 1, []);
    return `not<${schemaValueToString(inner)}>`;
  }

  // ── if / then / else ──────────────────────────────────────────────────────
  if ("if" in s) {
    return handleIfThenElse(s, root, opts, visiting, depth);
  }

  // ── type array  e.g. "type": ["string", "null"] ───────────────────────────
  if ("type" in s && Array.isArray(s["type"])) {
    const types = (s["type"] as string[]).map((t) =>
      convertSchema({ ...s, type: t }, root, opts, visiting, depth, requiredFields)
    );
    return types.length === 1 ? types[0] : unionString(types);
  }

  // ── By type ───────────────────────────────────────────────────────────────
  const type = s["type"] as string | undefined;

  switch (type) {
    case "object":
      return convertObject(s, root, opts, visiting, depth);

    case "array":
      return convertArray(s, root, opts, visiting, depth);

    case "string":
      return buildScalarType("string", s, opts);

    case "number":
      return buildScalarType("number", s, opts);

    case "integer":
      return buildScalarType("integer", s, opts);

    case "boolean":
      return buildScalarType("boolean", s, opts);

    case "null":
      return "null";

    default: {
      // No explicit type — infer from presence of keywords
      if ("properties" in s) {
        return convertObject(s, root, opts, visiting, depth);
      }
      if ("items" in s || "prefixItems" in s || "contains" in s) {
        return convertArray(s, root, opts, visiting, depth);
      }
      // Bare schema with no recognisable type
      return "any";
    }
  }
}

// ─── Object ───────────────────────────────────────────────────────────────────

function convertObject(
  s: Record<string, unknown>,
  root: Record<string, unknown>,
  opts: Required<ConvertOptions>,
  visiting: Set<string>,
  depth: number
): SchemaObject {
  const result: SchemaObject = {};
  const required: string[] = Array.isArray(s["required"])
    ? (s["required"] as string[])
    : [];

  const properties = (s["properties"] ?? {}) as Record<string, unknown>;

  for (const [key, propSchema] of Object.entries(properties)) {
    const isRequired = required.includes(key);
    let value = convertSchema(propSchema, root, opts, visiting, depth + 1, required);

    // Attach default annotation
    const propS = propSchema as Record<string, unknown>;
    if (opts.annotateDefaults && "default" in propS) {
      value = annotate(value, `default: ${JSON.stringify(propS["default"])}`);
    }
    // Attach required annotation
    if (opts.annotateRequired && isRequired) {
      value = annotate(value, "required");
    }
    // Attach title annotation
    if (opts.annotateTitle && propS["title"]) {
      value = annotate(value, `title: ${propS["title"]}`);
    }

    result[key] = value;
  }

  return result;
}

// ─── Array ────────────────────────────────────────────────────────────────────

function convertArray(
  s: Record<string, unknown>,
  root: Record<string, unknown>,
  opts: Required<ConvertOptions>,
  visiting: Set<string>,
  depth: number
): SchemaArray | string {
  // Tuple: prefixItems
  if ("prefixItems" in s && Array.isArray(s["prefixItems"])) {
    const tuple = (s["prefixItems"] as unknown[]).map((item) =>
      convertSchema(item, root, opts, visiting, depth + 1, [])
    );
    return tuple; // represents a fixed-length tuple
  }

  // items
  if ("items" in s) {
    if (s["items"] === false) return "never[]";
    const itemType = convertSchema(s["items"], root, opts, visiting, depth + 1, []);
    return [`${schemaValueToString(itemType)}[]`];
  }

  // contains
  if ("contains" in s) {
    const containsType = convertSchema(s["contains"], root, opts, visiting, depth + 1, []);
    return [`contains: ${schemaValueToString(containsType)}`];
  }

  return ["any[]"];
}

// ─── $ref resolver ────────────────────────────────────────────────────────────

function resolveRef(
  ref: string,
  root: Record<string, unknown>,
  opts: Required<ConvertOptions>,
  visiting: Set<string>,
  depth: number
): SchemaValue {
  if (!ref.startsWith("#/")) {
    // External ref — emit as-is
    return `$ref(${ref})`;
  }

  const path = ref.slice(2).split("/"); // e.g. ["$defs", "GroqModelConfig"]
  const refKey = path.join("/");

  // Circular reference guard
  if (visiting.has(refKey)) {
    return `circular($ref: #/${refKey})`;
  }

  // Resolve the path inside the root schema
  let node: unknown = root;
  for (const segment of path) {
    if (node == null || typeof node !== "object" || Array.isArray(node)) {
      return `unresolved($ref: ${ref})`;
    }
    node = (node as Record<string, unknown>)[segment];
  }

  if (node == null) return `unresolved($ref: ${ref})`;

  visiting.add(refKey);
  const result = convertSchema(node, root, opts, visiting, depth + 1, []);
  visiting.delete(refKey);
  return result;
}

// ─── Composition helpers ──────────────────────────────────────────────────────

function composeUnion(
  schemas: unknown[],
  keyword: "anyOf" | "oneOf",
  root: Record<string, unknown>,
  opts: Required<ConvertOptions>,
  visiting: Set<string>,
  depth: number
): SchemaValue {
  // Shortcut: ["type", "null"] pattern → nullable
  const types = schemas.map((s) => {
    if (typeof s === "object" && s !== null && !Array.isArray(s)) {
      const sc = s as Record<string, unknown>;
      if ("type" in sc && typeof sc["type"] === "string") return sc["type"];
    }
    return null;
  });

  const nonNullTypes = types.filter((t) => t !== "null");
  const hasNull = types.includes("null");

  if (nonNullTypes.length === 1 && hasNull && nonNullTypes[0]) {
    // Nullable shorthand
    return `${nonNullTypes[0]} | null`;
  }

  const resolved = schemas.map((s) =>
    convertSchema(s, root, opts, visiting, depth + 1, [])
  );

  // If all resolved values are simple strings → union string
  if (resolved.every((r) => typeof r === "string")) {
    return `${keyword}(${resolved.join(" | ")})`;
  }

  // Mixed: emit an array labelled with the keyword
  return { [keyword]: resolved } as unknown as SchemaObject;
}

function composeAllOf(
  schemas: unknown[],
  root: Record<string, unknown>,
  opts: Required<ConvertOptions>,
  visiting: Set<string>,
  depth: number
): SchemaValue {
  // Merge all resolved objects if possible
  const resolved = schemas.map((s) =>
    convertSchema(s, root, opts, visiting, depth + 1, [])
  );

  const allObjects = resolved.every(
    (r) => typeof r === "object" && r !== null && !Array.isArray(r)
  );

  if (allObjects) {
    return Object.assign({}, ...(resolved as SchemaObject[])) as SchemaObject;
  }

  // Otherwise represent as intersection
  const stringified = resolved.map(schemaValueToString);
  return `allOf(${stringified.join(" & ")})`;
}

function handleIfThenElse(
  s: Record<string, unknown>,
  root: Record<string, unknown>,
  opts: Required<ConvertOptions>,
  visiting: Set<string>,
  depth: number
): SchemaValue {
  const ifType = convertSchema(s["if"], root, opts, visiting, depth + 1, []);
  const thenType = s["then"]
    ? convertSchema(s["then"], root, opts, visiting, depth + 1, [])
    : "any";
  const elseType = s["else"]
    ? convertSchema(s["else"], root, opts, visiting, depth + 1, [])
    : "any";

  return `if(${schemaValueToString(ifType)}) then(${schemaValueToString(thenType)}) else(${schemaValueToString(elseType)})`;
}

// ─── Scalar type builder ──────────────────────────────────────────────────────

function buildScalarType(
  base: string,
  s: Record<string, unknown>,
  _opts: Required<ConvertOptions>
): string {
  const constraints: string[] = [];

  if ("minLength" in s) constraints.push(`minLength: ${s["minLength"]}`);
  if ("maxLength" in s) constraints.push(`maxLength: ${s["maxLength"]}`);
  if ("pattern" in s) constraints.push(`pattern: "${s["pattern"]}"`);
  if ("format" in s) constraints.push(`format: ${s["format"]}`);
  if ("minimum" in s) constraints.push(`min: ${s["minimum"]}`);
  if ("maximum" in s) constraints.push(`max: ${s["maximum"]}`);
  if ("exclusiveMinimum" in s) constraints.push(`exclusiveMin: ${s["exclusiveMinimum"]}`);
  if ("exclusiveMaximum" in s) constraints.push(`exclusiveMax: ${s["exclusiveMaximum"]}`);
  if ("multipleOf" in s) constraints.push(`multipleOf: ${s["multipleOf"]}`);

  if (constraints.length === 0) return base;
  return `${base}(${constraints.join(", ")})`;
}

// ─── Annotation helpers ───────────────────────────────────────────────────────

function annotate(value: SchemaValue, note: string): SchemaValue {
  if (typeof value === "string") return `${value} (${note})`;
  // For objects/arrays we can't easily append; wrap in a meta key
  if (typeof value === "object" && value !== null && !Array.isArray(value)) {
    return { ...(value as SchemaObject), _meta: note } as SchemaObject;
  }
  return value;
}

// ─── Stringify helper (for inline composition expressions) ────────────────────

function schemaValueToString(value: SchemaValue): string {
  if (value === null) return "null";
  if (typeof value === "string") return value;
  if (Array.isArray(value)) {
    return `[${value.map(schemaValueToString).join(", ")}]`;
  }
  // object
  return `{${Object.entries(value as SchemaObject)
    .map(([k, v]) => `${k}: ${schemaValueToString(v)}`)
    .join(", ")}}`;
}

function unionString(values: SchemaValue[]): string {
  return values.map(schemaValueToString).join(" | ");
}

// ─── CLI / demo ───────────────────────────────────────────────────────────────

const exampleSchema = {
  $defs: {
    GroqModelConfig: {
      properties: {
        response_model: {
          additionalProperties: true,
          title: "Response Model",
          type: "object",
        },
        model: {
          $ref: "#/$defs/GroqModelEnum",
          default: "openai/gpt-oss-120b",
        },
        max_tokens: {
          anyOf: [{ type: "integer" }, { type: "null" }],
          default: null,
          title: "Max Tokens",
        },
        system_prompt: {
          default: "Your are a helpful AI Assistant.",
          title: "System Prompt",
          type: "string",
        },
      },
      required: ["response_model"],
      title: "GroqModelConfig",
      type: "object",
    },
    GroqModelEnum: {
      enum: [
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "llama-3.3-70b-versatile",
        "moonshotai/kimi-k2-instruct-0905",
        "qwen/qwen3-32b",
      ],
      title: "GroqModelEnum",
      type: "string",
    },
  },
  additionalProperties: true,
  properties: {
    prompt: {
      title: "Prompt",
      type: "string",
    },
    config: {
      $ref: "#/$defs/GroqModelConfig",
    },
  },
  required: ["prompt", "config"],
  title: "GroqCallParams",
  type: "object",
};

const result = jsonSchemaToObject(exampleSchema, {
  annotateRequired: true,
  annotateDefaults: true,
  annotateTitle: false,
});

console.log("Converted schema object:");
console.log(JSON.stringify(result, null, 2));
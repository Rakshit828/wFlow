export type FieldType =
  | "string"
  | "number"
  | "integer"
  | "boolean"
  | "null"
  | "array"
  | "object"
  | "enum"
  | "const"
  | "anyOf"
  | "oneOf"
  | "allOf"
  | "not"
  | "if-then-else"
  | "union"
  | "unknown"
  | (string & {}); // allows custom / $ref-derived type names

export interface FieldProperties {
  /** Resolved logical type (see FieldType). */
  type: FieldType;

  /** Default value declared in the schema. */
  default?: any;

  /** Human-readable description. */
  description?: string;

  /** Human-readable title. */
  title?: string;

  // ── String constraints ────────────────────────────────────────────────────
  minLength?: number;
  maxLength?: number;
  pattern?: string;
  format?: string; // e.g. "date-time", "email", "uri", "uuid" …

  // ── Numeric constraints ───────────────────────────────────────────────────
  minimum?: number;
  maximum?: number;
  exclusiveMinimum?: number | boolean;
  exclusiveMaximum?: number | boolean;
  multipleOf?: number;

  // ── Array constraints ─────────────────────────────────────────────────────
  minItems?: number;
  maxItems?: number;
  uniqueItems?: boolean;
  /**
   * Resolved schema for array items.
   * When `items` is an array (tuple), each element is parsed and stored here.
   */
  items?: FieldProperties | FieldProperties[];
  prefixItems?: FieldProperties[]; // Draft-2020-12 tuple items
  contains?: FieldProperties;
  minContains?: number;
  maxContains?: number;

  // ── Object constraints ────────────────────────────────────────────────────
  minProperties?: number;
  maxProperties?: number;
  required?: string[];
  /** Recursively parsed properties of an object schema. */
  properties?: ParsedJsonSchema;
  additionalProperties?: boolean | FieldProperties;
  patternProperties?: Record<string, FieldProperties>;
  unevaluatedProperties?: boolean | FieldProperties;
  dependentRequired?: Record<string, string[]>;
  dependentSchemas?: Record<string, FieldProperties>;
  propertyNames?: FieldProperties;

  // ── Enum / const ──────────────────────────────────────────────────────────
  /** Allowed literal values when type === "enum". */
  enumValues?: any[];
  /** The single allowed value when type === "const". */
  constValue?: any;

  // ── Composite keywords ────────────────────────────────────────────────────
  anyOf?: FieldProperties[];
  oneOf?: FieldProperties[];
  allOf?: FieldProperties[];
  not?: FieldProperties;
  ifSchema?: FieldProperties;
  thenSchema?: FieldProperties;
  elseSchema?: FieldProperties;

  // ── $ref / $defs ─────────────────────────────────────────────────────────
  /** Original $ref string before resolution (for debugging / display). */
  $ref?: string;
  /** Whether this field was produced by resolving a $ref. */
  resolved?: boolean;

  // ── Metadata ─────────────────────────────────────────────────────────────
  examples?: any[];
  readOnly?: boolean;
  writeOnly?: boolean;
  deprecated?: boolean;
  $comment?: string;
  contentEncoding?: string;
  contentMediaType?: string;
  contentSchema?: FieldProperties;

  /** Catch-all for any non-standard vendor extensions (x-* keys). */
  [extension: string]: any;
}

export interface ParsedJsonSchema {
  [field: string]: FieldProperties;
}

export interface RawJsonSchema {
  $schema?: string;
  $id?: string;
  $ref?: string;
  $defs?: Record<string, RawJsonSchema>;
  definitions?: Record<string, RawJsonSchema>; // Draft-04/07 alias

  type?: string | string[];
  enum?: any[];
  const?: any;

  title?: string;
  description?: string;
  default?: any;
  examples?: any[];
  readOnly?: boolean;
  writeOnly?: boolean;
  deprecated?: boolean;
  $comment?: string;

  // String
  minLength?: number;
  maxLength?: number;
  pattern?: string;
  format?: string;
  contentEncoding?: string;
  contentMediaType?: string;
  contentSchema?: RawJsonSchema;

  // Number
  minimum?: number;
  maximum?: number;
  exclusiveMinimum?: number | boolean;
  exclusiveMaximum?: number | boolean;
  multipleOf?: number;

  // Array
  items?: RawJsonSchema | RawJsonSchema[];
  prefixItems?: RawJsonSchema[];
  contains?: RawJsonSchema;
  minItems?: number;
  maxItems?: number;
  uniqueItems?: boolean;
  minContains?: number;
  maxContains?: number;

  // Object
  properties?: Record<string, RawJsonSchema>;
  additionalProperties?: boolean | RawJsonSchema;
  patternProperties?: Record<string, RawJsonSchema>;
  unevaluatedProperties?: boolean | RawJsonSchema;
  required?: string[];
  minProperties?: number;
  maxProperties?: number;
  dependentRequired?: Record<string, string[]>;
  dependentSchemas?: Record<string, RawJsonSchema>;
  propertyNames?: RawJsonSchema;

  // Composite
  anyOf?: RawJsonSchema[];
  oneOf?: RawJsonSchema[];
  allOf?: RawJsonSchema[];
  not?: RawJsonSchema;
  if?: RawJsonSchema;
  then?: RawJsonSchema;
  else?: RawJsonSchema;

  [key: string]: any; // allow vendor extensions
}

// ─── Parser Options ───────────────────────────────────────────────────────────

export interface ParserOptions {
  /**
   * External $defs / definitions to merge before parsing.
   * Useful when you have cross-file references.
   */
  externalDefs?: Record<string, RawJsonSchema>;

  /**
   * Maximum recursion depth when resolving $ref or nested schemas.
   * Prevents infinite loops on circular schemas.
   * @default 20
   */
  maxDepth?: number;

  /**
   * When true, fields with no `description` inherit the nearest ancestor
   * description found while traversing.
   * @default false
   */
  inheritDescription?: boolean;

  /**
   * When true, throw on unresolvable $ref.
   * When false (default), use the ref name as the type string.
   * @default false
   */
  strictRef?: boolean;
}

// ─── Internal helpers ─────────────────────────────────────────────────────────

type DefsMap = Map<string, RawJsonSchema>;

/** Build a flat map of all $defs / definitions anchored under `#/$defs/…`. */
function buildDefsMap(
  schema: RawJsonSchema,
  external?: Record<string, RawJsonSchema>,
): DefsMap {
  const map: DefsMap = new Map();

  const addAll = (source: Record<string, RawJsonSchema> | undefined) => {
    if (!source) return;
    for (const [key, val] of Object.entries(source)) {
      map.set(key, val);
      map.set(`#/$defs/${key}`, val);
      map.set(`#/definitions/${key}`, val);
      map.set(`#/components/schemas/${key}`, val); // OpenAPI compat
    }
  };

  addAll(schema.$defs);
  addAll(schema.definitions);
  addAll(external);
  return map;
}

/** Resolve a $ref string against the defs map. Returns null if not found. */
function resolveRef(ref: string, defs: DefsMap): RawJsonSchema | null {
  // Direct hit
  if (defs.has(ref)) return defs.get(ref)!;

  // Strip leading '#/$defs/', '#/definitions/', '#/components/schemas/'
  const patterns = [
    /^#\/\$defs\//,
    /^#\/definitions\//,
    /^#\/components\/schemas\//,
  ];
  for (const p of patterns) {
    const name = ref.replace(p, "");
    if (defs.has(name)) return defs.get(name)!;
  }
  return null;
}

/** Derive a human-friendly type name from an unresolvable $ref. */
function refToTypeName(ref: string): string {
  const parts = ref.split("/");
  return parts[parts.length - 1] ?? ref;
}

/** Collect all vendor-extension keys (x-*). */
function extractExtensions(raw: RawJsonSchema): Record<string, any> {
  const out: Record<string, any> = {};
  for (const key of Object.keys(raw)) {
    if (key.startsWith("x-")) out[key] = raw[key];
  }
  return out;
}

/** Determine the primary FieldType from a raw schema node. */
function resolveType(raw: RawJsonSchema): FieldType {
  // $ref alone (not yet resolved) – caller handles this
  if (raw.$ref && Object.keys(raw).length === 1) return "unknown";

  if (raw.enum !== undefined) return "enum";
  if (raw.const !== undefined) return "const";

  if (raw.anyOf) return "anyOf";
  if (raw.oneOf) return "oneOf";
  if (raw.allOf) return "allOf";
  if (raw.not && !raw.type && !raw.properties) return "not";
  if (raw.if) return "if-then-else";

  if (Array.isArray(raw.type)) {
    if (raw.type.length === 1) return raw.type[0] as FieldType;
    return "union";
  }

  if (raw.type) return raw.type as FieldType;

  // Structural inference when `type` is omitted
  if (raw.properties || raw.additionalProperties !== undefined) return "object";
  if (raw.items || raw.prefixItems) return "array";
  if (
    raw.pattern ||
    raw.format ||
    raw.minLength !== undefined ||
    raw.maxLength !== undefined
  )
    return "string";
  if (
    raw.minimum !== undefined ||
    raw.maximum !== undefined ||
    raw.multipleOf !== undefined
  )
    return "number";

  return "unknown";
}

// ─── Core parser class ────────────────────────────────────────────────────────

export class JsonSchemaParser {
  private defs: DefsMap;
  private opts: Required<ParserOptions>;
  private refStack: Set<string> = new Set(); // cycle detection

  constructor(schema: RawJsonSchema, opts: ParserOptions = {}) {
    this.opts = {
      externalDefs: opts.externalDefs ?? {},
      maxDepth: opts.maxDepth ?? 20,
      inheritDescription: opts.inheritDescription ?? false,
      strictRef: opts.strictRef ?? false,
    };
    this.defs = buildDefsMap(schema, this.opts.externalDefs);
  }

  // ── Public API ─────────────────────────────────────────────────────────────

  /**
   * Parse a complete JSON Schema and return a flat `ParsedJsonSchema` map
   * covering the top-level `properties` (or any top-level composite fields).
   */
  parse(schema: RawJsonSchema): ParsedJsonSchema {
    this.refStack.clear();

    // Resolve top-level $ref
    const resolved = this.maybeResolveRef(schema, 0);

    // If the top-level schema is an object with properties, parse them.
    if (resolved.properties) {
      return this.parseProperties(resolved.properties, 0);
    }

    // Otherwise treat the whole schema as a single anonymous field.
    return { root: this.parseField(resolved, 0) };
  }

  /**
   * Parse an arbitrary sub-schema node into `FieldProperties`.
   * Useful if you want to parse a single field definition in isolation.
   */
  parseField(raw: RawJsonSchema, depth = 0): FieldProperties {
    if (depth > this.opts.maxDepth) {
      return { type: "unknown", description: "[max depth reached]" };
    }

    // ── Resolve $ref first ─────────────────────────────────────────────────
    let schema = raw;
    let refString: string | undefined;

    if (raw.$ref) {
      refString = raw.$ref;
      const found = resolveRef(raw.$ref, this.defs);
      if (found) {
        if (this.refStack.has(raw.$ref)) {
          // Circular reference – return stub
          return {
            type: refToTypeName(raw.$ref) as FieldType,
            $ref: raw.$ref,
            description: "[circular reference]",
          };
        }
        this.refStack.add(raw.$ref);
        // Merge sibling keywords on top of resolved schema (JSON Schema 2019-09+)
        schema = { ...found, ...raw, $ref: undefined } as RawJsonSchema;
        this.refStack.delete(raw.$ref);
      } else {
        if (this.opts.strictRef) {
          throw new Error(`Cannot resolve $ref: ${raw.$ref}`);
        }
        return {
          type: refToTypeName(raw.$ref) as FieldType,
          $ref: raw.$ref,
          resolved: false,
        };
      }
    }

    const type = resolveType(schema);
    const field: FieldProperties = { type };

    if (refString) {
      field.$ref = refString;
      field.resolved = true;
    }

    // ── Universal metadata ─────────────────────────────────────────────────
    if (schema.title !== undefined) field.title = schema.title;
    if (schema.description !== undefined)
      field.description = schema.description;
    if (schema.default !== undefined) field.default = schema.default;
    if (schema.examples !== undefined) field.examples = schema.examples;
    if (schema.readOnly !== undefined) field.readOnly = schema.readOnly;
    if (schema.writeOnly !== undefined) field.writeOnly = schema.writeOnly;
    if (schema.deprecated !== undefined) field.deprecated = schema.deprecated;
    if (schema.$comment !== undefined) field.$comment = schema.$comment;

    // ── Enum / const ───────────────────────────────────────────────────────
    if (schema.enum !== undefined) field.enumValues = schema.enum;
    if (schema.const !== undefined) field.constValue = schema.const;

    // ── String constraints ─────────────────────────────────────────────────
    if (schema.minLength !== undefined) field.minLength = schema.minLength;
    if (schema.maxLength !== undefined) field.maxLength = schema.maxLength;
    if (schema.pattern !== undefined) field.pattern = schema.pattern;
    if (schema.format !== undefined) field.format = schema.format;
    if (schema.contentEncoding !== undefined)
      field.contentEncoding = schema.contentEncoding;
    if (schema.contentMediaType !== undefined)
      field.contentMediaType = schema.contentMediaType;
    if (schema.contentSchema !== undefined)
      field.contentSchema = this.parseField(schema.contentSchema, depth + 1);

    // ── Numeric constraints ────────────────────────────────────────────────
    if (schema.minimum !== undefined) field.minimum = schema.minimum;
    if (schema.maximum !== undefined) field.maximum = schema.maximum;
    if (schema.exclusiveMinimum !== undefined)
      field.exclusiveMinimum = schema.exclusiveMinimum;
    if (schema.exclusiveMaximum !== undefined)
      field.exclusiveMaximum = schema.exclusiveMaximum;
    if (schema.multipleOf !== undefined) field.multipleOf = schema.multipleOf;

    // ── Array constraints ──────────────────────────────────────────────────
    if (schema.minItems !== undefined) field.minItems = schema.minItems;
    if (schema.maxItems !== undefined) field.maxItems = schema.maxItems;
    if (schema.uniqueItems !== undefined)
      field.uniqueItems = schema.uniqueItems;
    if (schema.minContains !== undefined)
      field.minContains = schema.minContains;
    if (schema.maxContains !== undefined)
      field.maxContains = schema.maxContains;

    if (schema.items !== undefined) {
      if (Array.isArray(schema.items)) {
        field.items = schema.items.map((s) => this.parseField(s, depth + 1));
      } else {
        field.items = this.parseField(schema.items, depth + 1);
      }
    }

    if (schema.prefixItems !== undefined) {
      field.prefixItems = schema.prefixItems.map((s) =>
        this.parseField(s, depth + 1),
      );
    }

    if (schema.contains !== undefined)
      field.contains = this.parseField(schema.contains, depth + 1);

    // ── Object constraints ─────────────────────────────────────────────────
    if (schema.required !== undefined) field.required = schema.required;
    if (schema.minProperties !== undefined)
      field.minProperties = schema.minProperties;
    if (schema.maxProperties !== undefined)
      field.maxProperties = schema.maxProperties;
    if (schema.dependentRequired !== undefined)
      field.dependentRequired = schema.dependentRequired;

    if (schema.properties !== undefined) {
      field.properties = this.parseProperties(schema.properties, depth + 1);
    }

    if (schema.additionalProperties !== undefined) {
      field.additionalProperties =
        typeof schema.additionalProperties === "boolean"
          ? schema.additionalProperties
          : this.parseField(schema.additionalProperties, depth + 1);
    }

    if (schema.unevaluatedProperties !== undefined) {
      field.unevaluatedProperties =
        typeof schema.unevaluatedProperties === "boolean"
          ? schema.unevaluatedProperties
          : this.parseField(schema.unevaluatedProperties, depth + 1);
    }

    if (schema.patternProperties !== undefined) {
      field.patternProperties = Object.fromEntries(
        Object.entries(schema.patternProperties).map(([pattern, sub]) => [
          pattern,
          this.parseField(sub, depth + 1),
        ]),
      );
    }

    if (schema.dependentSchemas !== undefined) {
      field.dependentSchemas = Object.fromEntries(
        Object.entries(schema.dependentSchemas).map(([key, sub]) => [
          key,
          this.parseField(sub, depth + 1),
        ]),
      );
    }

    if (schema.propertyNames !== undefined)
      field.propertyNames = this.parseField(schema.propertyNames, depth + 1);

    // ── Composite keywords ─────────────────────────────────────────────────
    if (schema.anyOf !== undefined)
      field.anyOf = schema.anyOf.map((s) => this.parseField(s, depth + 1));

    if (schema.oneOf !== undefined)
      field.oneOf = schema.oneOf.map((s) => this.parseField(s, depth + 1));

    if (schema.allOf !== undefined)
      field.allOf = schema.allOf.map((s) => this.parseField(s, depth + 1));

    if (schema.not !== undefined)
      field.not = this.parseField(schema.not, depth + 1);

    if (schema.if !== undefined)
      field.ifSchema = this.parseField(schema.if, depth + 1);
    if (schema.then !== undefined)
      field.thenSchema = this.parseField(schema.then, depth + 1);
    if (schema.else !== undefined)
      field.elseSchema = this.parseField(schema.else, depth + 1);

    // ── Vendor extensions (x-*) ────────────────────────────────────────────
    Object.assign(field, extractExtensions(schema));

    return field;
  }

  // ── Private helpers ────────────────────────────────────────────────────────

  private parseProperties(
    props: Record<string, RawJsonSchema>,
    depth: number,
  ): ParsedJsonSchema {
    const result: ParsedJsonSchema = {};
    for (const [name, subSchema] of Object.entries(props)) {
      result[name] = this.parseField(subSchema, depth);
    }
    return result;
  }

  /** Resolve a top-level $ref while preserving sibling keywords. */
  private maybeResolveRef(schema: RawJsonSchema): RawJsonSchema {
    if (!schema.$ref) return schema;
    const found = resolveRef(schema.$ref, this.defs);
    if (!found) return schema;
    return { ...found, ...schema, $ref: undefined } as RawJsonSchema;
  }
}

/**
 * Parse a JSON Schema and return a flat `ParsedJsonSchema`.
 *
 * @example
 * ```ts
 * const schema = {
 *   type: "object",
 *   properties: {
 *     age: { type: "integer", minimum: 0, default: 18 },
 *     email: { type: "string", format: "email" },
 *     role: { enum: ["admin", "user", "guest"] }
 *   }
 * };
 *
 * const parsed = parseJsonSchema(schema);
 * // parsed.age  → { type: "integer", minimum: 0, default: 18 }
 * // parsed.email → { type: "string", format: "email" }
 * // parsed.role  → { type: "enum", enumValues: ["admin", "user", "guest"] }
 * ```
 */
export function parseJsonSchema(
  schema: RawJsonSchema,
  opts?: ParserOptions,
): ParsedJsonSchema {
  return new JsonSchemaParser(schema, opts).parse(schema);
}

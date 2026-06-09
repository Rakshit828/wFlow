import React from "react";
import { ChevronRight, ChevronDown } from "lucide-react";

interface OutputSchemaTreeProps {
  schema: Record<string, any>;
  basePath: string;
}

const SchemaTreeNode: React.FC<{
  name: string;
  schema: Record<string, any>;
  path: string;
}> = ({ name, schema, path }) => {
  const [expanded, setExpanded] = React.useState(false);
  const hasChildren =
    schema.properties && Object.keys(schema.properties).length > 0;

  const handleDragStart = (event: React.DragEvent<HTMLDivElement>) => {
    event.dataTransfer.effectAllowed = "copy";
    event.dataTransfer.setData("application/x-output-path", path);
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(path);
    } catch {
      // Ignore copy errors
    }
  };

  return (
    <div className="text-xs">
      <div
        draggable
        onDragStart={handleDragStart}
        onClick={() => hasChildren && setExpanded(!expanded)}
        className={`flex items-center gap-1 px-2 py-1 rounded cursor-${hasChildren ? "pointer" : "default"} ${hasChildren ? "hover:bg-accent" : ""} select-none`}
      >
        {hasChildren ? (
          expanded ? (
            <ChevronDown size={14} className="text-muted-foreground" />
          ) : (
            <ChevronRight size={14} className="text-muted-foreground" />
          )
        ) : (
          <div className="w-[14px]" />
        )}
        <span
          onClick={handleCopy}
          className="text-foreground/80 hover:text-primary transition-colors cursor-pointer"
        >
          {name}
        </span>
        <span className="text-muted-foreground ml-auto text-[10px]">
          {schema.type}
        </span>
      </div>
      {expanded && hasChildren && (
        <div className="ml-4 border-l border-border space-y-px">
          {Object.entries(schema.properties).map(([key, propSchema]) => (
            <SchemaTreeNode
              key={key}
              name={key}
              schema={propSchema as Record<string, any>}
              path={`${path}.${key}`}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export const OutputSchemaTree: React.FC<OutputSchemaTreeProps> = ({
  schema,
  basePath,
}) => {
  return (
    <div className="rounded-xl border border-border bg-muted/30 p-3 space-y-1 text-foreground/80">
      {schema.properties ? (
        Object.entries(schema.properties).map(([key, propSchema]) => (
          <SchemaTreeNode
            key={key}
            name={key}
            schema={propSchema as Record<string, any>}
            path={`${basePath}.${key}`}
          />
        ))
      ) : (
        <div className="text-[11px] text-muted-foreground italic">
          No schema properties available
        </div>
      )}
    </div>
  );
};

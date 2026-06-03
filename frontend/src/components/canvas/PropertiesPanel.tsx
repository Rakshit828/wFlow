import React from 'react';
import { 
  X, 
  Settings, 
  Trash2, 
  HelpCircle,
  Plus,
  Minus,
  Link,
  AlertCircle,
  Info,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { useWorkflowStore } from '../../store/useWorkflowStore';
import { NODE_SPEC_CATALOG } from '../../types/workflow';
import { asNodeData, inputStr } from '../../types/flow';

const getNodeTypeColor = (type: string): string => {
  switch (type) {
    case 'LLM': return 'text-amber-400 bg-amber-400/10 border-amber-400/20';
    case 'CONTROL_FLOW': return 'text-purple-400 bg-purple-400/10 border-purple-400/20';
    case 'ACTION': return 'text-blue-400 bg-blue-400/10 border-blue-400/20';
    case 'TRANSFORM': return 'text-teal-400 bg-teal-400/10 border-teal-400/20';
    case 'API': return 'text-indigo-400 bg-indigo-400/10 border-indigo-400/20';
    case 'DATA_SOURCE': return 'text-cyan-400 bg-cyan-400/10 border-cyan-400/20';
    case 'TRIGGER': return 'text-orange-400 bg-orange-400/10 border-orange-400/20';
    default: return 'text-slate-400 bg-slate-400/10 border-slate-400/20';
  }
};

const getTypeLabel = (type: string): string => {
  switch (type) {
    case 'LLM': return 'Language Model';
    case 'CONTROL_FLOW': return 'Control Flow';
    case 'ACTION': return 'Integration';
    case 'TRANSFORM': return 'Transform';
    case 'API': return 'External API';
    case 'DATA_SOURCE': return 'Data Source';
    case 'TRIGGER': return 'Trigger';
    default: return type;
  }
};

export const PropertiesPanel: React.FC = () => {
  const { 
    activeNodeId, 
    nodes, 
    updateNodeInputs, 
    updateNodeConfig, 
    deleteNode, 
    setActiveNodeId,
    getPrecedingNodes,
    nodeRegistry
  } = useWorkflowStore();

  const [activeTab, setActiveTab] = React.useState<'inputs' | 'config'>('inputs');
  const [copiedPath, setCopiedPath] = React.useState<string | null>(null);
  const [showSchemaInfo, setShowSchemaInfo] = React.useState(false);

  const activeNode = React.useMemo(() => {
    return nodes.find(n => n.id === activeNodeId) || null;
  }, [nodes, activeNodeId]);

  const precedingNodes = React.useMemo(() => {
    if (!activeNodeId) return [];
    return getPrecedingNodes(activeNodeId);
  }, [activeNodeId, getPrecedingNodes]);

  if (!activeNode) return null;

  const data = asNodeData(activeNode.data);
  const nodeKey = data.key;
  const inputs = data.inputs;
  const config = data.config;
  const ifValues = (inputs.values as Record<string, unknown> | undefined) ?? {};
  const switchCases = Array.isArray(inputs.cases) ? (inputs.cases as string[]) : [];

  const handleInputChange = (key: string, value: any) => {
    updateNodeInputs(activeNode.id, { [key]: value });
  };

  const handleConfigChange = (key: string, value: any) => {
    updateNodeConfig(activeNode.id, { [key]: value });
  };

  const handleCopyPath = (path: string) => {
    navigator.clipboard.writeText(path);
    setCopiedPath(path);
    setTimeout(() => setCopiedPath(null), 2000);
  };

  const handleInsertReference = (path: string, inputFieldKey: string) => {
    const currentValue = String(inputs[inputFieldKey] ?? '');
    if (typeof currentValue === 'string') {
      const isTemplateInput = inputFieldKey === 'prompt' || inputFieldKey === 'body' || inputFieldKey === 'condition';
      const referenceToInsert = isTemplateInput ? `{${path}}` : path;
      handleInputChange(inputFieldKey, currentValue + referenceToInsert);
    }
  };

  // Helper to render static preceding output variables for the Autocomplete Assistant
  const renderAutocompleteAssistant = (targetFieldKey: string) => {
    if (precedingNodes.length === 0) return null;

    return (
      <div className="mt-3 p-3 rounded-lg bg-muted/40 border border-border">
        <div className="flex items-center gap-1.5 text-xs font-bold text-indigo-400 uppercase tracking-wider mb-2">
          <Link size={12} />
          Reference Injector Assistant
        </div>
        <p className="text-xs text-muted-foreground leading-normal mb-2.5">
          Select an output path from a preceding node to inject it as a dynamic reference variable:
        </p>
        <div className="max-h-[140px] overflow-y-auto space-y-2 pr-1">
          {precedingNodes.map(pn => {
            const outputsList: string[] = [];
            
            // 1. If output_model is defined in the node's schema
            if (pn.output_model && pn.output_model.properties) {
              Object.entries(pn.output_model.properties).forEach(([k, propVal]: [string, any]) => {
                if (k === 'output' && propVal && propVal.properties) {
                  // Nesting check for standard output structures (e.g. LLMs)
                  Object.keys(propVal.properties).forEach(subK => {
                    outputsList.push(`${pn.name}.outputs.output.${subK}`);
                  });
                } else {
                  outputsList.push(`${pn.name}.outputs.${k}`);
                }
              });
            }
            
            // 2. Custom schema overlays/fallbacks for dynamic LLM configuration at runtime
            if (pn.key.startsWith('llm.')) {
              const responseSchema = pn.config?.response_model?.output || {};
              Object.keys(responseSchema).forEach(k => {
                const path = `${pn.name}.outputs.output.${k}`;
                if (!outputsList.includes(path)) {
                  outputsList.push(path);
                }
              });
              if (outputsList.length === 0) {
                outputsList.push(`${pn.name}.outputs.output`);
              }
            }

            // 3. Fallbacks for standard hardcoded nodes if output_model wasn't loaded
            if (outputsList.length === 0) {
              if (pn.key === 'if_node') {
                outputsList.push(`${pn.name}.outputs.decision`);
              } else if (pn.key === 'switch_node') {
                outputsList.push(`${pn.name}.outputs.case`);
              } else if (pn.key.startsWith('gmail.')) {
                outputsList.push(`${pn.name}.outputs.id`);
                outputsList.push(`${pn.name}.outputs.threadId`);
              } else if (pn.key.startsWith('sheets.')) {
                outputsList.push(`${pn.name}.outputs.spreadsheet_id`);
                outputsList.push(`${pn.name}.outputs.values`);
              } else {
                outputsList.push(`${pn.name}.outputs.output`);
              }
            }

            return (
              <div key={pn.name} className="space-y-1">
                <span className="text-xs font-bold text-foreground block">
                  {pn.name} ({nodeRegistry[pn.key]?.name || NODE_SPEC_CATALOG[pn.key]?.name || pn.key})
                </span>
                <div className="flex flex-col gap-1 pl-1.5">
                  {outputsList.map(path => (
                    <div key={path} className="flex items-center justify-between gap-1.5 bg-background/60 hover:bg-background/90 border border-border px-1.5 py-1 rounded transition-all">
                      <code className="text-xs text-amber-300 truncate tracking-wide max-w-[170px]">{path}</code>
                      <div className="flex items-center gap-1 shrink-0">
                        <button
                          type="button"
                          onClick={() => handleCopyPath(path)}
                          className="text-[8px] bg-slate-800 text-foreground hover:text-white px-1 py-0.5 rounded border border-slate-700 hover:bg-slate-700 transition-colors"
                        >
                          {copiedPath === path ? 'Copied' : 'Copy'}
                        </button>
                        <button
                          type="button"
                          onClick={() => handleInsertReference(path, targetFieldKey)}
                          className="text-[8px] bg-indigo-600/30 text-indigo-300 hover:text-white px-1.5 py-0.5 rounded border border-indigo-500/30 hover:bg-indigo-600 transition-all font-semibold"
                        >
                          Inject
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderDynamicFormFromSchema = () => {
    const schema = data.input_model;
    if (!schema || !schema.properties) return null;

    return (
      <div className="space-y-4">
        {Object.entries(schema.properties).map(([fieldKey, propSchema]: [string, any]) => {
          if (fieldKey === 'config') return null;

          const title = propSchema.title || fieldKey;
          const description = propSchema.description;
          const isRequired = Array.isArray(schema.required) && schema.required.includes(fieldKey);

          return (
            <div key={fieldKey} className="space-y-1">
              <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide flex justify-between items-center">
                <span>
                  {title}
                  {isRequired && <span className="text-rose-400 ml-1">*</span>}
                </span>
                {description && (
                  <span className="text-[10px] text-slate-500 font-normal normal-case italic">
                    {description}
                  </span>
                )}
              </label>

              {propSchema.enum ? (
                <select
                  value={typeof inputs[fieldKey] === 'string' || typeof inputs[fieldKey] === 'number' ? String(inputs[fieldKey]) : ''}
                  onChange={(e) => handleInputChange(fieldKey, e.target.value)}
                  className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors"
                >
                  <option value="">Select option...</option>
                  {propSchema.enum.map((opt: string) => (
                    <option key={opt} value={opt}>{opt}</option>
                  ))}
                </select>
              ) : propSchema.type === 'boolean' ? (
                <select
                  value={String(inputs[fieldKey] ?? false)}
                  onChange={(e) => handleInputChange(fieldKey, e.target.value === 'true')}
                  className="w-full rounded-lg bg-background border border-border px-2 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors"
                >
                  <option value="true">True</option>
                  <option value="false">False</option>
                </select>
              ) : propSchema.type === 'array' && propSchema.items?.type === 'string' ? (
                <div className="space-y-1">
                  <input
                    type="text"
                    value={Array.isArray(inputs[fieldKey]) ? inputs[fieldKey].join(', ') : inputStr(inputs, fieldKey)}
                    onChange={(e) => {
                      const arr = e.target.value.split(',').map(s => s.trim()).filter(Boolean);
                      handleInputChange(fieldKey, arr);
                    }}
                    placeholder="Comma-separated values"
                    className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors"
                  />
                  {renderAutocompleteAssistant(fieldKey)}
                </div>
              ) : propSchema.type === 'integer' || propSchema.type === 'number' ? (
                <input
                  type="number"
                  value={typeof inputs[fieldKey] === 'number' || typeof inputs[fieldKey] === 'string' ? (inputs[fieldKey] as any) : ''}
                  onChange={(e) => handleInputChange(fieldKey, e.target.value === '' ? 0 : Number(e.target.value))}
                  className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors"
                />
              ) : propSchema.type === 'object' ? (
                <div className="space-y-1">
                  <textarea
                    value={typeof inputs[fieldKey] === 'string' ? inputs[fieldKey] : JSON.stringify(inputs[fieldKey] ?? {}, null, 2)}
                    onChange={(e) => {
                      let parsed = e.target.value;
                      try {
                        parsed = JSON.parse(e.target.value);
                      } catch {}
                      handleInputChange(fieldKey, parsed);
                    }}
                    rows={4}
                    placeholder='{"key": "value"}'
                    className="w-full rounded-lg bg-background border border-border p-2.5 text-xs text-foreground focus:outline-none focus:border-indigo-500 transition-colors font-mono resize-y"
                  />
                  {renderAutocompleteAssistant(fieldKey)}
                </div>
              ) : (
                <div className="space-y-1">
                  {fieldKey === 'prompt' || fieldKey === 'body' || fieldKey === 'condition' || fieldKey === 'template' ? (
                    <textarea
                      value={inputStr(inputs, fieldKey)}
                      onChange={(e) => handleInputChange(fieldKey, e.target.value)}
                      rows={4}
                      placeholder={`Enter ${title.toLowerCase()}...`}
                      className="w-full rounded-lg bg-background border border-border p-2.5 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors font-sans leading-normal resize-y"
                    />
                  ) : (
                    <input
                      type="text"
                      value={inputStr(inputs, fieldKey)}
                      onChange={(e) => handleInputChange(fieldKey, e.target.value)}
                      placeholder={`Enter ${title.toLowerCase()}...`}
                      className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors"
                    />
                  )}
                  {renderAutocompleteAssistant(fieldKey)}
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <aside 
      className="animate-slide-in-right w-[380px] h-full border-l border-border bg-card flex flex-col shadow-2xl relative z-40 shrink-0"
      style={{
        boxShadow: '-10px 0 30px -5px rgba(0, 0, 0, 0.6)'
      }}
    >
      {/* Header */}
      <div className="p-4 border-b border-border bg-muted/30">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2 min-w-0">
            <Settings className="text-primary shrink-0" size={18} />
            <h3 className="font-bold text-sm text-foreground uppercase tracking-wider truncate">Node properties</h3>
          </div>
          <button 
            type="button"
            onClick={() => setActiveNodeId(null)}
            className="p-1.5 rounded-lg bg-background hover:bg-accent text-muted-foreground hover:text-foreground border border-border transition-all hover:scale-105 active:scale-95"
          >
            <X size={14} />
          </button>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-muted-foreground font-mono leading-none truncate">{activeNode.id}</span>
          <span className={`text-[9px] px-1.5 py-0.5 rounded-md font-semibold border shrink-0 ${getNodeTypeColor(data.type)}`}>
            {getTypeLabel(data.type)}
          </span>
        </div>
        {/* Schema info toggle */}
        {data.input_model && (
          <button
            type="button"
            onClick={() => setShowSchemaInfo(!showSchemaInfo)}
            className="mt-2 flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground transition-colors"
          >
            <Info size={10} />
            <span>Schema info</span>
            {showSchemaInfo ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
          </button>
        )}
        {showSchemaInfo && data.input_model && (
          <div className="mt-2 p-2 rounded-lg bg-background/60 border border-border text-[10px] text-muted-foreground space-y-1 animate-tooltip">
            <p><span className="font-semibold text-foreground">Input fields:</span> {data.input_model.properties ? Object.keys(data.input_model.properties).length : 0}</p>
            {data.input_model.required && (
              <p><span className="font-semibold text-foreground">Required:</span> {data.input_model.required.join(', ')}</p>
            )}
            {data.output_model && (
              <p><span className="font-semibold text-foreground">Output fields:</span> {data.output_model.properties ? Object.keys(data.output_model.properties).length : 'dynamic'}</p>
            )}
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border text-sm font-semibold select-none bg-card">
        <button
          onClick={() => setActiveTab('inputs')}
          className={`flex-1 py-2.5 text-center transition-all border-b-2 tab-indicator ${
            activeTab === 'inputs' 
              ? 'text-indigo-400 border-indigo-500 bg-background/10' 
              : 'text-muted-foreground border-transparent hover:text-slate-200'
          }`}
        >
          Node Inputs
        </button>
        <button
          onClick={() => setActiveTab('config')}
          className={`flex-1 py-2.5 text-center transition-all border-b-2 tab-indicator ${
            activeTab === 'config' 
              ? 'text-indigo-400 border-indigo-500 bg-background/10' 
              : 'text-muted-foreground border-transparent hover:text-slate-200'
          }`}
        >
          Node Config
        </button>
      </div>

      {/* Form Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {activeTab === 'inputs' ? (
          <div className="space-y-4">
            {data.input_model ? (
              renderDynamicFormFromSchema()
            ) : (
              <>
                {/* LLM Input Prompts */}
                {nodeKey.startsWith('llm.') && (
              <div className="space-y-3">
                <div className="space-y-1">
                  <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide flex items-center justify-between">
                    Prompt Prompt Template
                    <span className="text-xs text-indigo-400 font-normal lowercase">interpolates variables</span>
                  </label>
                  <textarea
                    value={inputStr(inputs, 'prompt')}
                    onChange={(e) => handleInputChange('prompt', e.target.value)}
                    rows={4}
                    placeholder="Enter prompt e.g., Generate a blog about {topic}..."
                    className="w-full rounded-lg bg-background border border-border p-2.5 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors font-sans leading-normal resize-y"
                  />
                  {renderAutocompleteAssistant('prompt')}
                </div>

                {inputs.topics !== undefined && (
                  <div className="space-y-1 mt-2">
                    <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
                      Topics reference list
                    </label>
                    <input
                      type="text"
                      value={inputStr(inputs, 'topics')}
                      onChange={(e) => handleInputChange('topics', e.target.value)}
                      placeholder="e.g. node1.outputs.output.outlines[0]"
                      className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors"
                    />
                    {renderAutocompleteAssistant('topics')}
                  </div>
                )}
                
                {inputs.articles !== undefined && (
                  <div className="space-y-1 mt-2">
                    <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
                      Articles Reference List
                    </label>
                    <input
                      type="text"
                      value={inputStr(inputs, 'articles')}
                      onChange={(e) => handleInputChange('articles', e.target.value)}
                      placeholder="e.g. node2.outputs.output.article node3.outputs.output.article"
                      className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors"
                    />
                    {renderAutocompleteAssistant('articles')}
                  </div>
                )}

                {inputs.article !== undefined && (
                  <div className="space-y-1 mt-2">
                    <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
                      Article Input Reference
                    </label>
                    <input
                      type="text"
                      value={inputStr(inputs, 'article')}
                      onChange={(e) => handleInputChange('article', e.target.value)}
                      placeholder="e.g. groq_llm_node5.outputs.output.final_article"
                      className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors"
                    />
                    {renderAutocompleteAssistant('article')}
                  </div>
                )}
              </div>
            )}

            {/* Gmail Send / Draft Inputs */}
            {nodeKey.startsWith('gmail.') && (
              <div className="space-y-3">
                {inputs.to !== undefined && (
                  <div className="space-y-1">
                    <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
                      To (recipient email list)
                    </label>
                    <input
                      type="text"
                      value={Array.isArray(inputs.to) ? inputs.to.join(', ') : inputStr(inputs, 'to')}
                      onChange={(e) => {
                        const arr = e.target.value.split(',').map(s => s.trim()).filter(Boolean);
                        handleInputChange('to', arr);
                      }}
                      placeholder="comma-separated emails e.g. admin@domain.com"
                      className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors"
                    />
                  </div>
                )}
                {inputs.subject !== undefined && (
                  <div className="space-y-1">
                    <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
                      Subject Title
                    </label>
                    <input
                      type="text"
                      value={inputStr(inputs, 'subject')}
                      onChange={(e) => handleInputChange('subject', e.target.value)}
                      className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors"
                    />
                  </div>
                )}
                {inputs.body !== undefined && (
                  <div className="space-y-1">
                    <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
                      Email Body Content
                    </label>
                    <textarea
                      value={inputStr(inputs, 'body')}
                      onChange={(e) => handleInputChange('body', e.target.value)}
                      rows={5}
                      placeholder="Write email body, supporting {referencing_upstream_nodes} templates..."
                      className="w-full rounded-lg bg-background border border-border p-2.5 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors font-sans leading-normal resize-y"
                    />
                    {renderAutocompleteAssistant('body')}
                  </div>
                )}
                {inputs.label_id !== undefined && (
                  <div className="space-y-1">
                    <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
                      Gmail Label ID
                    </label>
                    <input
                      type="text"
                      value={inputStr(inputs, 'label_id')}
                      onChange={(e) => handleInputChange('label_id', e.target.value)}
                      placeholder="e.g. INBOX, STARRED, DRAFTS"
                      className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors font-mono"
                    />
                  </div>
                )}
              </div>
            )}

            {/* Sheets Inputs */}
            {nodeKey.startsWith('sheets.') && (
              <div className="space-y-3">
                {inputs.title !== undefined && (
                  <div className="space-y-1">
                    <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
                      Sheet Document Title
                    </label>
                    <input
                      type="text"
                      value={inputStr(inputs, 'title')}
                      onChange={(e) => handleInputChange('title', e.target.value)}
                      className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors"
                    />
                  </div>
                )}
                {inputs.spreadsheet_id !== undefined && (
                  <div className="space-y-1">
                    <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
                      Spreadsheet Document ID
                    </label>
                    <input
                      type="text"
                      value={inputStr(inputs, 'spreadsheet_id')}
                      onChange={(e) => handleInputChange('spreadsheet_id', e.target.value)}
                      placeholder="e.g. 1aBCDeFGhIJKlMnOPQrSTuvwxYz"
                      className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors font-mono"
                    />
                    {renderAutocompleteAssistant('spreadsheet_id')}
                  </div>
                )}
                {inputs.range !== undefined && (
                  <div className="space-y-1">
                    <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
                      A1 Cell Block Range
                    </label>
                    <input
                      type="text"
                      value={inputStr(inputs, 'range')}
                      onChange={(e) => handleInputChange('range', e.target.value)}
                      placeholder="e.g. Sheet1!A1:B10"
                      className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors font-mono"
                    />
                  </div>
                )}
                {inputs.value_input_option !== undefined && (
                  <div className="space-y-1">
                    <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
                      Value Input Option
                    </label>
                    <select
                      value={inputStr(inputs, 'value_input_option') || 'RAW'}
                      onChange={(e) => handleInputChange('value_input_option', e.target.value)}
                      className="w-full rounded-lg bg-background border border-border px-2 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors"
                    >
                      <option value="RAW">RAW (plain characters)</option>
                      <option value="USER_ENTERED">USER_ENTERED (interprets formatting/math)</option>
                    </select>
                  </div>
                )}
                {inputs.values !== undefined && (
                  <div className="space-y-1">
                    <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide flex justify-between">
                      Append Matrix Cells Payload
                      <span className="text-[8px] text-muted-foreground lowercase font-mono">expects array of arrays</span>
                    </label>
                    <textarea
                      value={typeof inputs.values === 'string' ? inputs.values : JSON.stringify(inputs.values || [])}
                      onChange={(e) => {
                        let parsed = e.target.value;
                        try {
                          parsed = JSON.parse(e.target.value);
                        } catch {}
                        handleInputChange('values', parsed);
                      }}
                      rows={3}
                      placeholder="e.g. [['col1', 'col2'], ['val1', 'val2']]"
                      className="w-full rounded-lg bg-background border border-border p-2.5 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors font-mono resize-y"
                    />
                    {renderAutocompleteAssistant('values')}
                  </div>
                )}
              </div>
            )}

            {/* Drive Upload Node */}
            {nodeKey === 'drive.upload' && (
              <div className="space-y-3">
                <div className="space-y-1">
                  <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
                    Content Upload Reference
                  </label>
                  <input
                    type="text"
                    value={inputStr(inputs, 'content_ref')}
                    onChange={(e) => handleInputChange('content_ref', e.target.value)}
                    placeholder="e.g. node_name.outputs.output.field"
                    className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors font-mono"
                  />
                  {renderAutocompleteAssistant('content_ref')}
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
                    File Target Name
                  </label>
                  <input
                    type="text"
                    value={inputStr(inputs, 'filename')}
                    onChange={(e) => handleInputChange('filename', e.target.value)}
                    className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
                    MIME Type specification
                  </label>
                  <input
                    type="text"
                    value={inputStr(inputs, 'mime_type')}
                    onChange={(e) => handleInputChange('mime_type', e.target.value)}
                    className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors font-mono"
                  />
                </div>
              </div>
            )}

            {/* IF Gate Inputs */}
            {nodeKey === 'if_node' && (
              <div className="space-y-3">
                <div className="space-y-1">
                  <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
                    Boolean condition expression
                  </label>
                  <input
                    type="text"
                    value={inputStr(inputs, 'condition')}
                    onChange={(e) => handleInputChange('condition', e.target.value)}
                    placeholder="e.g. word_count >= min_words"
                    className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors font-mono"
                  />
                  {renderAutocompleteAssistant('condition')}
                </div>

                <div className="space-y-2 mt-2 border-t border-slate-900 pt-3">
                  <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide flex justify-between items-center">
                    Variables checklist values
                    <button
                      type="button"
                      onClick={() => {
                        const vals = { ...ifValues };
                        const count = Object.keys(vals).length;
                        vals[`var_${count + 1}`] = '';
                        handleInputChange('values', vals);
                      }}
                      className="p-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
                    >
                      <Plus size={10} />
                    </button>
                  </label>
                  
                  <div className="space-y-2">
                    {Object.entries(ifValues).map(([vKey, vVal]) => (
                      <div key={vKey} className="flex gap-2 items-center bg-background/40 p-2 rounded border border-border/50">
                        <input
                          type="text"
                          value={vKey}
                          onChange={(e) => {
                            const newKey = e.target.value;
                            if (!newKey) return;
                            const vals = { ...ifValues };
                            const oldVal = vals[vKey];
                            delete vals[vKey];
                            vals[newKey] = oldVal;
                            handleInputChange('values', vals);
                          }}
                          className="w-[100px] rounded bg-background border border-border px-1.5 py-1 text-xs text-purple-300 focus:outline-none focus:border-indigo-500 font-mono"
                        />
                        <span className="text-xs text-muted-foreground">:</span>
                        <input
                          type="text"
                          value={typeof vVal === 'object' ? JSON.stringify(vVal) : (vVal as any)}
                          onChange={(e) => {
                            const vals = { ...ifValues };
                            vals[vKey] = e.target.value;
                            handleInputChange('values', vals);
                          }}
                          placeholder="path or static value"
                          className="flex-1 rounded bg-background border border-border px-1.5 py-1 text-sm text-foreground focus:outline-none focus:border-indigo-500 font-mono"
                        />
                        <button
                          type="button"
                          onClick={() => {
                            const vals = { ...ifValues };
                            delete vals[vKey];
                            handleInputChange('values', vals);
                          }}
                          className="text-muted-foreground hover:text-rose-400 p-0.5"
                        >
                          <Minus size={12} />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* SWITCH Gate Inputs */}
            {nodeKey === 'switch_node' && (
              <div className="space-y-3">
                <div className="space-y-1">
                  <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
                    Evaluation Value Reference
                  </label>
                  <input
                    type="text"
                    value={inputStr(inputs, 'value')}
                    onChange={(e) => handleInputChange('value', e.target.value)}
                    placeholder="e.g. channel_classifier.outputs.output.channel"
                    className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors font-mono"
                  />
                  {renderAutocompleteAssistant('value')}
                </div>
                
                <div className="space-y-1">
                  <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
                    Default Case Fallback
                  </label>
                  <input
                    type="text"
                    value={inputStr(inputs, 'default') || 'default'}
                    onChange={(e) => handleInputChange('default', e.target.value)}
                    className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors font-mono"
                  />
                </div>

                <div className="space-y-2 mt-2 border-t border-slate-900 pt-3">
                  <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide flex justify-between items-center">
                    Case Target Branches
                    <button
                      type="button"
                      onClick={() => {
                        const cases = [...switchCases];
                        cases.push(`case_${cases.length + 1}`);
                        handleInputChange('cases', cases);
                      }}
                      className="p-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
                    >
                      <Plus size={10} />
                    </button>
                  </label>
                  
                  <div className="space-y-2">
                    {switchCases.map((caseName, index) => (
                      <div key={index} className="flex gap-2 items-center">
                        <span className="text-xs text-muted-foreground font-mono w-4">#{index + 1}</span>
                        <input
                          type="text"
                          value={caseName}
                          onChange={(e) => {
                            const cases = [...switchCases];
                            cases[index] = e.target.value;
                            handleInputChange('cases', cases);
                          }}
                          className="flex-1 rounded bg-background border border-border px-2 py-1 text-sm text-white focus:outline-none focus:border-indigo-500 font-mono"
                        />
                        <button
                          type="button"
                          onClick={() => {
                            const cases = switchCases.filter((_, i) => i !== index);
                            handleInputChange('cases', cases);
                          }}
                          className="text-muted-foreground hover:text-rose-400 p-1"
                        >
                          <Minus size={12} />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
              </>
            )}
          </div>
        ) : (
          /* CONFIGURATION TAB */
          <div className="space-y-4">
            {/* LLM Model specifications */}
            {nodeKey.startsWith('llm.') && (
              <div className="space-y-3">
                <div className="space-y-1">
                  <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
                    Provider Model Selection
                  </label>
                  {nodeKey === 'llm.groq' ? (
                    <select
                      value={inputStr(config, 'model') || 'llama-3.3-70b-versatile'}
                      onChange={(e) => handleConfigChange('model', e.target.value)}
                      className="w-full rounded-lg bg-background border border-border px-2 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors"
                    >
                      <option value="llama-3.3-70b-versatile">Llama 3.3 70B (llama-3.3-70b-versatile)</option>
                      <option value="openai/gpt-oss-120b">GPT OSS 120B (openai/gpt-oss-120b)</option>
                      <option value="openai/gpt-oss-20b">GPT OSS 20B (openai/gpt-oss-20b)</option>
                      <option value="moonshotai/kimi-k2-instruct-0905">Kimi K2 Instruct (moonshotai/kimi-k2-instruct-0905)</option>
                      <option value="qwen/qwen3-32b">Qwen 3 32B (qwen/qwen3-32b)</option>
                    </select>
                  ) : (
                    <select
                      value={inputStr(config, 'model') || 'gemini-2.5-flash'}
                      onChange={(e) => handleConfigChange('model', e.target.value)}
                      className="w-full rounded-lg bg-background border border-border px-2 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors"
                    >
                      <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
                      <option value="gemini-2.5-pro">Gemini 2.5 Pro</option>
                      <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
                      <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                    </select>
                  )}
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
                    System Persona Instructions
                  </label>
                  <textarea
                    value={inputStr(config, 'system_prompt') || 'You are a helpful AI Assistant.'}
                    onChange={(e) => handleConfigChange('system_prompt', e.target.value)}
                    rows={3}
                    className="w-full rounded-lg bg-background border border-border p-2.5 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors font-sans leading-normal resize-y"
                  />
                </div>

                {config.temperature !== undefined && (
                  <div className="space-y-1">
                    <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide flex justify-between">
                      Model Temperature
                      <span className="text-amber-400">{Number(config.temperature ?? 1)}</span>
                    </label>
                    <input
                      type="range"
                      min={0}
                      max={2}
                      step={0.1}
                      value={Number(config.temperature ?? 1)}
                      onChange={(e) => handleConfigChange('temperature', parseFloat(e.target.value))}
                      className="w-full accent-indigo-500"
                    />
                  </div>
                )}

                <div className="space-y-1">
                  <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
                    Maximum Output Tokens limit
                  </label>
                  <input
                    type="number"
                    value={inputStr(config, 'max_tokens') || inputStr(config, 'max_output_tokens')}
                    onChange={(e) => {
                      const val = e.target.value ? parseInt(e.target.value, 10) : null;
                      if (nodeKey === 'llm.groq') {
                        handleConfigChange('max_tokens', val);
                      } else {
                        handleConfigChange('max_output_tokens', val);
                      }
                    }}
                    placeholder="Auto limit"
                    className="w-full rounded-lg bg-background border border-border px-3 py-2 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors"
                  />
                </div>

                <div className="space-y-1 mt-2">
                  <label className="text-xs font-bold text-muted-foreground uppercase tracking-wide flex justify-between items-center">
                    Structured Output response model schema
                    <span title="Defines fields extracted as outputs by the parser.">
                      <HelpCircle size={10} className="text-muted-foreground hover:text-foreground" />
                    </span>
                  </label>
                  <textarea
                    value={JSON.stringify(config.response_model || {}, null, 2)}
                    onChange={(e) => {
                      try {
                        const parsed = JSON.parse(e.target.value);
                        handleConfigChange('response_model', parsed);
                      } catch {}
                    }}
                    rows={6}
                    placeholder='{"output": {"advantages": "str"}}'
                    className="w-full rounded-lg bg-background border border-border p-2.5 text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-colors font-mono resize-y"
                  />
                </div>
              </div>
            )}

            {/* Standard static configurations fallback info */}
            {!nodeKey.startsWith('llm.') && (
              <div className="p-4 rounded-lg bg-background/60 border border-border flex gap-2 items-start text-xs text-muted-foreground">
                <AlertCircle size={14} className="text-indigo-400 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-foreground">Action Configurations</p>
                  <p className="mt-1 leading-normal">
                    This action is powered by credentials resolved automatically by FastAPI in real-time. No static configuration options are required for this node. Use the "Inputs" tab to structure its dynamically resolved parameters.
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Delete / Danger zone Footer */}
      <div className="p-3 border-t border-border bg-card/80 flex gap-2 justify-between items-center">
        <button
          onClick={() => {
            if (confirm('Are you sure you want to delete this node and all of its edge connections?')) {
              deleteNode(activeNode.id);
            }
          }}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 hover:text-rose-300 border border-rose-500/20 hover:border-rose-500/30 text-xs font-semibold transition-all w-full justify-center hover:scale-[1.01] active:scale-[0.99]"
        >
          <Trash2 size={13} />
          Delete Node
        </button>
      </div>
    </aside>
  );
};
export default PropertiesPanel;

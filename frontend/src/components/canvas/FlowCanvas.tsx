import React from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  Panel,
  BackgroundVariant
} from '@xyflow/react';
import type { ReactFlowInstance } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { useWorkflowStore } from '../../store/useWorkflowStore';
import WFlowCustomNode from './CustomNodes';
import { SaveWorkflowDialog } from './SaveWorkflowDialog';
import { Save, Trash2, HelpCircle } from 'lucide-react';

const nodeTypes = {
  wflowNode: WFlowCustomNode,
};

export const FlowCanvas: React.FC = () => {
  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    addNode,
    setActiveNodeId,
    setActiveEdgeId,
    resetWorkflow,
  } = useWorkflowStore();

  const [reactFlowInstance, setReactFlowInstance] = React.useState<ReactFlowInstance | null>(null);
  const [saveDialogOpen, setSaveDialogOpen] = React.useState(false);

  const onDragOver = React.useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = React.useCallback((event: React.DragEvent) => {
    event.preventDefault();

    if (!reactFlowInstance) return;

    const nodeKey = event.dataTransfer.getData('application/reactflow-nodekey');

    if (typeof nodeKey === 'undefined' || !nodeKey) return;

    const position = reactFlowInstance.screenToFlowPosition({
      x: event.clientX,
      y: event.clientY,
    });

    addNode(nodeKey, position);
  }, [reactFlowInstance, addNode]);

  return (
    <div className="flex-1 h-full relative" onDragOver={onDragOver} onDrop={onDrop}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onInit={setReactFlowInstance}
        nodeTypes={nodeTypes}
        onNodeClick={(_, node) => {
          setActiveEdgeId(null);
          setActiveNodeId(node.id);
        }}
        onEdgeClick={(_, edge) => {
          setActiveNodeId(null);
          setActiveEdgeId(edge.id);
        }}
        onPaneClick={() => {
          setActiveNodeId(null);
          setActiveEdgeId(null);
        }}
        fitView
        className="bg-background"
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color="rgba(255, 255, 255, 0.07)"
        />

        <Controls showInteractive={false} />

        <Panel position="top-right" className="!mt-3 flex flex-wrap gap-2 justify-end">
          <button
            type="button"
            onClick={() => setSaveDialogOpen(true)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-semibold shadow-lg hover:shadow-primary/25 hover:scale-[1.02] active:scale-[0.98] transition-all border border-primary/40"
          >
            <Save size={14} />
            Save
          </button>

          <button
            type="button"
            onClick={() => {
              if (confirm('Clear the entire canvas? All nodes and edges will be removed.')) {
                resetWorkflow(false);
              }
            }}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-card hover:bg-accent hover:text-destructive text-muted-foreground text-sm font-semibold shadow-lg transition-colors border border-border"
          >
            <Trash2 size={14} />
            Clear canvas
          </button>
        </Panel>

        <Panel position="bottom-center" className="bg-card/95 border border-border px-4 py-2.5 rounded-xl flex items-center gap-2 text-sm text-muted-foreground shadow-xl max-w-[min(100%,520px)] mb-2">
          <HelpCircle size={16} className="text-primary shrink-0" />
          <p className="leading-snug">
            <span className="font-semibold text-foreground">Quick tips:</span> Click a node for properties. Drag nodes from the catalog. Connect handles to link steps.
          </p>
        </Panel>
      </ReactFlow>

      <SaveWorkflowDialog open={saveDialogOpen} onClose={() => setSaveDialogOpen(false)} />
    </div>
  );
};

export default FlowCanvas;

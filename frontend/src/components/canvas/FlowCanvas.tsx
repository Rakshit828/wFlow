import React from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Panel,
  BackgroundVariant
} from '@xyflow/react';
import type { ReactFlowInstance } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { useWorkflowStore } from '../../store/useWorkflowStore';
import WFlowCustomNode from './CustomNodes';
import { Sparkles, Trash2, HelpCircle } from 'lucide-react';

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
    resetWorkflow
  } = useWorkflowStore();

  const [reactFlowInstance, setReactFlowInstance] = React.useState<ReactFlowInstance | null>(null);

  const onDragOver = React.useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = React.useCallback((event: React.DragEvent) => {
    event.preventDefault();

    if (!reactFlowInstance) return;

    const nodeKey = event.dataTransfer.getData('application/reactflow-nodekey');

    // check if the dropped element is valid
    if (typeof nodeKey === 'undefined' || !nodeKey) return;

    // Get drop position in canvas coordinates
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
        className="bg-slate-900/10"
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color="rgba(255, 255, 255, 0.07)"
        />

        <Controls showInteractive={false} className="text-white" />

        <MiniMap
          nodeStrokeColor={(n) => {
            if (n.data.type === 'LLM') return 'rgba(245, 158, 11, 0.7)';
            if (n.data.type === 'ACTION') return 'rgba(59, 130, 246, 0.7)';
            return 'rgba(168, 85, 247, 0.7)';
          }}
          nodeColor={() => 'rgba(15, 23, 42, 0.9)'}
          maskColor="rgba(0, 0, 0, 0.4)"
          className="rounded-lg overflow-hidden border border-slate-800"
        />

        {/* Canvas Floating Top Overlay Menu */}
        <Panel position="top-right" className="flex gap-2">
          <button
            onClick={() => {
              if (confirm('Load the sample Nepalese Essay multi-branch pipeline shown in requirements? This will reset the current canvas.')) {
                resetWorkflow(true);
              }
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg hover:shadow-indigo-500/20 hover:scale-102 active:scale-98 transition-all border border-indigo-500/40"
          >
            <Sparkles size={12} />
            Load Prompt Sample Pipeline
          </button>

          <button
            onClick={() => {
              if (confirm('Clear the entire canvas? All nodes and edges will be removed.')) {
                resetWorkflow(false);
              }
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 hover:text-rose-400 text-slate-400 text-xs font-semibold shadow-lg transition-colors border border-slate-800"
          >
            <Trash2 size={12} />
            Clear Canvas
          </button>
        </Panel>

        {/* Dynamic usage tips float */}
        <Panel position="bottom-center" className="bg-slate-950/90 border border-slate-800/80 px-4 py-2 rounded-xl flex items-center gap-2 text-[10.5px] text-slate-400 shadow-xl max-w-[450px]">
          <HelpCircle size={14} className="text-indigo-400 shrink-0" />
          <p className="leading-snug">
            <span className="font-semibold text-slate-300">Quick Tips:</span> Click a node to view properties. Drag from catalog to add nodes. Drag connections between handles to link.
          </p>
        </Panel>
      </ReactFlow>
    </div>
  );
};
export default FlowCanvas;

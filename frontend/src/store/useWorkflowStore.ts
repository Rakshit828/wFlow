import { create } from "zustand";
import { applyNodeChanges, applyEdgeChanges, addEdge } from "@xyflow/react";
import type {
    Node as RFNode,
    Edge as RFEdge,
    OnNodesChange,
    OnEdgesChange,
    OnConnect,
    XYPosition,
} from "@xyflow/react";
import type {
    Node as wNode,
    NodeFullResponse as wNodeFullResponse,
    Edge as wEdge,
    Workflow,
    NodesRegistryListItem,
} from "../types/workflow";
import type { WFlowNodeData, WFlowEdgeData } from "../types/flow";
import { asNodeData, asEdgeData } from "../types/flow";
import { createWorkflow, fetchWorkflowById } from "../api/workflows";

// Standard displacement constants for automatic node layout
const NODE_WIDTH = 250;
const NODE_HEIGHT = 100;
const HORIZONTAL_GAP = 120;
const VERTICAL_GAP = 120;

interface WorkflowState {
    // Metadata
    workflowId: string | null;
    workflowName: string;
    workflowDescription: string;
    workflowVisibility: "public" | "private";

    // React Flow elements
    nodes: RFNode<WFlowNodeData>[];
    edges: RFEdge<WFlowEdgeData>[];
    activeNodeId: string | null;
    activeEdgeId: string | null;
    isDirty: boolean;
    saveStatus: "idle" | "saving" | "saved" | "error";
    saveError: string | null;

    // Loading/Error states for routing
    isLoadingWorkflow: boolean;
    workflowLoadError: string | null;
    loadWorkflowById: (id: string) => Promise<void>;

    // Node Registry state for dynamic schemas
    nodeRegistry: Record<string, NodesRegistryListItem>;
    addRegistryItems: (items: NodesRegistryListItem[]) => void;

    // Basic Metadata setters
    setMetadata: (meta: {
        name?: string;
        description?: string;
        visibility?: "public" | "private";
    }) => void;

    // React Flow standard events
    setNodes: (nodes: RFNode<WFlowNodeData>[]) => void;
    setEdges: (edges: RFEdge<WFlowEdgeData>[]) => void;
    onNodesChange: OnNodesChange;
    onEdgesChange: OnEdgesChange;
    onConnect: OnConnect;

    // Flow Manipulation
    addNode: (key: string, position?: XYPosition) => void;
    updateNodeInputs: (nodeId: string, inputs: Record<string, any>) => void;
    updateNodeConfig: (nodeId: string, config: Record<string, any>) => void;
    deleteNode: (nodeId: string) => void;
    setActiveNodeId: (nodeId: string | null) => void;
    setActiveEdgeId: (edgeId: string | null) => void;
    updateEdgeProps: (edgeId: string, updates: Partial<WFlowEdgeData>) => void;
    deleteEdge: (edgeId: string) => void;
    saveWorkflow: () => Promise<boolean>;

    // Load and Export
    loadWorkflow: (workflow: Workflow) => void;
    resetWorkflow: (loadSample?: boolean) => void;
    getWorkflowJson: () => Workflow;

    // Reference and autocomplete helper
    getPrecedingNodes: (nodeId: string) => wNodeFullResponse[];
}

// Minimal topological sorting helper to arrange loaded nodes beautifully
function computeAutomaticLayout(
    wNodes: wNode[],
    wEdges: wEdge[],
): Record<string, XYPosition> {
    const positions: Record<string, XYPosition> = {};

    // Create adjacency lists
    const adj: Record<string, string[]> = {};
    const inDegree: Record<string, number> = {};

    wNodes.forEach((n) => {
        adj[n.name] = [];
        inDegree[n.name] = 0;
    });

    wEdges.forEach((e) => {
        if (adj[e.source] && adj[e.target] !== undefined) {
            adj[e.source].push(e.target);
            inDegree[e.target] = (inDegree[e.target] || 0) + 1;
        }
    });

    // Simple BFS / Kahn's algorithm for layering
    const queue: string[] = [];
    const layers: Record<string, number> = {};

    wNodes.forEach((n) => {
        if (inDegree[n.name] === 0) {
            queue.push(n.name);
            layers[n.name] = 0;
        }
    });

    while (queue.length > 0) {
        const curr = queue.shift()!;
        const currLayer = layers[curr];

        adj[curr].forEach((neighbor) => {
            inDegree[neighbor]--;
            layers[neighbor] = Math.max(layers[neighbor] || 0, currLayer + 1);
            if (inDegree[neighbor] === 0) {
                queue.push(neighbor);
            }
        });
    }

    // Group nodes by layers
    const layerGroups: Record<number, string[]> = {};
    wNodes.forEach((n) => {
        // If there was a cycle or disconnected, default to layer 0
        const l = layers[n.name] !== undefined ? layers[n.name] : 0;
        if (!layerGroups[l]) layerGroups[l] = [];
        layerGroups[l].push(n.name);
    });

    // Calculate coordinates based on layers
    Object.keys(layerGroups).forEach((layerStr) => {
        const l = parseInt(layerStr, 10);
        const nodesInLayer = layerGroups[l];
        nodesInLayer.forEach((nodeName, idx) => {
            positions[nodeName] = {
                x: 100 + l * (NODE_WIDTH + HORIZONTAL_GAP),
                y:
                    100 +
                    idx * (NODE_HEIGHT + VERTICAL_GAP) -
                    ((nodesInLayer.length - 1) * (NODE_HEIGHT + VERTICAL_GAP)) /
                        2,
            };
        });
    });

    return positions;
}

function getInputsAndConfigDefaults(
    inputModel: Record<string, any> | null | undefined,
) {
    const defaultInputs: Record<string, any> = {};
    const defaultConfig: Record<string, any> = {};

    if (!inputModel) {
        return { defaultInputs, defaultConfig };
    }

    // 1. Inputs defaults (excluding 'config')
    if (inputModel.properties) {
        Object.entries(inputModel.properties).forEach(
            ([pKey, pVal]: [string, any]) => {
                if (pKey === "config") return;
                if (pVal.default !== undefined) {
                    defaultInputs[pKey] = pVal.default;
                } else {
                    if (pVal.type === "array") {
                        defaultInputs[pKey] = [];
                    } else if (pVal.type === "object") {
                        defaultInputs[pKey] = {};
                    } else if (pVal.type === "boolean") {
                        defaultInputs[pKey] = false;
                    } else if (
                        pVal.type === "integer" ||
                        pVal.type === "number"
                    ) {
                        defaultInputs[pKey] = 0;
                    } else {
                        defaultInputs[pKey] = "";
                    }
                }
            },
        );
    }

    // 2. Config defaults
    const rawConfigSchema =
        inputModel.config ?? inputModel.properties?.config ?? null;
    let configSchema = rawConfigSchema;
    if (rawConfigSchema && rawConfigSchema.$ref && inputModel) {
        const ref = rawConfigSchema.$ref;
        if (typeof ref === "string" && ref.startsWith("#/")) {
            const path = ref.slice(2).split("/");
            let current: any = inputModel;
            for (const step of path) {
                if (current && typeof current === "object" && step in current) {
                    current = current[step];
                }
            }
            if (current && typeof current === "object") {
                configSchema = current;
            }
        }
    }

    if (configSchema && configSchema.properties) {
        Object.entries(configSchema.properties).forEach(
            ([pKey, pVal]: [string, any]) => {
                if (pVal.default !== undefined) {
                    defaultConfig[pKey] = pVal.default;
                } else {
                    if (pVal.type === "array") {
                        defaultConfig[pKey] = [];
                    } else if (pVal.type === "object") {
                        defaultConfig[pKey] = {};
                    } else if (pVal.type === "boolean") {
                        defaultConfig[pKey] = false;
                    } else if (
                        pVal.type === "integer" ||
                        pVal.type === "number"
                    ) {
                        defaultConfig[pKey] = 0;
                    } else {
                        defaultConfig[pKey] = "";
                    }
                }
            },
        );
    }

    return { defaultInputs, defaultConfig };
}

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
    workflowId: null,
    workflowName: "My AI Workflow",
    workflowDescription: "An automated pipeline built on wFlow.",
    workflowVisibility: "private",

    nodes: [],
    edges: [],
    activeNodeId: null,
    activeEdgeId: null,
    isDirty: false,
    saveStatus: "idle",
    saveError: null,

    isLoadingWorkflow: false,
    workflowLoadError: null,

    nodeRegistry: {},
    addRegistryItems: (items) =>
        set((state) => {
            const newRegistry = { ...state.nodeRegistry };
            items.forEach((item) => {
                newRegistry[item.fn_key] = item;
            });
            return { nodeRegistry: newRegistry };
        }),

    setMetadata: (meta) =>
        set(() => {
            const updates: Partial<WorkflowState> = {};
            if (meta.name !== undefined) updates.workflowName = meta.name;
            if (meta.description !== undefined)
                updates.workflowDescription = meta.description;
            if (meta.visibility !== undefined)
                updates.workflowVisibility = meta.visibility;
            return { ...updates, isDirty: true };
        }),

    setNodes: (nodes) => set({ nodes }),
    setEdges: (edges) => set({ edges }),

    onNodesChange: (changes) =>
        set((state) => ({
            nodes: applyNodeChanges(
                changes,
                state.nodes,
            ) as RFNode<WFlowNodeData>[],
            isDirty: true,
        })),

    onEdgesChange: (changes) =>
        set((state) => ({
            edges: applyEdgeChanges(
                changes,
                state.edges,
            ) as RFEdge<WFlowEdgeData>[],
            isDirty: true,
        })),

    onConnect: (connection) =>
        set((state) => {
            const sourceNode = state.nodes.find(
                (n) => n.id === connection.source,
            );
            const sourceKey = sourceNode ? asNodeData(sourceNode.data).key : "";

            const existingFromSource = state.edges.filter(
                (e) => e.source === connection.source,
            );
            const existingToTarget = state.edges.filter(
                (e) => e.target === connection.target,
            );

            let edgeType: wEdge["type"] = "linear";
            let decision: boolean | null = null;
            let switchCase: string | null = null;

            if (sourceKey === "if_node") {
                edgeType = "if";
                const hasTrue = existingFromSource.some(
                    (e) =>
                        asEdgeData(e.data).type === "if" &&
                        asEdgeData(e.data).decision === true,
                );
                decision = !hasTrue;
            } else if (sourceKey === "switch_node") {
                edgeType = "switch";
                const inputs = sourceNode
                    ? asNodeData(sourceNode.data).inputs
                    : {};
                const cases = (inputs.cases as string[]) || ["default"];
                const usedCases = existingFromSource
                    .map((e) => asEdgeData(e.data).case)
                    .filter(Boolean);
                switchCase =
                    cases.find((c) => !usedCases.includes(c)) ??
                    cases[0] ??
                    "default";
            } else if (existingFromSource.length > 0) {
                edgeType = "parallel";
            } else if (existingToTarget.length > 0) {
                edgeType = "merge";
            }

            const edgeData: WFlowEdgeData = {
                type: edgeType,
                decision,
                case: switchCase,
            };
            const label =
                edgeType === "if"
                    ? decision
                        ? "True"
                        : "False"
                    : edgeType === "switch"
                      ? (switchCase ?? undefined)
                      : edgeType === "parallel"
                        ? "parallel"
                        : edgeType === "merge"
                          ? "merge"
                          : undefined;

            const newEdge: RFEdge<WFlowEdgeData> = {
                id: `edge-${connection.source}-${connection.target}-${Date.now()}`,
                source: connection.source!,
                target: connection.target!,
                sourceHandle: connection.sourceHandle,
                targetHandle: connection.targetHandle,
                animated: true,
                data: edgeData,
                style: { stroke: "hsl(var(--primary))" },
                label,
            };

            return {
                edges: addEdge(newEdge, state.edges),
                isDirty: true,
                activeEdgeId: newEdge.id,
                activeNodeId: null,
            };
        }),

    addNode: (key, position) =>
        set((state) => {
            const registrySpec = state.nodeRegistry[key];

            // Generate unique name e.g. "groq_llm_node1"
            const keyClean = key.replace(".", "_");
            const existingCount = state.nodes.filter(
                (n) => (n.data.key as string) === key,
            ).length;
            const name = `${keyClean}_node${existingCount + 1}`;

            let label = "";
            let type: any = "ACTION";
            let defaultInputs: Record<string, any> = {};
            let defaultConfig: Record<string, any> = {};
            let inputModel: any = null;
            let outputModel: any = null;

            if (registrySpec) {
                label = registrySpec.name;
                type = registrySpec.type;
                inputModel = registrySpec.input_model;
                outputModel = registrySpec.output_model;

                const defaults = getInputsAndConfigDefaults(inputModel);
                defaultInputs = defaults.defaultInputs;
                defaultConfig = defaults.defaultConfig;
            }

            const nodeData: WFlowNodeData = {
                label,
                key,
                name,
                type,
                inputs: defaultInputs,
                config: defaultConfig,
                outputs: {},
                input_model: inputModel,
                output_model: outputModel,
            };

            const newRFNode: RFNode<WFlowNodeData> = {
                id: name,
                type: "wflowNode",
                position: position || {
                    x: 250 + Math.random() * 50,
                    y: 150 + Math.random() * 50,
                },
                data: nodeData,
            };

            return {
                nodes: [...state.nodes, newRFNode],
                activeNodeId: name,
                isDirty: true,
            };
        }),

    updateNodeInputs: (nodeId, inputs) =>
        set((state) => {
            const nodes = state.nodes.map((n) => {
                if (n.id === nodeId) {
                    const data = asNodeData(n.data);
                    return {
                        ...n,
                        data: {
                            ...data,
                            inputs: { ...data.inputs, ...inputs },
                        } satisfies WFlowNodeData,
                    };
                }
                return n;
            });
            return { nodes, isDirty: true };
        }),

    updateNodeConfig: (nodeId, config) =>
        set((state) => {
            const nodes = state.nodes.map((n) => {
                if (n.id === nodeId) {
                    const data = asNodeData(n.data);
                    return {
                        ...n,
                        data: {
                            ...data,
                            config: { ...data.config, ...config },
                        } satisfies WFlowNodeData,
                    };
                }
                return n;
            });
            return { nodes, isDirty: true };
        }),

    deleteNode: (nodeId) =>
        set((state) => {
            // Delete node and any associated edges
            const nodes = state.nodes.filter((n) => n.id !== nodeId);
            const edges = state.edges.filter(
                (e) => e.source !== nodeId && e.target !== nodeId,
            );
            return {
                nodes,
                edges,
                activeNodeId:
                    state.activeNodeId === nodeId ? null : state.activeNodeId,
                isDirty: true,
            };
        }),

    setActiveNodeId: (nodeId) =>
        set({ activeNodeId: nodeId, activeEdgeId: null }),

    setActiveEdgeId: (edgeId) =>
        set({ activeEdgeId: edgeId, activeNodeId: null }),

    updateEdgeProps: (edgeId, updates) =>
        set((state) => {
            const edges = state.edges.map((e) => {
                if (e.id === edgeId) {
                    const prev = asEdgeData(e.data);
                    const data: WFlowEdgeData = { ...prev, ...updates };
                    let label: string | undefined;
                    if (data.type === "if") {
                        label = data.decision ? "True" : "False";
                    } else if (data.type === "switch") {
                        label = data.case ?? undefined;
                    } else if (data.type === "parallel") {
                        label = "parallel";
                    } else if (data.type === "merge") {
                        label = "merge";
                    }

                    return { ...e, data, label };
                }
                return e;
            });
            return { edges, isDirty: true };
        }),

    deleteEdge: (edgeId) =>
        set((state) => ({
            edges: state.edges.filter((e) => e.id !== edgeId),
            isDirty: true,
        })),

    loadWorkflow: (workflow) =>
        set(() => {
            // Convert Beanie/FastAPI workflow nodes and edges to React Flow
            // If stashed node configuration position is found, use it; otherwise compute layout!
            const nodePositions: Record<string, XYPosition> = {};
            workflow.nodes.forEach((n) => {
                if (n.config && n.config._position) {
                    nodePositions[n.name] = n.config._position;
                }
            });

            // Check if we need to compute full layout
            const needsLayout =
                Object.keys(nodePositions).length < workflow.nodes.length;
            const computedPositions = needsLayout
                ? computeAutomaticLayout(workflow.nodes, workflow.edges)
                : nodePositions;

            const rfNodes: RFNode<WFlowNodeData>[] = workflow.nodes.map((n) => {
                const position = computedPositions[n.name] || {
                    x: 100,
                    y: 100,
                };

                // Filter out position coordinates from config payload for visualization
                const configClean = { ...n.config };
                delete configClean._position;

                const spec = get().nodeRegistry[n.key];
                const inputModel = n.input_model || spec?.input_model;
                const outputModel =
                    n.output_model !== undefined
                        ? n.output_model
                        : spec?.output_model;

                // Retrieve frontend-constructed defaults from the schema/spec
                const defaults = getInputsAndConfigDefaults(inputModel);

                const data: WFlowNodeData = {
                    label: spec ? spec.name : n.name,
                    key: n.key,
                    name: n.name,
                    type: n.type,
                    // Merge frontend-constructed defaults with backend-saved inputs/config
                    inputs: {
                        ...defaults.defaultInputs,
                        ...(n.inputs || {}),
                    } as Record<string, unknown>,
                    config: {
                        ...defaults.defaultConfig,
                        ...(configClean || {}),
                    } as Record<string, unknown>,
                    outputs: (n.outputs || {}) as Record<string, unknown>,
                    input_model: inputModel,
                    output_model: outputModel,
                };

                return {
                    id: n.name,
                    type: "wflowNode",
                    position,
                    data,
                };
            });

            const rfEdges: RFEdge<WFlowEdgeData>[] = workflow.edges.map(
                (e, index) => {
                    const label =
                        e.type === "if"
                            ? e.decision
                                ? "True"
                                : "False"
                            : e.type === "switch"
                              ? e.case
                              : undefined;

                    return {
                        id: `edge-${e.source}-${e.target}-${index}`,
                        source: e.source,
                        target: e.target,
                        animated: true,
                        data: {
                            type: e.type,
                            decision: e.decision ?? null,
                            case: e.case ?? null,
                        } satisfies WFlowEdgeData,
                        style: { stroke: "hsl(var(--primary))" },
                        label,
                    };
                },
            );

            return {
                workflowId: workflow.workflow_id || null,
                workflowName: workflow.name,
                workflowDescription: workflow.description || "",
                workflowVisibility: workflow.visibility || "private",
                nodes: rfNodes,
                edges: rfEdges,
                activeNodeId: null,
                activeEdgeId: null,
                isDirty: false,
                saveStatus: "idle",
                saveError: null,
            };
        }),

    loadWorkflowById: async (id: string) => {
        const { isLoadingWorkflow, workflowId, isDirty } = get();

        // Skip if already loading this workflow (double-mount guard)
        if (isLoadingWorkflow) return;

        // Skip if we already have this workflow loaded and no unsaved changes
        if (workflowId === id && !isDirty) return;

        set({ isLoadingWorkflow: true, workflowLoadError: null });
        try {
            const workflow = (await fetchWorkflowById(id)).data;
            get().loadWorkflow(workflow);
            set({ isLoadingWorkflow: false });
        } catch (err) {
            const message =
                err instanceof Error ? err.message : "Failed to load workflow";
            set({ workflowLoadError: message, isLoadingWorkflow: false });
        }
    },

    saveWorkflow: async () => {
        const { getWorkflowJson } = get();
        set({ saveStatus: "saving", saveError: null });
        try {
            const payload = getWorkflowJson();
            const res = await createWorkflow({
                name: payload.name,
                description: payload.description,
                nodes: payload.nodes,
                edges: payload.edges,
                visibility: payload.visibility,
            });
            set({
                workflowId: res.data.workflow_id,
                saveStatus: "saved",
                isDirty: false,
            });
            return true;
        } catch (err) {
            const message = err instanceof Error ? err.message : "Save failed";
            set({ saveStatus: "error", saveError: message });
            return false;
        }
    },

    resetWorkflow: () =>
        set(() => {
            return {
                workflowId: null,
                workflowName: "New AI Pipeline",
                workflowDescription:
                    "Configure your custom automation workflow here.",
                workflowVisibility: "private",
                nodes: [],
                edges: [],
                activeNodeId: null,
                activeEdgeId: null,
                isDirty: false,
                saveStatus: "idle",
                saveError: null,
            };
        }),

    getWorkflowJson: () => {
        const {
            workflowId,
            workflowName,
            workflowDescription,
            workflowVisibility,
            nodes,
            edges,
        } = get();

        // Map RFNodes back to clean Beanie models
        const parsedNodes: wNode[] = nodes.map((n) => {
            const data = asNodeData(n.data);

            // For runtime payload we strip internal UI positioning and
            // do not include input_model/output_model fields. Outputs
            // are left empty for the backend to populate at runtime.
            const configClean = { ...data.config };

            return {
                key: data.key,
                name: n.id,
                type: data.type,
                inputs: data.inputs as Record<string, unknown>,
                config: configClean,
                outputs: {},
            } as wNode;
        });

        const parsedEdges: wEdge[] = edges.map((e) => {
            const edgeData = asEdgeData(e.data);
            const type = edgeData.type || "linear";
            const edge: wEdge = {
                source: e.source,
                target: e.target,
                type,
            };

            if (type === "if") {
                edge.decision = edgeData.decision ?? true;
            } else if (type === "switch") {
                edge.case = edgeData.case || "default";
            }

            return edge;
        });

        const workflowJson: Workflow = {
            name: workflowName,
            description: workflowDescription,
            nodes: parsedNodes,
            edges: parsedEdges,
            visibility: workflowVisibility,
            // runtime context is empty by default; runtime may populate it
            // with variables when executing the workflow
            context: {},
        } as Workflow;

        if (workflowId) {
            workflowJson.workflow_id = workflowId;
        }

        return workflowJson;
    },

    getPrecedingNodes: (nodeId) => {
        const { nodes, edges } = get();

        const reverseAdj: Record<string, string[]> = {};
        nodes.forEach((n) => {
            reverseAdj[n.id] = [];
        });
        edges.forEach((e) => {
            if (!reverseAdj[e.target]) reverseAdj[e.target] = [];
            reverseAdj[e.target].push(e.source);
        });

        const ancestors = new Set<string>();
        const queue = [...(reverseAdj[nodeId] || [])];
        const visited = new Set<string>();

        while (queue.length > 0) {
            const curr = queue.shift()!;
            if (visited.has(curr)) continue;
            visited.add(curr);
            ancestors.add(curr);
            queue.push(...(reverseAdj[curr] || []));
        }

        return nodes
            .filter((n) => ancestors.has(n.id))
            .map((n) => {
                const data = asNodeData(n.data);
                return {
                    key: data.key,
                    name: n.id,
                    type: data.type,
                    inputs: data.inputs as Record<string, unknown>,
                    config: data.config as Record<string, unknown>,
                    outputs: data.outputs as Record<string, unknown>,
                    input_model: data.input_model,
                    output_model: data.output_model,
                } as wNodeFullResponse;
            });
    },
}));

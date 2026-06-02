# Building the Frontend for AI Workflow Automation Tool (wFlow)

This plan details the design and implementation of a modular, scalable, and highly aesthetic React frontend for **wFlow**, an AI Workflow Automation platform. 

The frontend will enable users to create, configure, visualize, and save complex workflows containing LLMs, Google Cloud integrations (Gmail, Sheets, Drive), and Control Flow nodes (`if_node`, `switch_node`).

---

## User Review Required

> [!NOTE]
> We will initialize a separate React 19 + TypeScript + Vite project under the `frontend` directory using `create-vite`.
> We will implement a custom properties sidebar panel to configure node `inputs` and `config` instead of cramming configuration forms inside React Flow nodes, which preserves canvas space and visual cleanliness.

> [!IMPORTANT]
> Since the backend API for executing the workflow is not fully ready (it's stubbed in the backend routes), we will focus entirely on:
> 1. Building, tracking, and editing the Workflow JSON structure (`nodes` and `edges`).
> 2. Integrating ready endpoints: Fetching workflows (`GET /api/workflows`), Searching (`GET /api/workflows/search`), Creating/saving workflows (`POST /api/workflows/create`), Starring workflows (`POST /api/workflows/star/{id}`), and Google Login/OAuth Scope flows.
> 3. Designing a rich, premium user experience with responsive dark-mode support, micro-animations, and dynamic canvas resizing.

---

## Proposed Changes

We will create a clean and scalable React project structure inside the `frontend` folder:

```
frontend/
├── index.html
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── index.css
│   ├── types/
│   │   └── workflow.ts          # Core type definitions matching backend models
│   ├── store/
│   │   └── useWorkflowStore.ts  # Zustand store managing nodes, edges, validation, & JSON tracking
│   ├── components/
│   │   ├── ui/                  # Custom beautifully styled components (buttons, input, dial, cards)
│   │   ├── canvas/
│   │   │   ├── FlowCanvas.tsx   # React Flow engine canvas
│   │   │   ├── SidebarCatalog.tsx # Draggable node catalog panel
│   │   │   ├── PropertiesPanel.tsx # Sliding panel for node configuration (inputs & config)
│   │   │   ├── JsonPreview.tsx  # Dynamic side-by-side YAML/JSON live tracker
│   │   │   └── CustomNodes.tsx  # Sleek custom visual designs for LLM, ACTION, and CONTROL_FLOW
│   │   ├── dashboard/
│   │   │   ├── WorkflowGrid.tsx # Paginated grid for saved workflows
│   │   │   ├── CreateDialog.tsx # Modal to create new workflow with metadata
│   │   │   └── Integrations.tsx # Google/services status and connect links
│   │   └── layout/
│   │       ├── Header.tsx       # Navbar with save button, user profile, theme toggle
│   │       └── Sidebar.tsx      # App navigation (Dashboard vs. Canvas)
│   └── lib/
│       ├── api.ts               # Axios client for connecting to FastAPI endpoints
│       └── utils.ts             # Tailwind class merging & string utilities
```

### Component Details

#### [NEW] [workflow.ts](file:///d:/Projects/wFlow/frontend/src/types/workflow.ts)
Contains TypeScript types mirroring beanie/pydantic definitions in the backend:
- `Node` (name, key, type, inputs, config, outputs)
- `Edge` (source, target, type, decision, case)
- `Workflow` (name, description, nodes, edges, visibility, context)
- Available `NodeKeys`: `llm.groq`, `llm.google`, `drive.upload`, `gmail.send`, `gmail.create_draft_email`, etc.

#### [NEW] [useWorkflowStore.ts](file:///d:/Projects/wFlow/frontend/src/store/useWorkflowStore.ts)
A centralized Zustand store managing:
- React Flow's `nodes` and `edges` list.
- Selection of active node for the properties panel.
- Dynamic conversion of React Flow data back into the raw `Workflow` JSON required by Beanie schema.
- Reference autocompletion engine: analyzes previous node outputs and helps users write strings like `groq_llm_node1.outputs.output.outlines` inside inputs fields.
- Local validation of paths and reference structures before saving.

#### [NEW] [CustomNodes.tsx](file:///d:/Projects/wFlow/frontend/src/components/canvas/CustomNodes.tsx)
Sleek React Flow custom nodes with vibrant colors:
- **LLM Nodes** (`llm.groq`, `llm.google`): Cool neon orange/violet accents, model indicator badges, status of configuration.
- **Action Nodes** (`gmail.*`, `sheets.*`, `drive.*`): Google blue/green styling, icon indicators, active permissions checklist.
- **Control Flow Nodes** (`if_node`, `switch_node`): Neon yellow accents, custom branch labels, conditional syntax previews.
- Custom edge styling that matches decision types:
  - If `type === "if"`, visual indicator showing `True` or `False` branch.
  - If `type === "switch"`, indicator showing the matching `case` text on the connection.

#### [NEW] [PropertiesPanel.tsx](file:///d:/Projects/wFlow/frontend/src/components/canvas/PropertiesPanel.tsx)
A slider interface that opens when a node is selected. It features:
- **Inputs Editor**: Renders inputs dynamically based on node key.
- **Config Editor**: Custom options (e.g. system prompt, model choice, max tokens for LLMs).
- **Reference Autocomplete**: Input fields parse text like `node.outputs` and offer an interactive dropdown suggestion list of valid preceding node output properties.

#### [NEW] [JsonPreview.tsx](file:///d:/Projects/wFlow/frontend/src/components/canvas/JsonPreview.tsx)
Collapsible panel on the right showing the exact JSON payload being built in real time. It highlights dynamic fields and errors, enhancing transparency for developers.

#### [NEW] [WorkflowGrid.tsx](file:///d:/Projects/wFlow/frontend/src/components/dashboard/WorkflowGrid.tsx)
A beautiful dashboard showing:
- A grid of all saved workflows with a star counter, visibility status, search filtering, and pagination.
- Creation card to launch the canvas editor.

---

## Verification Plan

### Automated & Manual Verification
1. **Node Manipulation**: Verify that dragging, dropping, renaming, deleting, and editing nodes updates the live JSON correctly.
2. **Edge Connections**: Connect nodes and ensure edges correctly reflect types:
   - Connect from standard node → standard node (`linear`).
   - Connect from standard nodes → multiple nodes in parallel (`parallel`).
   - Connect from multiple nodes → single node (`merge`).
   - Connect from `if_node` → nodes (`if` with true/false options).
   - Connect from `switch_node` → nodes (`switch` with customized case entries).
3. **Properties Configuration**: Ensure changes in the properties sidebar (changing prompts, LLM model choice, temperature) are dynamically updated in the Zustand store.
4. **Mocked and Active API Integration**:
   - Check that all workflows load, pagination works, and searches successfully fetch from `/api/workflows/`.
   - Verify that clicking "Save Workflow" serializes the exact format expected by Beanie and hits `/api/workflows/create`.
   - Validate that Google Authentication redirects and callbacks are connected correctly.

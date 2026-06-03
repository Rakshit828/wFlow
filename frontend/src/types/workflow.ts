export type NodesType = 'ACTION' | 'LLM' | 'TRANSFORM' | 'API' | 'DATA_SOURCE' | 'CONTROL_FLOW' | 'TRIGGER';
export type EdgesType = 'linear' | 'if' | 'switch' | 'parallel' | 'merge';

export interface Node {
  key: string;
  name: string;
  type: NodesType;
  inputs: Record<string, any>;
  config: Record<string, any>;
  outputs: Record<string, any>;
  input_model?: Record<string, any>;
  output_model?: Record<string, any> | null;
}

export interface Edge {
  source: string;
  target: string;
  type: EdgesType;
  decision?: boolean | null;
  case?: string | null;
}

export interface Workflow {
  workflow_id?: string;
  name: string;
  description: string;
  nodes: Node[];
  edges: Edge[];
  visibility: 'public' | 'private';
  stars?: number;
  created_by?: string;
}

export interface WorkflowListItem {
  workflow_id: string;
  name: string;
  description: string;
  visibility: 'public' | 'private';
  stars: number;
  created_by: string;
}

export interface NodesRegistryListItem {
  name: string;
  description: string;
  type: NodesType;
  service: string;
  valid_permissions?: string[] | null;
  fn_key: string;
  input_model: Record<string, any>;
  output_model: Record<string, any> | null;
}

export interface PaginatedNodesResponse {
  data: NodesRegistryListItem[];
  pagination: PaginationMeta;
}

export interface PaginationMeta {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface PaginatedWorkflowsResponse {
  data: WorkflowListItem[];
  pagination: PaginationMeta;
}

export interface CreateWorkflowResponse {
  workflow_id: string;
  name: string;
  description: string;
  nodes: Node[];
  edges: Edge[];
  visibility: 'public' | 'private';
  stars: number;
  created_by: string;
}
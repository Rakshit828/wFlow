import { apiFetch } from '../lib/api';
import type { Workflow } from '../types/workflow';

export interface WorkflowListItem {
  workflow_id: string;
  name: string;
  description: string;
  visibility: 'public' | 'private';
  stars: number;
  created_by: string;
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

export interface WorkflowResponse {
  workflow_id: string;
  name: string;
  description: string;
  nodes: Workflow['nodes'];
  edges: Workflow['edges'];
  visibility: 'public' | 'private';
  stars?: number;
  created_by: string;
}

export async function fetchWorkflows(
  page: number = 1,
  pageSize: number = 10
): Promise<PaginatedWorkflowsResponse> {
  return apiFetch(`/api/workflows/?page=${page}&page_size=${pageSize}`);
}

export async function searchWorkflows(
  query: string,
  page: number = 1,
  pageSize: number = 10
): Promise<PaginatedWorkflowsResponse> {
  return apiFetch(
    `/api/workflows/search?query=${encodeURIComponent(query)}&page=${page}&page_size=${pageSize}`
  );
}

export async function createWorkflow(
  workflow: Omit<Workflow, 'workflow_id' | 'stars' | 'created_by'>
): Promise<WorkflowResponse> {
  return apiFetch('/api/workflows/create', {
    method: 'POST',
    json: workflow,
  });
}

export async function starWorkflow(
  workflowId: string
): Promise<{ workflow_id: string; stars: number }> {
  return apiFetch(`/api/workflows/star/${workflowId}`, { method: 'POST' });
}

import { apiFetch } from "../lib/api";
import type {
    Workflow,
    PaginatedWorkflowsResponse,
    CreateWorkflowResponse,
    ApiResponse,
    StarWorkflowResponse
} from "../types/workflow";
import type { PaginatedNodesResponse } from "../types/workflow";

export async function fetchWorkflows(
    page: number = 1,
    pageSize: number = 10,
    explore: boolean = false,
): Promise<ApiResponse<PaginatedWorkflowsResponse>> {
    return apiFetch(
        `/api/workflows/?page=${page}&page_size=${pageSize}&explore=${explore}`,
    );
}

export async function searchWorkflows(
    query: string,
    page: number = 1,
    pageSize: number = 10,
    explore: boolean = false,
): Promise<ApiResponse<PaginatedWorkflowsResponse>> {
    return apiFetch(
        `/api/workflows/search?query=${encodeURIComponent(query)}&page=${page}&page_size=${pageSize}&explore=${explore}`,
    );
}

export async function fetchWorkflowById(workflowId: string): Promise<ApiResponse<Workflow>> {
    return apiFetch(`/api/workflows/${workflowId}`);
}

export async function createWorkflow(
    workflow: Omit<Workflow, "workflow_id" | "stars" | "created_by">,
): Promise<ApiResponse<CreateWorkflowResponse>> {
    return apiFetch("/api/workflows/create", {
        method: "POST",
        json: workflow,
    });
}

export async function starWorkflow(
    workflowId: string,
): Promise<ApiResponse<StarWorkflowResponse>> {
    return apiFetch(`/api/workflows/star/${workflowId}`, { method: "POST" });
}

export async function fetchRegisteredNodes(
    page: number = 1,
    pageSize: number = 10,
): Promise<ApiResponse<PaginatedNodesResponse>> {
    return apiFetch(
        `/api/workflows/all-nodes?page=${page}&page_size=${pageSize}`,
    );
}

export async function searchRegisteredNodes(
    nodeType: string,
    service?: string,
    page: number = 1,
    pageSize: number = 10,
): Promise<ApiResponse<PaginatedNodesResponse>> {
    const serviceParam = service
        ? `&service=${encodeURIComponent(service)}`
        : "";
    return apiFetch(
        `/api/workflows/nodes/${nodeType}?page=${page}&page_size=${pageSize}${serviceParam}`,
    );
}

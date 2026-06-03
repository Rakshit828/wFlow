import type { NodesType, EdgesType } from './workflow';

/** React Flow node payload stored in Zustand / @xyflow/react */
export interface WFlowNodeData extends Record<string, unknown> {
  label: string;
  key: string;
  name: string;
  type: NodesType;
  inputs: Record<string, unknown>;
  config: Record<string, unknown>;
  outputs: Record<string, unknown>;
  input_model?: Record<string, any>;
  output_model?: Record<string, any> | null;
}

export interface WFlowEdgeData extends Record<string, unknown> {
  type: EdgesType;
  decision?: boolean | null;
  case?: string | null;
}

export function asNodeData(data: Record<string, unknown> | undefined): WFlowNodeData {
  return data as unknown as WFlowNodeData;
}

export function asEdgeData(data: Record<string, unknown> | undefined): WFlowEdgeData {
  return (data ?? { type: 'linear' }) as unknown as WFlowEdgeData;
}

export function inputStr(inputs: Record<string, unknown>, key: string): string {
  const v = inputs[key];
  if (v == null) return '';
  if (typeof v === 'string') return v;
  if (typeof v === 'number' || typeof v === 'boolean') return String(v);
  return JSON.stringify(v);
}

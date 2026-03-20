/* Forge types — autonomous coding agent */

export type ForgeStatus = 'idle' | 'streaming' | 'done' | 'error';

export type ForgeEventType = 'log' | 'done' | 'error' | 'heartbeat';

export type ForgeCategory =
  | 'info'
  | 'thinking'
  | 'tool'
  | 'tool_result'
  | 'git'
  | 'status'
  | 'warning'
  | 'error';

export interface ForgeEvent {
  type: ForgeEventType;
  message?: string;
  category?: ForgeCategory;
  status?: string;
  pr_url?: string | null;
}

export interface ForgeMessage {
  id: string;
  type: ForgeEventType;
  category: ForgeCategory;
  message: string;
  timestamp: number;
  prUrl?: string | null;
}

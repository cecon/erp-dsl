/* Cappy types — autonomous coding agent */

export type CappyStatus = 'idle' | 'streaming' | 'done' | 'error';

export type CappyEventType = 'log' | 'done' | 'error' | 'heartbeat';

export type CappyCategory =
  | 'info'
  | 'thinking'
  | 'tool'
  | 'tool_result'
  | 'git'
  | 'status'
  | 'warning'
  | 'error';

export interface CappyEvent {
  type: CappyEventType;
  message?: string;
  category?: CappyCategory;
  status?: string;
  pr_url?: string | null;
}

export interface CappyMessage {
  id: string;
  type: CappyEventType;
  category: CappyCategory;
  message: string;
  timestamp: number;
  prUrl?: string | null;
}

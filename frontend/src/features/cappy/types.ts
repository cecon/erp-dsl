/* Cappy types — autonomous coding agent */

export type CappyStatus = 'idle' | 'streaming' | 'done' | 'error';

export type CappyEventType = 'log' | 'done' | 'error' | 'heartbeat';

export interface CappyEvent {
  type: CappyEventType;
  message?: string;
  status?: string;
  pr_url?: string | null;
}

export interface CappyMessage {
  id: string;
  type: CappyEventType;
  message: string;
  timestamp: number;
  prUrl?: string | null;
}

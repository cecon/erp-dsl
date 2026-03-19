/* Forge types — autonomous coding agent */

export type ForgeStatus = 'idle' | 'streaming' | 'done' | 'error';

export type ForgeEventType = 'log' | 'done' | 'error' | 'heartbeat';

export interface ForgeEvent {
  type: ForgeEventType;
  message?: string;
  status?: string;
  pr_url?: string | null;
}

export interface ForgeMessage {
  id: string;
  type: ForgeEventType;
  message: string;
  timestamp: number;
  prUrl?: string | null;
}

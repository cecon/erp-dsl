/**
 * CappyFab — Floating action button for the Cappy autonomous coding agent.
 * Displays separately from Otto FAB to keep them distinct.
 */

import { useCappyContext } from './CappyProvider';
import './cappy.css';

export function CappyFab() {
  const { toggle, status } = useCappyContext();

  return (
    <button
      className={`cappy-fab ${status === 'streaming' ? 'cappy-fab-pulse' : ''}`}
      onClick={toggle}
      aria-label="Open Cappy coding agent"
      type="button"
      title="Cappy — Agente de Programação Autônomo"
    >
      <span className="cappy-fab-icon">⚒️</span>
      <span className="cappy-fab-label">Cappy</span>
    </button>
  );
}

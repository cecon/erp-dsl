/**
 * ForgeFab — Floating action button for the Forge autonomous coding agent.
 * Displays separately from Otto FAB to keep them distinct.
 */

import { useForgeContext } from './ForgeProvider';
import './forge.css';

export function ForgeFab() {
  const { toggle, status } = useForgeContext();

  return (
    <button
      className={`forge-fab ${status === 'streaming' ? 'forge-fab-pulse' : ''}`}
      onClick={toggle}
      aria-label="Open Forge coding agent"
      type="button"
      title="Forge — Agente de Programação Autônomo"
    >
      <span className="forge-fab-icon">⚒️</span>
      <span className="forge-fab-label">Forge</span>
    </button>
  );
}

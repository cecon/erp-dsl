/**
 * OttoFab — floating action button for the Otto chat.
 */

import { useOttoContext } from './OttoProvider';

export function OttoFab() {
  const { toggle, status } = useOttoContext();

  return (
    <button
      className={`otto-fab ${status === 'streaming' ? 'otto-fab-pulse' : ''}`}
      onClick={toggle}
      aria-label="Open Otto chat"
      type="button"
    >
      <span className="otto-fab-icon">🐾</span>
      <span className="otto-fab-label">Otto</span>
    </button>
  );
}

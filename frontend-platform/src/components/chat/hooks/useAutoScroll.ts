import { useCallback, useEffect, useRef } from "react";

/**
 * Hook for smart auto-scrolling behavior.
 * Scrolls to bottom when new content arrives, but pauses if user has
 * manually scrolled up. Resumes auto-scroll when user scrolls back to bottom.
 */
export function useAutoScroll(deps: unknown[]) {
  const viewportRef = useRef<HTMLDivElement>(null);
  const isUserScrolled = useRef(false);
  const lastScrollHeight = useRef(0);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = "smooth") => {
    const viewport = viewportRef.current;
    if (!viewport) return;
    viewport.scrollTo({
      top: viewport.scrollHeight,
      behavior,
    });
  }, []);

  const handleScroll = useCallback(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;

    const { scrollTop, scrollHeight, clientHeight } = viewport;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
    // Consider "at bottom" if within 80px
    isUserScrolled.current = distanceFromBottom > 80;
  }, []);

  // Auto-scroll when dependencies change (e.g., messages update)
  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport) return;

    // If scroll height changed and user hasn't scrolled up, auto-scroll
    if (
      !isUserScrolled.current &&
      viewport.scrollHeight !== lastScrollHeight.current
    ) {
      scrollToBottom();
    }
    lastScrollHeight.current = viewport.scrollHeight;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { viewportRef, handleScroll, scrollToBottom, isUserScrolled };
}

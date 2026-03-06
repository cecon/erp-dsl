import type { ComponentType } from 'react';

/* eslint-disable @typescript-eslint/no-explicit-any */

export interface FieldComponentProps {
  label?: string;
  placeholder?: string;
  value?: any;
  onChange?: (value: any) => void;
  options?: { value: string; label: string }[];
  [key: string]: any;
}

/**
 * Creates a component registry from a map of DSL type strings to components.
 *
 * Each component is self-contained — all formatting, masks, and
 * locale defaults live INSIDE the component, not here.
 */
export function createRegistry(
  components: Record<string, ComponentType<any>>,
): Record<string, ComponentType<any>> {
  return { ...components };
}

/**
 * Resolves a component from a registry by type string.
 * Returns null when the type is not registered.
 */
export function getComponent(
  registry: Record<string, ComponentType<any>>,
  type: string,
): ComponentType<any> | null {
  return registry[type] ?? null;
}

/**
 * Returns the list of all registered component names in a registry.
 */
export function listComponents(
  registry: Record<string, ComponentType<any>>,
): string[] {
  return Object.keys(registry);
}

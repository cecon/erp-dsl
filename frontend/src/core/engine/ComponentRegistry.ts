import type { ComponentType } from 'react';
import {
  TextField,
  NumberField,
  MoneyField,
  DateField,
  DateTimeField,
  SelectField,
  CheckboxField,
  TextAreaField,
  ColorSwatchPicker,
  ThemeSwitch,
  SegmentedField,
} from '@erp-dsl/form-ui';
import { ProductEnrichModal } from '../../features/agent/ProductEnrichModal';
import { WorkflowStepEditorField } from '../../features/workflows';

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * ERP-specific component registry.
 *
 * Combines shared form components from @erp-dsl/form-ui
 * with project-specific components (agent modals, workflow editors).
 *
 * Passed to EngineProvider so the engine can resolve field types.
 */
export const componentRegistry: Record<string, ComponentType<any>> = {
  text: TextField,
  number: NumberField,
  money: MoneyField,
  date: DateField,
  datetime: DateTimeField,
  select: SelectField,
  checkbox: CheckboxField,
  textarea: TextAreaField,
  color_swatch_picker: ColorSwatchPicker,
  theme_switch: ThemeSwitch,
  segmented: SegmentedField,
  hidden: () => null,

  /* ── Agent modals ─────────────────────────────────────── */
  'agent:product-enrich': ProductEnrichModal,

  /* ── Workflow editor ──────────────────────────────────── */
  'workflow_step_editor': WorkflowStepEditorField,
};

export function getComponent(type: string): ComponentType<any> | null {
  return componentRegistry[type] ?? null;
}

/** Returns the list of all registered component names. */
export function listComponents(): string[] {
  return Object.keys(componentRegistry);
}

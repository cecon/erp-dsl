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
} from '../../components/form';
import { ProductEnrichModal } from '../../features/agent/ProductEnrichModal';
import { WorkflowStepEditorField } from '../../features/workflows';

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
 * Registry mapping DSL type strings to encapsulated field components.
 *
 * Each component is self-contained — all formatting, masks, and
 * locale defaults live INSIDE the component, not here.
 *
 * To add a new field type:
 * 1. Create a component in src/components/form/
 * 2. Export it from src/components/form/index.ts
 * 3. Register it here with a DSL type key
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

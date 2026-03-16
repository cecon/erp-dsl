/**
 * Barrel export for all DSL form field components.
 *
 * Each component is self-contained with its own formatting,
 * masks, and defaults — the DSL engine never needs to know
 * implementation details.
 *
 * @module @erp-dsl/form-ui
 */

// ── UX Container ──────────────────────────────────────────────────────────
export { FieldWrapper } from './FieldWrapper';
export type { FieldWrapperProps } from './FieldWrapper';

// ── Field Components ──────────────────────────────────────────────────────
export { TextField } from './TextField';
export type { TextFieldProps } from './TextField';

export { NumberField } from './NumberField';
export type { NumberFieldProps } from './NumberField';

export { MoneyField } from './MoneyField';
export type { MoneyFieldProps } from './MoneyField';

export { DateField } from './DateField';
export type { DateFieldProps } from './DateField';

export { DateTimeField } from './DateTimeField';
export type { DateTimeFieldProps } from './DateTimeField';

export { SelectField } from './SelectField';
export type { SelectFieldProps } from './SelectField';

export { CheckboxField } from './CheckboxField';
export type { CheckboxFieldProps } from './CheckboxField';

export { TextAreaField } from './TextAreaField';
export type { TextAreaFieldProps } from './TextAreaField';

export { SegmentedField } from './SegmentedField';
export type { SegmentedFieldProps } from './SegmentedField';

export { SwitchField } from './SwitchField';
export type { SwitchFieldProps } from './SwitchField';

export { ColorSwatchPicker } from './ColorSwatchPicker';
export { ThemeSwitch } from './ThemeSwitch';

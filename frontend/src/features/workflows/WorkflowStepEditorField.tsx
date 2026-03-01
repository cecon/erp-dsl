/**
 * WorkflowStepEditorField — composite field registered in ComponentRegistry.
 *
 * Combines WorkflowStepEditor (step list with ▲▼) and WorkflowTester
 * (inline sandbox SSE tester) into a single form field component.
 *
 * The workflow ID is extracted from the URL search params (?id=...).
 */

import { WorkflowStepEditor, type WorkflowStepData } from './WorkflowStepEditor';
import { WorkflowTester } from './WorkflowTester';

/* eslint-disable @typescript-eslint/no-explicit-any */

interface WorkflowStepEditorFieldProps {
  value?: WorkflowStepData[];
  onChange?: (steps: WorkflowStepData[]) => void;
  label?: string;
}

export function WorkflowStepEditorField({
  value,
  onChange,
  label,
}: WorkflowStepEditorFieldProps) {
  // Extract workflow ID from URL for the tester
  const urlParams = new URLSearchParams(window.location.search);
  const workflowId = urlParams.get('id');

  return (
    <>
      <WorkflowStepEditor value={value} onChange={onChange} label={label} />
      <WorkflowTester workflowId={workflowId} />
    </>
  );
}

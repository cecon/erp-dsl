/**
 * useSkills — fetches available skills from GET /api/otto/components.
 *
 * Returns the skills list with name, description, and params_schema
 * for use in the WorkflowStepEditor dropdown and dynamic params form.
 */

import { useQuery } from '@tanstack/react-query';
import api from '../../services/api';

export interface SkillInfo {
  name: string;
  description: string;
  params_schema?: {
    type?: string;
    properties?: Record<
      string,
      { type: string; description?: string; enum?: string[] }
    >;
    required?: string[];
  };
}

interface ComponentsResponse {
  components: string[];
  skills: SkillInfo[];
}

export function useSkills() {
  const { data, isLoading, error } = useQuery<ComponentsResponse>({
    queryKey: ['otto-components'],
    queryFn: () => api.get('/otto/components').then((r) => r.data),
    staleTime: 60_000,
  });

  return {
    skills: data?.skills ?? [],
    isLoading,
    error,
  };
}

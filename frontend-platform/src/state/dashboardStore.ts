import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Project {
  id: string;
  name: string;
  slug: string;
  status: string;
  created_at: string;
}

export interface AppItem {
  id: string;
  project_id: string;
  name: string;
  slug: string;
  status: string;
  llm_provider: string | null;
  llm_model: string | null;
  created_at: string;
}

export interface DatabaseInfo {
  id: string;
  app_id: string;
  db_name: string;
  db_host: string;
  db_port: number;
  db_user: string;
  db_password: string;
  status: string;
}

interface DashboardState {
  projects: Project[];
  activeProjectId: string | null;
  activeAppId: string | null;

  setProjects: (projects: Project[]) => void;
  setActiveProject: (id: string | null) => void;
  setActiveApp: (id: string | null) => void;
  addProject: (project: Project) => void;
}

export const useDashboardStore = create<DashboardState>()(
  persist(
    (set) => ({
      projects: [],
      activeProjectId: null,
      activeAppId: null,

      setProjects: (projects) => set({ projects }),
      setActiveProject: (id) => set({ activeProjectId: id, activeAppId: null }),
      setActiveApp: (id) => set({ activeAppId: id }),
      addProject: (project) =>
        set((state) => ({ projects: [...state.projects, project] })),
    }),
    { name: 'erp-dsl-dashboard' }
  )
);

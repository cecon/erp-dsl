import {
  Badge,
  Group,
  Loader,
  Tabs,
  Title,
  UnstyledButton,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconArrowLeft,
  IconBuildingStore,
  IconDatabase,
  IconRocket,
  IconSettings,
} from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../../services/api';
import type { AppItem, DatabaseInfo, Project } from '../../state/dashboardStore';
import { CreateAppModal } from './CreateAppModal';
import { AppsTab } from './tabs/AppsTab';
import { CompanyTab } from './tabs/CompanyTab';
import { DatabaseTab } from './tabs/DatabaseTab';
import { GeneralTab } from './tabs/GeneralTab';

interface CompanyData {
  type: string;
  razao_social: string;
  nome_fantasia: string;
  cnpj_cpf: string;
}

export function ProjectSettings() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const [project, setProject] = useState<Project | null>(null);
  const [apps, setApps] = useState<AppItem[]>([]);
  const [companyData, setCompanyData] = useState<CompanyData | null>(null);
  const [loading, setLoading] = useState(true);

  const [dbInfo, setDbInfo] = useState<DatabaseInfo | null>(null);
  const [selectedAppId, setSelectedAppId] = useState<string | null>(null);
  const [dbLoading, setDbLoading] = useState(false);
  const [appModal, setAppModal] = useState(false);

  useEffect(() => {
    if (!projectId) return;
    Promise.all([
      api.get(`/api/accounts/projects/${projectId}`),
      api.get(`/api/accounts/projects/${projectId}/apps`),
      api.get(`/api/accounts/projects/${projectId}/company`).catch(() => ({
        data: null,
      })),
    ])
      .then(([pRes, aRes, cRes]) => {
        setProject(pRes.data);
        setApps(aRes.data);
        if (cRes.data) {
          setCompanyData(cRes.data);
        }
      })
      .catch(() => {
        notifications.show({
          title: 'Erro',
          message: 'Não foi possível carregar os dados do projeto',
          color: 'red',
        });
      })
      .finally(() => setLoading(false));
  }, [projectId]);

  const loadDbInfo = async (appId: string) => {
    setSelectedAppId(appId);
    setDbLoading(true);
    try {
      const { data } = await api.get(`/api/accounts/apps/${appId}/database`);
      setDbInfo(data);
    } catch {
      setDbInfo(null);
      notifications.show({
        title: 'Erro',
        message: 'Não foi possível carregar os dados do banco',
        color: 'red',
      });
    } finally {
      setDbLoading(false);
    }
  };

  if (loading) {
    return (
      <Group justify="center" py={80}>
        <Loader />
      </Group>
    );
  }

  return (
    <div className="dash-layout">
      <main className="dash-main" style={{ maxWidth: 960, margin: '0 auto' }}>
        <Group mb="lg" gap="xs">
          <UnstyledButton onClick={() => navigate('/')}>
            <IconArrowLeft size={20} />
          </UnstyledButton>
          <Title order={3} fw={600}>
            {project?.name || 'Projeto'}
          </Title>
          <Badge variant="light" color="teal" size="sm">
            {project?.status}
          </Badge>
        </Group>

        <Tabs defaultValue="general" variant="outline">
          <Tabs.List mb="lg">
            <Tabs.Tab value="general" leftSection={<IconSettings size={16} />}>
              Geral
            </Tabs.Tab>
            <Tabs.Tab
              value="company"
              leftSection={<IconBuildingStore size={16} />}
            >
              Empresa
            </Tabs.Tab>
            <Tabs.Tab value="apps" leftSection={<IconRocket size={16} />}>
              Apps
            </Tabs.Tab>
            <Tabs.Tab value="database" leftSection={<IconDatabase size={16} />}>
              Database
            </Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="general">
            <GeneralTab project={project} />
          </Tabs.Panel>

          <Tabs.Panel value="company">
            <CompanyTab
              projectId={projectId!}
              initialData={companyData}
            />
          </Tabs.Panel>

          <Tabs.Panel value="apps">
            <AppsTab
              apps={apps}
              onOpenCreateModal={() => setAppModal(true)}
              onSelectApp={loadDbInfo}
            />
          </Tabs.Panel>

          <Tabs.Panel value="database">
            <DatabaseTab
              dbInfo={dbInfo}
              selectedAppId={selectedAppId}
              loading={dbLoading}
            />
          </Tabs.Panel>
        </Tabs>
      </main>

      <CreateAppModal
        projectId={projectId!}
        opened={appModal}
        onClose={() => setAppModal(false)}
        onCreated={(app) => setApps((prev) => [...prev, app])}
      />
    </div>
  );
}

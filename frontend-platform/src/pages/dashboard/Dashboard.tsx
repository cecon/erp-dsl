import {
  ActionIcon,
  Badge,
  Button,
  Card,
  Group,
  Loader,
  Modal,
  Stack,
  Text,
  TextInput,
  Title,
  UnstyledButton,
} from '@mantine/core';
import {
  IconApps,
  IconDatabase,
  IconFolder,
  IconLogout,
  IconPlus,
  IconSettings,
} from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { useAuthStore } from '../../state/authStore';
import type { Project } from '../../state/dashboardStore';
import { useDashboardStore } from '../../state/dashboardStore';

export function Dashboard() {
  const navigate = useNavigate();
  const logout = useAuthStore((s) => s.logout);
  const projects = useDashboardStore((s) => s.projects);
  const setProjects = useDashboardStore((s) => s.setProjects);
  const addProject = useDashboardStore((s) => s.addProject);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    api
      .get('/api/accounts/projects')
      .then(({ data }) => setProjects(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [setProjects]);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    setCreating(true);
    try {
      const { data } = await api.post('/api/accounts/projects', {
        name: newName,
      });
      addProject(data);
      setModalOpen(false);
      setNewName('');
    } catch {
      // handled
    } finally {
      setCreating(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="dash-layout">
      {/* Sidebar */}
      <aside className="dash-sidebar">
        <div className="dash-sidebar__header">
          <div className="dash-sidebar__logo">
            <span className="dash-sidebar__logo-icon">A</span>
            <span className="dash-sidebar__logo-text">AutoSystem</span>
          </div>
        </div>

        <div className="dash-sidebar__section-title">
          <Text size="xs" fw={600} c="dimmed" tt="uppercase">
            Projetos
          </Text>
          <ActionIcon
            variant="subtle"
            size="sm"
            onClick={() => setModalOpen(true)}
          >
            <IconPlus size={14} />
          </ActionIcon>
        </div>

        <nav className="dash-sidebar__nav">
          {projects.map((p: Project) => (
            <UnstyledButton
              key={p.id}
              className="dash-sidebar__item"
              onClick={() => navigate(`/projects/${p.id}`)}
            >
              <IconFolder size={16} />
              <Text size="sm" truncate>
                {p.name}
              </Text>
            </UnstyledButton>
          ))}
          {projects.length === 0 && !loading && (
            <Text size="xs" c="dimmed" ta="center" py="md">
              Nenhum projeto ainda
            </Text>
          )}
        </nav>

        <div className="dash-sidebar__footer">
          <UnstyledButton
            className="dash-sidebar__item"
            onClick={handleLogout}
          >
            <IconLogout size={16} />
            <Text size="sm">Sair</Text>
          </UnstyledButton>
        </div>
      </aside>

      {/* Main content */}
      <main className="dash-main">
        <div className="dash-main__header">
          <Title order={3} fw={600}>
            Seus Projetos
          </Title>
          <Button
            leftSection={<IconPlus size={16} />}
            onClick={() => setModalOpen(true)}
          >
            Novo Projeto
          </Button>
        </div>

        {loading ? (
          <Group justify="center" py={80}>
            <Loader />
          </Group>
        ) : projects.length === 0 ? (
          <Card className="dash-empty-card" padding="xl" radius="lg">
            <Stack align="center" gap="md">
              <IconFolder size={48} stroke={1} color="var(--mantine-color-dimmed)" />
              <Title order={4} c="dimmed">
                Nenhum projeto criado
              </Title>
              <Text c="dimmed" size="sm" ta="center">
                Crie seu primeiro projeto para começar a configurar
                seu ambiente.
              </Text>
              <Button onClick={() => setModalOpen(true)}>
                Criar Projeto
              </Button>
            </Stack>
          </Card>
        ) : (
          <div className="dash-grid">
            {projects.map((p: Project) => (
              <Card
                key={p.id}
                className="dash-project-card"
                padding="lg"
                radius="md"
                onClick={() => navigate(`/projects/${p.id}`)}
                style={{ cursor: 'pointer' }}
              >
                <Group justify="space-between" mb="sm">
                  <Group gap="xs">
                    <IconFolder size={20} />
                    <Text fw={600}>{p.name}</Text>
                  </Group>
                  <Badge
                    variant="light"
                    color={p.status === 'active' ? 'teal' : 'gray'}
                    size="sm"
                  >
                    {p.status}
                  </Badge>
                </Group>
                <Group gap="lg">
                  <Group gap={4}>
                    <IconApps size={14} color="var(--mantine-color-dimmed)" />
                    <Text size="xs" c="dimmed">
                      Apps
                    </Text>
                  </Group>
                  <Group gap={4}>
                    <IconDatabase size={14} color="var(--mantine-color-dimmed)" />
                    <Text size="xs" c="dimmed">
                      Database
                    </Text>
                  </Group>
                  <Group gap={4}>
                    <IconSettings size={14} color="var(--mantine-color-dimmed)" />
                    <Text size="xs" c="dimmed">
                      Config
                    </Text>
                  </Group>
                </Group>
              </Card>
            ))}
          </div>
        )}
      </main>

      {/* Create project modal */}
      <Modal
        opened={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Novo Projeto"
        centered
      >
        <Stack gap="md">
          <TextInput
            label="Nome do Projeto"
            placeholder="Meu Projeto"
            value={newName}
            onChange={(e) => setNewName(e.currentTarget.value)}
            data-autofocus
          />
          <Button
            fullWidth
            loading={creating}
            onClick={handleCreate}
            disabled={!newName.trim()}
          >
            Criar
          </Button>
        </Stack>
      </Modal>
    </div>
  );
}

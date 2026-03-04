import {
  Anchor,
  Button,
  PasswordInput,
  Stack,
  Text,
  TextInput,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuthStore } from '../state/authStore';

export function Login() {
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);
  const [loading, setLoading] = useState(false);

  const form = useForm({
    initialValues: { email: '', password: '' },
    validate: {
      email: (v: string) => (v.length < 1 ? 'E-mail é obrigatório' : null),
      password: (v: string) => (v.length < 1 ? 'Senha é obrigatória' : null),
    },
  });

  const handleSubmit = async (values: { email: string; password: string }) => {
    setLoading(true);
    try {
      const { data } = await api.post('/api/accounts/login', values);
      login(data);
      navigate('/');
    } catch {
      notifications.show({
        title: 'Falha na autenticação',
        message: 'E-mail ou senha inválidos',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <div className="auth-logo">
          <div className="auth-logo-icon">A</div>
          <div className="auth-logo-text">AutoSystem</div>
        </div>
        <div className="auth-subtitle">Acesse sua conta</div>

        <form onSubmit={form.onSubmit(handleSubmit)}>
          <Stack gap="md">
            <TextInput
              label="E-mail"
              placeholder="seu@email.com"
              size="md"
              {...form.getInputProps('email')}
            />
            <PasswordInput
              label="Senha"
              placeholder="Sua senha"
              size="md"
              {...form.getInputProps('password')}
            />
            <Button type="submit" fullWidth size="md" loading={loading} mt="sm">
              Entrar
            </Button>
          </Stack>
        </form>

        <div className="auth-footer">
          <Text size="sm" c="dimmed">
            Não tem uma conta?{' '}
            <Anchor component="button" onClick={() => navigate('/signup')}>
              Criar conta
            </Anchor>
          </Text>
        </div>
      </div>
    </div>
  );
}

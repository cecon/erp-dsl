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

export function SignUp() {
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);
  const [loading, setLoading] = useState(false);

  const form = useForm({
    initialValues: { email: '', name: '', password: '', confirm: '' },
    validate: {
      email: (v: string) =>
        /^\S+@\S+\.\S+$/.test(v) ? null : 'E-mail inválido',
      name: (v: string) => (v.length < 2 ? 'Nome é obrigatório' : null),
      password: (v: string) =>
        v.length < 6 ? 'Mínimo 6 caracteres' : null,
      confirm: (v: string, values: any) =>
        v !== values.password ? 'Senhas não coincidem' : null,
    },
  });

  const handleSubmit = async (values: {
    email: string;
    name: string;
    password: string;
  }) => {
    setLoading(true);
    try {
      const { data } = await api.post('/api/accounts/signup', {
        email: values.email,
        name: values.name,
        password: values.password,
      });
      login(data);
      navigate('/');
    } catch (err: any) {
      notifications.show({
        title: 'Erro ao criar conta',
        message: err.response?.data?.detail || 'Tente novamente',
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
        <div className="auth-subtitle">Crie sua conta</div>

        <form onSubmit={form.onSubmit(handleSubmit)}>
          <Stack gap="md">
            <TextInput
              label="Nome"
              placeholder="Seu nome completo"
              size="md"
              {...form.getInputProps('name')}
            />
            <TextInput
              label="E-mail"
              placeholder="seu@email.com"
              size="md"
              {...form.getInputProps('email')}
            />
            <PasswordInput
              label="Senha"
              placeholder="Mínimo 6 caracteres"
              size="md"
              {...form.getInputProps('password')}
            />
            <PasswordInput
              label="Confirmar Senha"
              placeholder="Repita a senha"
              size="md"
              {...form.getInputProps('confirm')}
            />
            <Button
              type="submit"
              fullWidth
              size="md"
              loading={loading}
              mt="sm"
            >
              Criar Conta
            </Button>
          </Stack>
        </form>

        <div className="auth-footer">
          <Text size="sm" c="dimmed">
            Já tem uma conta?{' '}
            <Anchor component="button" onClick={() => navigate('/login')}>
              Entrar
            </Anchor>
          </Text>
        </div>
      </div>
    </div>
  );
}

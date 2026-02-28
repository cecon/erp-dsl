import {
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
    initialValues: { username: '', password: '' },
    validate: {
      username: (v: string) => (v.length < 1 ? 'Username is required' : null),
      password: (v: string) => (v.length < 1 ? 'Password is required' : null),
    },
  });

  const handleSubmit = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      const { data } = await api.post('/auth/login', values);
      login(data);
      navigate('/');
    } catch {
      notifications.show({
        title: 'Authentication failed',
        message: 'Invalid username or password',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-wrapper">
      <div className="login-card">
        <div className="login-logo">
          <div className="login-logo-icon">A</div>
          <div className="login-logo-text">AutoSystem</div>
        </div>
        <div className="login-subtitle">
          Enterprise Management Platform
        </div>

        <form onSubmit={form.onSubmit(handleSubmit)}>
          <Stack gap="md">
            <TextInput
              label="Username"
              placeholder="Enter your username"
              size="md"
              {...form.getInputProps('username')}
            />
            <PasswordInput
              label="Password"
              placeholder="Enter your password"
              size="md"
              {...form.getInputProps('password')}
            />
            <Button
              type="submit"
              fullWidth
              size="md"
              loading={loading}
              mt="sm"
            >
              Sign In
            </Button>
          </Stack>
        </form>

        <div className="login-footer">
          <Text size="xs" c="dimmed">
            Default: admin / admin
          </Text>
        </div>
      </div>
    </div>
  );
}

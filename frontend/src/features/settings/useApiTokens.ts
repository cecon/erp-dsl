import { useState, useEffect, useCallback } from 'react';
import api from '../../services/api';

interface ApiToken {
  id: string;
  name: string;
  is_active: boolean;
  created_at: string;
  last_used_at: string | null;
}

interface CreatedToken extends ApiToken {
  token: string;
}

export function useApiTokens() {
  const [tokens, setTokens] = useState<ApiToken[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTokens = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get<ApiToken[]>('/settings/tokens');
      setTokens(res.data);
    } catch {
      setError('Erro ao carregar tokens');
    } finally {
      setLoading(false);
    }
  }, []);

  const createToken = useCallback(async (name: string): Promise<CreatedToken> => {
    const res = await api.post<CreatedToken>('/settings/tokens', { name });
    await fetchTokens();
    return res.data;
  }, [fetchTokens]);

  const revokeToken = useCallback(async (id: string) => {
    await api.delete(`/settings/tokens/${id}`);
    setTokens((prev) => prev.filter((t) => t.id !== id));
  }, []);

  useEffect(() => { fetchTokens(); }, [fetchTokens]);

  return { tokens, loading, error, createToken, revokeToken, refetch: fetchTokens };
}

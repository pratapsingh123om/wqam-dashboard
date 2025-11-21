import { api, setAuthToken } from './api';

export async function login(username: string, password: string): Promise<{ access_token: string, token_type: string, role: string }> {
  const response = await api.post('/auth/login', { username, password });
  const data = response.data;
  if (data.access_token) {
    setAuthToken(data.access_token);
  }
  return data;
}

export async function register(username: string, password: string, role: string): Promise<any> {
  const response = await api.post('/auth/register', { username, password, role });
  return response.data;
}

export async function getMe(): Promise<any> {
    const response = await api.get('/auth/me');
    return response.data;
}
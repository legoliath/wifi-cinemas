import api from './api';
import type { TokenResponse } from '../types';

export async function loginWithEmail(email: string, password: string): Promise<TokenResponse> {
  const { data } = await api.post('/auth/login', { email, password });
  return { accessToken: data.access_token, tokenType: data.token_type, expiresIn: data.expires_in, userId: data.user_id, role: data.role };
}

export async function registerWithInviteCode(email: string, name: string, password: string, inviteCode?: string, lang = 'fr'): Promise<TokenResponse> {
  const { data } = await api.post('/auth/register', { email, name, password, invite_code: inviteCode, lang });
  return { accessToken: data.access_token, tokenType: data.token_type, expiresIn: data.expires_in, userId: data.user_id, role: data.role };
}

export async function verifyInviteCode(code: string) {
  const { data } = await api.post('/auth/verify-invite-code', { code });
  return { valid: data.valid, shootId: data.shoot_id };
}

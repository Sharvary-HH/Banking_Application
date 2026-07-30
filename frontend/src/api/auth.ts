import { apiClient } from './client'
import type {
  Enable2FaRequest,
  Enable2FaResponse,
  LoginRequest,
  LoginResponse,
  RefreshRequest,
  RegisterRequest,
  RegisterResponse,
  Setup2FaResponse,
  TokenResponse,
  User,
  Verify2FaRequest,
} from './types'

export const authApi = {
  async register(payload: RegisterRequest): Promise<RegisterResponse> {
    const { data } = await apiClient.post<RegisterResponse>('/auth/register', payload)
    return data
  },

  async login(payload: LoginRequest): Promise<LoginResponse> {
    const { data } = await apiClient.post<LoginResponse>('/auth/login', payload)
    return data
  },

  async verify2fa(payload: Verify2FaRequest): Promise<TokenResponse> {
    const { data } = await apiClient.post<TokenResponse>('/auth/login/verify-2fa', payload)
    return data
  },

  async refresh(payload: RefreshRequest): Promise<TokenResponse> {
    const { data } = await apiClient.post<TokenResponse>('/auth/refresh', payload)
    return data
  },

  async setup2fa(): Promise<Setup2FaResponse> {
    const { data } = await apiClient.post<Setup2FaResponse>('/auth/2fa/setup')
    return data
  },

  async enable2fa(payload: Enable2FaRequest): Promise<Enable2FaResponse> {
    const { data } = await apiClient.post<Enable2FaResponse>('/auth/2fa/enable', payload)
    return data
  },

  async me(): Promise<User> {
    const { data } = await apiClient.get<User>('/auth/me')
    return data
  },
}

export function isTwoFaRequired(res: LoginResponse): res is Extract<LoginResponse, { two_fa_required: true }> {
  return (res as { two_fa_required?: boolean }).two_fa_required === true
}

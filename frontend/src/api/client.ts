import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { tokenStorage } from './tokenStorage'
import type { TokenResponse } from './types'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

export const apiClient = axios.create({
  baseURL,
})

// A separate, un-intercepted instance used only for the refresh call itself,
// so it never recurses into the response interceptor below.
const refreshClient = axios.create({ baseURL })

apiClient.interceptors.request.use((config) => {
  const token = tokenStorage.getAccessToken()
  if (token) {
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

interface RetriableRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean
}

let refreshPromise: Promise<string | null> | null = null

function redirectToLogin(): void {
  tokenStorage.clear()
  if (window.location.pathname !== '/login') {
    window.location.href = '/login'
  }
}

async function performRefresh(): Promise<string | null> {
  const refreshToken = tokenStorage.getRefreshToken()
  if (!refreshToken) {
    return null
  }
  try {
    const { data } = await refreshClient.post<TokenResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    })
    tokenStorage.setTokens(data.access_token, data.refresh_token)
    return data.access_token
  } catch {
    return null
  }
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetriableRequestConfig | undefined

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/refresh')
    ) {
      originalRequest._retry = true

      if (!refreshPromise) {
        refreshPromise = performRefresh().finally(() => {
          refreshPromise = null
        })
      }

      const newAccessToken = await refreshPromise

      if (newAccessToken) {
        originalRequest.headers = originalRequest.headers ?? {}
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        return apiClient(originalRequest)
      }

      redirectToLogin()
    }

    return Promise.reject(error)
  },
)

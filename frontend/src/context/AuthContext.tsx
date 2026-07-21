import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { authApi } from '../api/auth'
import { tokenStorage } from '../api/tokenStorage'
import type { TokenResponse, User } from '../api/types'

interface AuthContextValue {
  user: User | null
  accessToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (tokens: TokenResponse) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [accessToken, setAccessToken] = useState<string | null>(tokenStorage.getAccessToken())
  const [isLoading, setIsLoading] = useState<boolean>(true)

  const loadUser = useCallback(async () => {
    const token = tokenStorage.getAccessToken()
    if (!token) {
      setUser(null)
      setAccessToken(null)
      setIsLoading(false)
      return
    }
    try {
      const me = await authApi.me()
      setUser(me)
      setAccessToken(token)
    } catch {
      tokenStorage.clear()
      setUser(null)
      setAccessToken(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadUser()
  }, [loadUser])

  const login = useCallback(async (tokens: TokenResponse) => {
    tokenStorage.setTokens(tokens.access_token, tokens.refresh_token)
    setAccessToken(tokens.access_token)
    const me = await authApi.me()
    setUser(me)
  }, [])

  const logout = useCallback(() => {
    tokenStorage.clear()
    setUser(null)
    setAccessToken(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      accessToken,
      isAuthenticated: Boolean(user && accessToken),
      isLoading,
      login,
      logout,
      refreshUser: loadUser,
    }),
    [user, accessToken, isLoading, login, logout, loadUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return ctx
}

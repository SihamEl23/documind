/** Contexte d'authentification : qui est connecté, connexion, déconnexion. */
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api, tokens } from './api'
import type { User } from './types'

interface AuthState {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (fullName: string, email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  // Si un token est déjà enregistré, on charge le profil au démarrage
  const [loading, setLoading] = useState(Boolean(tokens.access))

  useEffect(() => {
    if (!tokens.access) return
    api<User>('/api/auth/me')
      .then(setUser)
      .catch(() => tokens.clear())
      .finally(() => setLoading(false))
  }, [])

  async function login(email: string, password: string) {
    const t = await api<{ access_token: string; refresh_token: string }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    tokens.save(t.access_token, t.refresh_token)
    setUser(await api<User>('/api/auth/me'))
  }

  async function register(fullName: string, email: string, password: string) {
    await api('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ full_name: fullName, email, password }),
    })
    await login(email, password)
  }

  function logout() {
    tokens.clear()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>{children}</AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth doit être utilisé dans <AuthProvider>')
  return ctx
}

import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

import { apiFetch } from './api'

export type TokenPair = {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
}

export type Me = {
  id: string
  email: string
  first_name: string
  last_name: string
  headline: string
  location: string
  avatar_url: string
}

type AuthState = {
  tokens: TokenPair | null
  me: Me | null
}

type AuthContextValue = AuthState & {
  login(email: string, password: string): Promise<void>
  register(payload: { email: string; password: string; first_name: string; last_name: string }): Promise<void>
  logout(): Promise<void>
  refresh(): Promise<void>
}

const AUTH_STORAGE_KEY = 'linkedin_clone_tokens'

function loadTokens(): TokenPair | null {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY)
    if (!raw) return null
    return JSON.parse(raw) as TokenPair
  } catch {
    return null
  }
}

function saveTokens(tokens: TokenPair | null) {
  if (!tokens) {
    localStorage.removeItem(AUTH_STORAGE_KEY)
    return
  }
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(tokens))
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [tokens, setTokens] = useState<TokenPair | null>(() => loadTokens())
  const [me, setMe] = useState<Me | null>(null)

  const fetchMe = useCallback(
    async (t: TokenPair) => {
      const meRes = await apiFetch<Me>('/auth/me', { accessToken: t.access_token })
      setMe(meRes)
    },
    [setMe],
  )

  const login = useCallback(
    async (email: string, password: string) => {
      const t = await apiFetch<TokenPair>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      })
      setTokens(t)
      saveTokens(t)
      await fetchMe(t)
    },
    [fetchMe],
  )

  const register = useCallback(
    async (payload: { email: string; password: string; first_name: string; last_name: string }) => {
      const t = await apiFetch<TokenPair>('/auth/register', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      setTokens(t)
      saveTokens(t)
      await fetchMe(t)
    },
    [fetchMe],
  )

  const refresh = useCallback(async () => {
    if (!tokens) return
    const next = await apiFetch<TokenPair>('/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: tokens.refresh_token }),
    })
    setTokens(next)
    saveTokens(next)
    await fetchMe(next)
  }, [tokens, fetchMe])

  const logout = useCallback(async () => {
    if (tokens) {
      await apiFetch('/auth/logout', { method: 'POST', body: JSON.stringify({ refresh_token: tokens.refresh_token }) }).catch(
        () => null,
      )
    }
    setTokens(null)
    setMe(null)
    saveTokens(null)
  }, [tokens])

  const value = useMemo<AuthContextValue>(
    () => ({ tokens, me, login, register, logout, refresh }),
    [tokens, me, login, register, logout, refresh],
  )

  useEffect(() => {
    // Hydrate `me` on page reload when tokens exist.
    if (!tokens || me) return
    fetchMe(tokens).catch(() => {
      // If tokens are invalid/expired, clear them so the app routes to /login.
      setTokens(null)
      setMe(null)
      saveTokens(null)
    })
  }, [tokens, me, fetchMe])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}


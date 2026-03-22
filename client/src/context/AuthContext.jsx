import { createContext, useContext, useEffect, useState } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [accessToken, setAccessToken] = useState(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    fetch('/auth/refresh', { method: 'POST', credentials: 'include' })
      .then(async (res) => {
        if (res.ok) {
          const data = await res.json()
          setAccessToken(data.access_token)
        }
      })
      .catch(() => {})
      .finally(() => setReady(true))
  }, [])

  function login(token) {
    setAccessToken(token)
  }

  function logout() {
    setAccessToken(null)
    fetch('/auth/logout', { method: 'POST', credentials: 'include' }).catch(() => {})
  }

  return (
    <AuthContext.Provider value={{ accessToken, login, logout, ready }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}

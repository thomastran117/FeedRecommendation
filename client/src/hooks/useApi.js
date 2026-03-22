import { useCallback } from 'react'
import { useAuth } from '../context/AuthContext'

// Shared in-flight refresh promise — prevents multiple concurrent token refreshes
let refreshPromise = null

export function useApi() {
  const { accessToken, login, logout } = useAuth()

  const apiFetch = useCallback(
    async (url, options = {}) => {
      const { headers: extraHeaders, ...rest } = options

      function buildRequest(token) {
        return fetch(url, {
          ...rest,
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...extraHeaders,
          },
        })
      }

      let res = await buildRequest(accessToken)

      if (res.status !== 401) return res

      // Token expired — attempt refresh, deduplicated across concurrent calls
      if (!refreshPromise) {
        refreshPromise = fetch('/auth/refresh', { method: 'POST', credentials: 'include' })
          .then((r) => {
            if (!r.ok) throw new Error('Refresh failed')
            return r.json()
          })
          .finally(() => {
            refreshPromise = null
          })
      }

      try {
        const data = await refreshPromise
        login(data.access_token)
        res = await buildRequest(data.access_token)
      } catch {
        logout()
        throw new Error('Session expired. Please sign in again.')
      }

      return res
    },
    [accessToken, login, logout],
  )

  return { apiFetch }
}

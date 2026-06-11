'use client'

import { useState, useEffect } from 'react'
import { getUser, isAuthenticated, clearToken, type AuthUser } from '@/lib/auth'
import { useRouter } from 'next/navigation'

export function useAuth(requireAuth = true) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    const authed = isAuthenticated()
    if (!authed && requireAuth) {
      router.replace('/login')
      return
    }
    setUser(getUser())
    setLoading(false)
  }, [requireAuth, router])

  const logout = () => {
    clearToken()
    router.replace('/login')
  }

  return { user, loading, logout }
}

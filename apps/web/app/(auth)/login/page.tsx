'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Eye, EyeOff, ShieldAlert, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { setToken, setUser } from '@/lib/auth'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setError((data as { detail?: string }).detail || 'Invalid credentials')
        return
      }

      const data = await res.json() as { access_token: string; user: { id: string; email: string; name: string; role: string; org_name?: string } }
      setToken(data.access_token)
      setUser({ ...data.user, role: data.user.role as 'ADMIN' | 'ANALYST' | 'VIEWER' })
      router.push('/dashboard')
    } catch {
      setError('Connection failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  async function handleDevLogin() {
    setEmail('admin@skysignal.dev')
    setPassword('demo1234')
    setLoading(true)
    setError(null)

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'admin@skysignal.dev', password: 'demo1234' }),
      })

      if (!res.ok) {
        // Demo fallback: store mock token
        setToken('demo-token-12345')
        setUser({
          id: 'demo-user',
          email: 'admin@skysignal.dev',
          name: 'Demo Admin',
          role: 'ADMIN',
          org_name: 'SkySignal Demo',
        })
        router.push('/dashboard')
        return
      }

      const data = await res.json() as { access_token: string; user: { id: string; email: string; name: string; role: string; org_name?: string } }
      setToken(data.access_token)
      setUser({ ...data.user, role: data.user.role as 'ADMIN' | 'ANALYST' | 'VIEWER' })
      router.push('/dashboard')
    } catch {
      // Demo fallback
      setToken('demo-token-12345')
      setUser({
        id: 'demo-user',
        email: 'admin@skysignal.dev',
        name: 'Demo Admin',
        role: 'ADMIN',
        org_name: 'SkySignal Demo',
      })
      router.push('/dashboard')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-navy flex items-center justify-center p-4">
      {/* Background grid */}
      <div
        className="fixed inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `linear-gradient(rgba(0,180,200,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(0,180,200,0.5) 1px, transparent 1px)`,
          backgroundSize: '40px 40px',
        }}
      />

      <div className="w-full max-w-md relative">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-teal/20 border border-teal/30 flex items-center justify-center mb-4">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
              <path
                d="M12 2L4 6v6c0 5.25 3.4 10.15 8 11.35C16.6 22.15 20 17.25 20 12V6L12 2z"
                stroke="#00B4C8"
                strokeWidth="1.5"
                strokeLinejoin="round"
              />
              <path
                d="M9 12l2 2 4-4"
                stroke="#00B4C8"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <circle cx="12" cy="9" r="1.5" fill="#00B4C8" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-foreground">SkySignal</h1>
          <p className="text-sm text-muted-foreground mt-1">Drone Threat Intelligence Platform</p>
        </div>

        {/* Card */}
        <div className="bg-[#162030] border border-white/[0.08] rounded-xl p-8 shadow-2xl">
          <h2 className="text-lg font-semibold text-foreground mb-6">Sign in to your account</h2>

          {error && (
            <div className="mb-4 px-3 py-2.5 rounded-md bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="email">Email address</Label>
              <Input
                id="email"
                type="email"
                placeholder="analyst@agency.gov"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                'Sign in'
              )}
            </Button>
          </form>

          <div className="mt-4 pt-4 border-t border-white/[0.08]">
            <Button
              variant="outline"
              className="w-full text-teal border-teal/30 hover:bg-teal/10"
              onClick={handleDevLogin}
              disabled={loading}
              type="button"
            >
              <ShieldAlert className="w-4 h-4" />
              Dev Login (admin@skysignal.dev)
            </Button>
          </div>
        </div>

        <p className="text-center text-xs text-muted-foreground mt-6">
          Authorized access only. All activity is monitored and logged.
        </p>
      </div>
    </div>
  )
}

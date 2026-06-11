'use client'

import { useState } from 'react'
import { Save, Key, Eye, EyeOff } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuth } from '@/hooks/useAuth'

export default function SettingsPage() {
  const { user } = useAuth(false)
  const [orgName, setOrgName] = useState(user?.org_name || '')
  const [showKey, setShowKey] = useState(false)
  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-xl font-bold text-foreground">Settings</h1>
        <p className="text-sm text-muted-foreground mt-0.5">Platform configuration</p>
      </div>

      {/* Org settings */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Organization</CardTitle>
          <CardDescription>Basic organization settings</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="orgName">Organization Name</Label>
            <Input
              id="orgName"
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              placeholder="Enter org name"
            />
          </div>
          <div className="space-y-1.5">
            <Label>Account Email</Label>
            <Input value={user?.email || ''} disabled />
          </div>
          <div className="space-y-1.5">
            <Label>Role</Label>
            <Input value={user?.role || 'ANALYST'} disabled />
          </div>
          <Button onClick={handleSave}>
            <Save className="w-4 h-4" />
            {saved ? 'Saved!' : 'Save Changes'}
          </Button>
        </CardContent>
      </Card>

      {/* API Keys */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Key className="w-4 h-4 text-teal" />
            API Keys
          </CardTitle>
          <CardDescription>Manage API access tokens</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <Label>SkySignal API Key</Label>
            <div className="relative">
              <Input
                type={showKey ? 'text' : 'password'}
                value="sk-demo-••••••••••••••••••••"
                readOnly
                className="pr-10 font-mono text-xs"
              />
              <button
                onClick={() => setShowKey(!showKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-white/[0.03] border border-white/[0.06]">
            <p className="text-xs font-medium text-foreground mb-1">API Base URL</p>
            <code className="text-xs text-teal font-mono">
              {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
            </code>
          </div>

          <div className="space-y-2">
            <Label className="text-xs text-muted-foreground">External Integrations</Label>
            <div className="space-y-2">
              {['FAA DroneZone', 'ADS-B Exchange', 'AUVSI Network', 'FISINT Feed'].map((name) => (
                <div
                  key={name}
                  className="flex items-center justify-between p-3 rounded-lg bg-white/[0.03] border border-white/[0.06]"
                >
                  <span className="text-sm text-foreground">{name}</span>
                  <span className="text-xs text-muted-foreground">Not configured</span>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

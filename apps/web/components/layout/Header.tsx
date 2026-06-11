'use client'

import { Bell, LogOut, User, ChevronDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/hooks/useAuth'
import { useState } from 'react'

interface HeaderProps {
  title?: string
}

export function Header({ title }: HeaderProps) {
  const { user, logout } = useAuth(false)
  const [showMenu, setShowMenu] = useState(false)

  return (
    <header className="fixed top-0 right-0 left-56 h-14 border-b border-white/[0.08] bg-navy/80 backdrop-blur-sm flex items-center px-6 z-10">
      {/* Page title / breadcrumb */}
      <div className="flex-1">
        {title && (
          <h1 className="text-sm font-semibold text-foreground">{title}</h1>
        )}
      </div>

      {/* Right actions */}
      <div className="flex items-center gap-3">
        {/* Notifications */}
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-orange-alert" />
        </Button>

        {/* User menu */}
        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="flex items-center gap-2.5 px-3 py-1.5 rounded-md hover:bg-white/5 transition-colors"
          >
            <div className="w-7 h-7 rounded-full bg-teal/20 border border-teal/30 flex items-center justify-center">
              <User className="w-3.5 h-3.5 text-teal" />
            </div>
            <div className="text-left hidden sm:block">
              <p className="text-xs font-medium text-foreground leading-none">
                {user?.name || 'Analyst'}
              </p>
              <p className="text-[10px] text-muted-foreground mt-0.5">
                {user?.org_name || 'SkySignal'}
              </p>
            </div>
            <ChevronDown className="w-3 h-3 text-muted-foreground" />
          </button>

          {showMenu && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setShowMenu(false)}
              />
              <div className="absolute right-0 top-full mt-1 w-48 bg-[#162030] border border-white/10 rounded-lg shadow-xl z-20 py-1">
                <div className="px-3 py-2 border-b border-white/[0.08]">
                  <p className="text-xs font-medium text-foreground">{user?.name || 'Analyst'}</p>
                  <p className="text-[10px] text-muted-foreground">{user?.email || ''}</p>
                </div>
                <button
                  onClick={() => { setShowMenu(false); logout() }}
                  className="flex items-center gap-2 w-full px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  Sign out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  )
}

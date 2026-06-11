'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  Map,
  CrosshairIcon,
  AlertTriangle,
  BarChart3,
  FileText,
  Database,
  ShieldAlert,
  Settings,
  ChevronRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navItems = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Map', href: '/map', icon: Map },
  { label: 'Assess Location', href: '/assessments/new', icon: CrosshairIcon },
  { label: 'Incidents', href: '/incidents', icon: AlertTriangle },
  { label: 'Analytics', href: '/analytics', icon: BarChart3 },
  { label: 'Reports', href: '/reports', icon: FileText },
  { label: 'Sources', href: '/sources', icon: Database },
]

const adminItems = [
  { label: 'Review Queue', href: '/admin/review', icon: ShieldAlert },
  { label: 'Settings', href: '/admin/settings', icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="fixed left-0 top-0 h-full w-56 border-r border-white/[0.08] bg-[#0a1120] flex flex-col z-20">
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-white/[0.08]">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-teal/20 border border-teal/30">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-label="SkySignal">
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
        <div>
          <span className="font-bold text-sm tracking-wide text-foreground">SkySignal</span>
          <p className="text-[10px] text-muted-foreground leading-none mt-0.5">Drone Intelligence</p>
        </div>
      </div>

      {/* Main nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {navItems.map(({ label, href, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + '/')
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors group',
                active
                  ? 'bg-teal/10 text-teal border border-teal/20'
                  : 'text-slate-400 hover:text-foreground hover:bg-white/5 border border-transparent'
              )}
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{label}</span>
              {active && <ChevronRight className="w-3 h-3 ml-auto opacity-50" />}
            </Link>
          )
        })}

        <div className="pt-4 pb-1 px-3">
          <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
            Admin
          </span>
        </div>

        {adminItems.map(({ label, href, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + '/')
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors group',
                active
                  ? 'bg-teal/10 text-teal border border-teal/20'
                  : 'text-slate-400 hover:text-foreground hover:bg-white/5 border border-transparent'
              )}
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{label}</span>
              {active && <ChevronRight className="w-3 h-3 ml-auto opacity-50" />}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-3 py-3 border-t border-white/[0.08]">
        <div className="flex items-center gap-2 px-3 py-2 rounded-md bg-white/[0.03]">
          <div className="w-2 h-2 rounded-full bg-green-confirmed animate-pulse" />
          <span className="text-xs text-muted-foreground">API Connected</span>
        </div>
      </div>
    </aside>
  )
}

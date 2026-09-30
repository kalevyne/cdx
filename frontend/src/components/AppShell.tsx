import { FolderTree, History, LayoutDashboard, LogOut, Upload } from 'lucide-react'
import { NavLink, Outlet } from 'react-router'

import { useLogout } from '@/api/queries'
import type { SessionUser } from '@/api/types'
import { Logo } from '@/components/Logo'
import { SponsorCredit } from '@/components/SponsorCredit'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

// Add a page to the top navigation by adding it here.
const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/browse', label: 'Browse', icon: FolderTree },
  { to: '/commit', label: 'Commit', icon: Upload },
  { to: '/history', label: 'History', icon: History },
]

export function AppShell({ user }: { user: SessionUser }) {
  const logout = useLogout()

  return (
    <div className="flex min-h-svh flex-col bg-muted/30">
      <header className="sticky top-0 z-10 border-b bg-background/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
          <NavLink to="/" aria-label="CDX home">
            <Logo />
          </NavLink>
          <nav className="order-last flex w-full gap-1 overflow-x-auto sm:order-none sm:w-auto">
            {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground',
                    isActive && 'bg-muted text-foreground',
                  )
                }
              >
                <Icon className="size-4" aria-hidden />
                {label}
              </NavLink>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-2">
            <span className="hidden text-sm text-muted-foreground sm:inline">{user.name}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => logout.mutate()}
              disabled={logout.isPending}
            >
              <LogOut aria-hidden />
              Log out
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:py-8">
        <Outlet />
      </main>

      <footer className="border-t bg-background">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-4 py-4">
          <SponsorCredit />
          <NavLink to="/sponsor" className="text-xs text-muted-foreground hover:text-foreground">
            Public summary
          </NavLink>
        </div>
      </footer>
    </div>
  )
}

/** Page heading used at the top of every page inside the shell. */
export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string
  description?: string
  actions?: React.ReactNode
}) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="font-heading text-2xl font-semibold tracking-tight">{title}</h1>
        {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
      </div>
      {actions && <div className="flex gap-2">{actions}</div>}
    </div>
  )
}

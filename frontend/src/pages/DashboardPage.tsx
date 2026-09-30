import { Activity, CheckCircle2, FileStack, Upload, Users } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router'

import { useCdxCommits, usePublicSummary, useSubsystems } from '@/api/queries'
import type { SubsystemSummary } from '@/api/types'
import { PageHeader } from '@/components/AppShell'
import { CdxCommitRow } from '@/components/CdxCommitRow'
import { StatTile } from '@/components/StatTile'
import { EmptyState, ErrorState, LoadingRows } from '@/components/StateViews'
import { SubsystemCard } from '@/components/SubsystemCard'
import { buttonVariants } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

// A subsystem counts as "active" with a commit in this window.
const ACTIVE_WINDOW_DAYS = 14

export function DashboardPage() {
  const subsystems = useSubsystems()

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="What every subteam is working on, and where it stands."
        actions={
          <Link to="/commit" className={buttonVariants()}>
            <Upload aria-hidden />
            New commit
          </Link>
        }
      />
      <div className="flex flex-col gap-8">
        <Stats subsystems={subsystems.data} />

        <section className="flex flex-col gap-3">
          <h2 className="font-heading text-lg font-semibold">Subsystems</h2>
          {subsystems.isPending && (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 6 }, (_, i) => (
                <Skeleton key={i} className="h-44" />
              ))}
            </div>
          )}
          {subsystems.isError && <ErrorState error={subsystems.error} title="Couldn't load subsystems" />}
          {subsystems.isSuccess && (
            <div className="grid items-start gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {subsystems.data.map((subsystem) => (
                <SubsystemCard key={subsystem.slug} subsystem={subsystem} />
              ))}
            </div>
          )}
        </section>

        <RecentActivity />
      </div>
    </>
  )
}

function Stats({ subsystems }: { subsystems?: SubsystemSummary[] }) {
  const summary = usePublicSummary()
  const [mountedAt] = useState(Date.now)
  const cutoff = mountedAt - ACTIVE_WINDOW_DAYS * 24 * 3600 * 1000
  const active = subsystems?.filter(
    (s) => s.last_commit_at && new Date(s.last_commit_at).getTime() > cutoff,
  ).length

  if (summary.isPending) return <Skeleton className="h-24 w-full" />
  if (summary.isError) return null // The cards below still work; stats are a bonus.

  const { total_commits, anchored_commits, contributors } = summary.data
  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      <StatTile icon={FileStack} label="Commits" value={total_commits} />
      <StatTile
        icon={CheckCircle2}
        label="Anchored on XRPL"
        value={anchored_commits}
        hint={total_commits ? `${Math.round((anchored_commits / total_commits) * 100)}% of commits` : undefined}
      />
      <StatTile icon={Users} label="Contributors" value={contributors} />
      <StatTile
        icon={Activity}
        label="Active subsystems"
        value={active ?? '—'}
        hint={`commits in the last ${ACTIVE_WINDOW_DAYS} days`}
      />
    </div>
  )
}

function RecentActivity() {
  const recent = useCdxCommits({ limit: 6 })

  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="font-heading text-lg font-semibold">Recent activity</h2>
        <Link to="/history" className="text-sm text-primary hover:underline">
          All history
        </Link>
      </div>
      {recent.isPending && <LoadingRows rows={3} />}
      {recent.isError && <ErrorState error={recent.error} title="Couldn't load recent commits" />}
      {recent.isSuccess &&
        (recent.data.length === 0 ? (
          <EmptyState
            icon={FileStack}
            title="Nothing committed yet"
            description="Commits from every subteam will show up here."
          />
        ) : (
          <Card className="py-0">
            <ul className="divide-y">
              {recent.data.map((cdxCommit) => (
                <CdxCommitRow key={cdxCommit.id} cdxCommit={cdxCommit} />
              ))}
            </ul>
          </Card>
        ))}
    </section>
  )
}

import { History, Upload } from 'lucide-react'
import { Link, useSearchParams } from 'react-router'

import { useCdxCommits, useSubsystems } from '@/api/queries'
import { PageHeader } from '@/components/AppShell'
import { CdxCommitRow } from '@/components/CdxCommitRow'
import { EmptyState, ErrorState, LoadingRows } from '@/components/StateViews'
import { buttonVariants } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { cn } from '@/lib/utils'

export function HistoryPage() {
  const [params, setParams] = useSearchParams()
  const subsystem = params.get('subsystem') ?? undefined
  const cdxCommits = useCdxCommits({ subsystem, limit: 100 })

  return (
    <>
      <PageHeader
        title="History"
        description="Every CDX commit, newest first. Open one to see its proof on the XRP Ledger."
        actions={
          <Link to="/commit" className={buttonVariants()}>
            <Upload aria-hidden />
            New commit
          </Link>
        }
      />
      <SubsystemFilter
        selected={subsystem}
        onSelect={(slug) => setParams(slug ? { subsystem: slug } : {})}
      />
      {cdxCommits.isPending && <LoadingRows rows={6} />}
      {cdxCommits.isError && <ErrorState error={cdxCommits.error} title="Couldn't load history" />}
      {cdxCommits.isSuccess &&
        (cdxCommits.data.length === 0 ? (
          <EmptyState
            icon={History}
            title={subsystem ? 'No commits in this subsystem yet' : 'No commits yet'}
            description="Files committed through CDX show up here with their ledger proof."
            action={
              <Link to="/commit" className={buttonVariants({ variant: 'outline' })}>
                Commit a file
              </Link>
            }
          />
        ) : (
          <Card className="py-0">
            <ul className="divide-y">
              {cdxCommits.data.map((cdxCommit) => (
                <CdxCommitRow key={cdxCommit.id} cdxCommit={cdxCommit} />
              ))}
            </ul>
          </Card>
        ))}
    </>
  )
}

function SubsystemFilter({
  selected,
  onSelect,
}: {
  selected?: string
  onSelect: (slug?: string) => void
}) {
  const subsystems = useSubsystems()
  const options = [
    { slug: undefined, name: 'All' },
    ...(subsystems.data ?? []).map(({ slug, name }) => ({ slug, name })),
  ]

  return (
    <div className="mb-4 flex flex-wrap gap-1.5" role="group" aria-label="Filter by subsystem">
      {options.map(({ slug, name }) => (
        <button
          key={name}
          type="button"
          aria-pressed={selected === slug}
          onClick={() => onSelect(slug)}
          className={cn(
            'rounded-full border px-3 py-1 text-xs font-medium transition-colors hover:bg-muted',
            selected === slug && 'border-primary bg-primary text-primary-foreground hover:bg-primary/90',
          )}
        >
          {name}
        </button>
      ))}
    </div>
  )
}

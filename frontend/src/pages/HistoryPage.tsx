import { History, Upload } from 'lucide-react'
import { Link } from 'react-router'

import { useCdxCommits } from '@/api/queries'
import { PageHeader } from '@/components/AppShell'
import { CdxCommitRow } from '@/components/CdxCommitRow'
import { EmptyState, ErrorState, LoadingRows } from '@/components/StateViews'
import { buttonVariants } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

export function HistoryPage() {
  const cdxCommits = useCdxCommits({ limit: 100 })

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
      {cdxCommits.isPending && <LoadingRows rows={6} />}
      {cdxCommits.isError && <ErrorState error={cdxCommits.error} title="Couldn't load history" />}
      {cdxCommits.isSuccess &&
        (cdxCommits.data.length === 0 ? (
          <EmptyState
            icon={History}
            title="No commits yet"
            description="The first file committed through CDX will show up here with its ledger proof."
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

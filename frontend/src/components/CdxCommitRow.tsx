import { FileText } from 'lucide-react'
import { Link } from 'react-router'

import { useSubsystemName } from '@/api/queries'
import type { CdxCommit } from '@/api/types'
import { AnchorStatusBadge } from '@/components/AnchorStatusBadge'
import { Badge } from '@/components/ui/badge'
import { formatRelative } from '@/lib/format'

/** One line in a commit list; links to the commit's proof page. */
export function CdxCommitRow({ cdxCommit }: { cdxCommit: CdxCommit }) {
  const subsystemName = useSubsystemName(cdxCommit.subsystem)

  return (
    <li>
      <Link
        to={`/commits/${cdxCommit.id}`}
        className="flex flex-col gap-1.5 px-4 py-3 transition-colors hover:bg-muted/50 sm:flex-row sm:items-center sm:gap-4"
      >
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <FileText className="size-4 shrink-0 text-muted-foreground" aria-hidden />
            <span className="truncate text-sm font-medium">{cdxCommit.file_name}</span>
            {subsystemName && <Badge variant="outline">{subsystemName}</Badge>}
          </div>
          <p className="truncate text-sm text-muted-foreground">{cdxCommit.message}</p>
        </div>
        <div className="flex shrink-0 items-center gap-3 text-xs text-muted-foreground">
          <span>
            {cdxCommit.author_name} · {formatRelative(cdxCommit.created_at)}
          </span>
          <AnchorStatusBadge status={cdxCommit.anchor_status} />
        </div>
      </Link>
    </li>
  )
}

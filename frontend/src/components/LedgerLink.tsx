import { ExternalLink } from 'lucide-react'

import type { CdxCommit } from '@/api/types'
import { shortHash } from '@/lib/format'
import { cn } from '@/lib/utils'

/** Link to a commit's anchoring transaction on the public XRPL explorer. */
export function LedgerLink({
  cdxCommit,
  className,
}: {
  cdxCommit: Pick<CdxCommit, 'xrpl_tx_hash' | 'xrpl_explorer_url'>
  className?: string
}) {
  if (!cdxCommit.xrpl_tx_hash || !cdxCommit.xrpl_explorer_url) return null
  return (
    <a
      href={cdxCommit.xrpl_explorer_url}
      target="_blank"
      rel="noreferrer"
      className={cn(
        'inline-flex items-center gap-1 font-mono text-xs text-primary hover:underline',
        className,
      )}
    >
      {shortHash(cdxCommit.xrpl_tx_hash)}
      <ExternalLink className="size-3" aria-label="(opens XRPL explorer)" />
    </a>
  )
}

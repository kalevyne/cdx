import { Check, Copy } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

/** A SHA-256 hash in monospace with a copy button. Truncated to one line
 * unless `wrap` is set (for places where people compare it by eye). */
export function HashText({
  hash,
  wrap = false,
  className,
}: {
  hash: string
  wrap?: boolean
  className?: string
}) {
  const [copied, setCopied] = useState(false)

  async function copy() {
    await navigator.clipboard.writeText(hash)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <span className={cn('inline-flex max-w-full items-center gap-1', className)}>
      <code
        className={cn(
          'rounded bg-muted px-1.5 py-0.5 font-mono text-xs',
          wrap ? 'break-all' : 'truncate',
        )}
        title={hash}
      >
        {hash}
      </code>
      <Button variant="ghost" size="icon-xs" onClick={copy} aria-label="Copy hash">
        {copied ? <Check /> : <Copy />}
      </Button>
    </span>
  )
}

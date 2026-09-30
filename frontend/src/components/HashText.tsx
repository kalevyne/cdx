import { Check, Copy } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

/** A SHA-256 hash in monospace with a copy button. */
export function HashText({ hash, className }: { hash: string; className?: string }) {
  const [copied, setCopied] = useState(false)

  async function copy() {
    await navigator.clipboard.writeText(hash)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <span className={cn('inline-flex max-w-full items-center gap-1', className)}>
      <code className="truncate rounded bg-muted px-1.5 py-0.5 font-mono text-xs" title={hash}>
        {hash}
      </code>
      <Button variant="ghost" size="icon-xs" onClick={copy} aria-label="Copy hash">
        {copied ? <Check /> : <Copy />}
      </Button>
    </span>
  )
}

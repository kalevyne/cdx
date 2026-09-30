import { AlertTriangle, CheckCircle2, Clock, Loader2 } from 'lucide-react'

import { useServerStatus } from '@/api/queries'
import type { AnchorStatus } from '@/api/types'
import { Badge } from '@/components/ui/badge'

const STATUS = {
  anchored: { label: 'Anchored', variant: 'success', icon: CheckCircle2, spin: false },
  pending: { label: 'Anchoring…', variant: 'warning', icon: Loader2, spin: true },
  // Pending on a server without XRPL configured: nothing is in flight.
  queued: { label: 'Not anchored yet', variant: 'secondary', icon: Clock, spin: false },
  failed: { label: 'Anchor failed', variant: 'destructive', icon: AlertTriangle, spin: false },
} as const

export function AnchorStatusBadge({ status }: { status: AnchorStatus }) {
  const anchoringEnabled = useServerStatus().data?.anchoring_enabled !== false
  const display = STATUS[status === 'pending' && !anchoringEnabled ? 'queued' : status]
  const Icon = display.icon
  return (
    <Badge variant={display.variant}>
      <Icon className={display.spin ? 'animate-spin' : undefined} aria-hidden />
      {display.label}
    </Badge>
  )
}

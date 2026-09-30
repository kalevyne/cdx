import { AlertTriangle, CheckCircle2, Loader2 } from 'lucide-react'

import type { AnchorStatus } from '@/api/types'
import { Badge } from '@/components/ui/badge'

const STATUS = {
  anchored: { label: 'Anchored', variant: 'success', icon: CheckCircle2 },
  pending: { label: 'Anchoring…', variant: 'warning', icon: Loader2 },
  failed: { label: 'Anchor failed', variant: 'destructive', icon: AlertTriangle },
} as const

export function AnchorStatusBadge({ status }: { status: AnchorStatus }) {
  const { label, variant, icon: Icon } = STATUS[status]
  return (
    <Badge variant={variant}>
      <Icon className={status === 'pending' ? 'animate-spin' : undefined} aria-hidden />
      {label}
    </Badge>
  )
}

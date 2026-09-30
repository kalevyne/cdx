import { cn } from '@/lib/utils'

export function SponsorCredit({ className }: { className?: string }) {
  return (
    <p className={cn('text-xs text-muted-foreground', className)}>
      Supported by Ripple's Center for Digital Assets (CDA).
    </p>
  )
}

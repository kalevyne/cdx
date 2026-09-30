// Shared empty / error / loading states, so every page handles the three
// non-happy paths the same way.
import { AlertTriangle, type LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Skeleton } from '@/components/ui/skeleton'

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: LucideIcon
  title: string
  description?: ReactNode
  action?: ReactNode
}) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-xl border border-dashed px-6 py-10 text-center">
      <div className="flex size-10 items-center justify-center rounded-full bg-muted">
        <Icon className="size-5 text-muted-foreground" aria-hidden />
      </div>
      <p className="font-medium">{title}</p>
      {description && <p className="max-w-sm text-sm text-muted-foreground">{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}

export function ErrorState({ error, title = 'Something went wrong' }: { error: unknown; title?: string }) {
  return (
    <Alert variant="destructive">
      <AlertTriangle aria-hidden />
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription>
        {error instanceof Error ? error.message : 'Please try again in a moment.'}
      </AlertDescription>
    </Alert>
  )
}

export function LoadingRows({ rows = 4 }: { rows?: number }) {
  return (
    <div className="flex flex-col gap-2" aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }, (_, i) => (
        <Skeleton key={i} className="h-9 w-full" />
      ))}
    </div>
  )
}

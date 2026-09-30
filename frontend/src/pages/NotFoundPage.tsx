import { SearchX } from 'lucide-react'
import { Link } from 'react-router'

import { EmptyState } from '@/components/StateViews'
import { buttonVariants } from '@/components/ui/button'

export function NotFoundPage() {
  return (
    <EmptyState
      icon={SearchX}
      title="Page not found"
      description="That link doesn't match anything in CDX."
      action={
        <Link to="/" className={buttonVariants({ variant: 'outline' })}>
          Go home
        </Link>
      }
    />
  )
}

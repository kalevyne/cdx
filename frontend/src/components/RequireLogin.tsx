import { useCurrentUser } from '@/api/queries'
import { AppShell } from '@/components/AppShell'
import { ErrorState } from '@/components/StateViews'
import { Skeleton } from '@/components/ui/skeleton'
import { LoginPage } from '@/pages/LoginPage'

/** Route layout: the app shell for logged-in engineers, the login page otherwise. */
export function RequireLogin() {
  const me = useCurrentUser()

  if (me.isPending) {
    return (
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-6">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }
  if (me.isError) {
    return (
      <div className="mx-auto max-w-md px-4 py-10">
        <ErrorState error={me.error} title="Can't reach the CDX server" />
      </div>
    )
  }
  return me.data ? <AppShell user={me.data} /> : <LoginPage />
}

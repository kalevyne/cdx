import { useEffect } from 'react'
import { useNavigate } from 'react-router'

import { takeLoginReturnPath } from '@/api/client'
import { useCurrentUser } from '@/api/queries'
import { AppShell } from '@/components/AppShell'
import { ErrorState } from '@/components/StateViews'
import { Skeleton } from '@/components/ui/skeleton'
import { LoginPage } from '@/pages/LoginPage'

/** Route layout: the app shell for logged-in engineers, the login page otherwise. */
export function RequireLogin() {
  const me = useCurrentUser()
  const navigate = useNavigate()
  const loggedIn = Boolean(me.data)

  // Back to the page the engineer was on before the Box login round trip.
  useEffect(() => {
    if (!loggedIn) return
    const returnTo = takeLoginReturnPath()
    if (returnTo) navigate(returnTo, { replace: true })
  }, [loggedIn, navigate])

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

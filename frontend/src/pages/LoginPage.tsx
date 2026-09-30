import { AlertTriangle, LogIn } from 'lucide-react'
import { useSearchParams } from 'react-router'

import { startLogin } from '@/api/client'
import { Logo } from '@/components/Logo'
import { SponsorCredit } from '@/components/SponsorCredit'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

// Error codes set by the backend's /api/auth/callback redirect.
const LOGIN_ERRORS: Record<string, { title: string; description: string }> = {
  no_access: {
    title: "Your Box account can't see the CDX folder",
    description:
      'Ask a CalSol lead to share the CDX Dashboard folder in Box with you, then try again.',
  },
  failed: {
    title: "Box login didn't complete",
    description: 'The login was cancelled or expired. Please try again.',
  },
}

export function LoginPage() {
  const [params] = useSearchParams()
  const loginError = LOGIN_ERRORS[params.get('login_error') ?? '']

  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-6 bg-muted/30 px-4 py-10">
      <Card className="w-full max-w-sm">
        <CardHeader className="gap-3">
          <Logo />
          <CardTitle className="text-xl">Log in to CDX</CardTitle>
          <CardDescription>
            CalSol's shared engineering record: browse every subteam's files, commit your work, and
            get a tamper-evident timestamp for each file on the XRP Ledger.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {loginError && (
            <Alert variant="destructive">
              <AlertTriangle aria-hidden />
              <AlertTitle>{loginError.title}</AlertTitle>
              <AlertDescription>{loginError.description}</AlertDescription>
            </Alert>
          )}
          <Button size="lg" className="w-full" onClick={startLogin}>
            <LogIn aria-hidden />
            Log in with Box
          </Button>
          <p className="text-center text-xs text-muted-foreground">
            Use your Berkeley Box account. CDX never sees your password.
          </p>
        </CardContent>
      </Card>
      <SponsorCredit />
    </div>
  )
}

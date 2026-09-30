import {
  AlertTriangle,
  CheckCircle2,
  Download,
  FileText,
  Fingerprint,
  Landmark,
  Loader2,
  type LucideIcon,
  MinusCircle,
  RotateCw,
  ShieldCheck,
  XCircle,
} from 'lucide-react'
import type { ReactNode } from 'react'
import { useState } from 'react'
import { Link, useParams } from 'react-router'

import { fileDownloadUrl } from '@/api/client'
import { useCdxCommit, useRetryAnchoring, useServerStatus, useVerification } from '@/api/queries'
import type { CdxCommit, VerificationCheck } from '@/api/types'
import { AnchorStatusBadge } from '@/components/AnchorStatusBadge'
import { PageHeader } from '@/components/AppShell'
import { HashText } from '@/components/HashText'
import { LedgerLink } from '@/components/LedgerLink'
import { ErrorState, LoadingRows } from '@/components/StateViews'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button, buttonVariants } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { formatBytes, formatDateTime } from '@/lib/format'
import { cn } from '@/lib/utils'

export function CommitDetailPage() {
  const id = Number(useParams().id)
  const cdxCommit = useCdxCommit(id)

  if (cdxCommit.isPending) return <LoadingRows rows={6} />
  if (cdxCommit.isError) return <ErrorState error={cdxCommit.error} title="Couldn't load this commit" />

  const commit = cdxCommit.data
  return (
    <>
      <PageHeader
        title={commit.file_name}
        description={commit.message}
        actions={
          <a
            href={fileDownloadUrl(commit.box_file_id, commit.box_file_version)}
            download
            className={buttonVariants({ variant: 'outline' })}
          >
            <Download aria-hidden />
            Download this version
          </a>
        }
      />
      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <ProofCard cdxCommit={commit} />
        <DetailsCard cdxCommit={commit} />
      </div>
    </>
  )
}

/** The demo moment: file → fingerprint → public ledger, each independently re-checkable. */
function ProofCard({ cdxCommit }: { cdxCommit: CdxCommit }) {
  const [verifyRequested, setVerifyRequested] = useState(false)
  const verification = useVerification(cdxCommit.id, verifyRequested)
  const retry = useRetryAnchoring(cdxCommit.id)
  const result = verification.data

  function verify() {
    if (verifyRequested) verification.refetch()
    else setVerifyRequested(true)
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <CardTitle>Proof of record</CardTitle>
          <AnchorStatusBadge status={cdxCommit.anchor_status} />
        </div>
        <CardDescription>
          This file's fingerprint is written to the public XRP Ledger. Anyone can re-hash the file
          and compare — no need to trust CDX, Box, or CalSol.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">
        <ol className="grid gap-3 md:grid-cols-3">
          <ProofStep step={1} icon={FileText} title="The file in Box" check={result?.box}>
            <span className="truncate">{cdxCommit.file_name}</span>
            <span className="text-xs text-muted-foreground">{formatBytes(cdxCommit.file_size)}</span>
          </ProofStep>
          <ProofStep step={2} icon={Fingerprint} title="Its SHA-256 fingerprint">
            <HashText hash={cdxCommit.sha256_hash} wrap />
          </ProofStep>
          <ProofStep step={3} icon={Landmark} title="On the XRP Ledger" check={result?.ledger}>
            <LedgerStepBody cdxCommit={cdxCommit} />
          </ProofStep>
        </ol>

        {cdxCommit.anchor_status === 'failed' && (
          <Alert variant="destructive">
            <AlertTriangle aria-hidden />
            <AlertTitle>Anchoring failed</AlertTitle>
            <AlertDescription className="flex flex-col items-start gap-2">
              <span>{cdxCommit.anchor_error}</span>
              <Button size="sm" variant="outline" onClick={() => retry.mutate()} disabled={retry.isPending}>
                <RotateCw aria-hidden />
                Retry anchoring
              </Button>
              {retry.isError && <span>{retry.error.message}</span>}
            </AlertDescription>
          </Alert>
        )}

        <div className="flex flex-col gap-3 border-t pt-4 sm:flex-row sm:items-center">
          <Button onClick={verify} disabled={verification.isFetching}>
            {verification.isFetching ? <Loader2 className="animate-spin" aria-hidden /> : <ShieldCheck aria-hidden />}
            {verification.isFetching ? 'Checking Box and the ledger…' : 'Verify now'}
          </Button>
          {verification.isError && (
            <span className="text-sm text-destructive">{verification.error.message}</span>
          )}
          {result && !verification.isFetching && (
            <p className={cn('text-sm font-medium', result.verified ? 'text-emerald-700' : 'text-amber-700')}>
              {result.verified
                ? "Verified: Box's copy and the public ledger both match this fingerprint."
                : 'Not fully verified — see the steps above.'}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

function LedgerStepBody({ cdxCommit }: { cdxCommit: CdxCommit }) {
  const anchoringEnabled = useServerStatus().data?.anchoring_enabled !== false
  if (cdxCommit.anchor_status === 'anchored') {
    return (
      <>
        <LedgerLink cdxCommit={cdxCommit} />
        <span className="text-xs text-muted-foreground">
          Ledger #{cdxCommit.xrpl_ledger_index} · XRPL {cdxCommit.xrpl_network}
        </span>
      </>
    )
  }
  if (cdxCommit.anchor_status === 'pending') {
    return (
      <span className="text-sm text-muted-foreground">
        {anchoringEnabled
          ? 'Waiting for ledger validation…'
          : "XRPL anchoring isn't configured on this server yet. This commit will be anchored automatically once it is."}
      </span>
    )
  }
  return <span className="text-sm text-muted-foreground">Not anchored</span>
}

const CHECK_DISPLAY = {
  match: { icon: CheckCircle2, className: 'text-emerald-600', label: 'Matches' },
  mismatch: { icon: XCircle, className: 'text-destructive', label: "Doesn't match" },
  unavailable: { icon: MinusCircle, className: 'text-muted-foreground', label: "Couldn't check" },
} as const

function ProofStep({
  step,
  icon: Icon,
  title,
  check,
  children,
}: {
  step: number
  icon: LucideIcon
  title: string
  check?: VerificationCheck
  children: ReactNode
}) {
  const display = check ? CHECK_DISPLAY[check.status] : null
  return (
    <li
      className={cn(
        'flex min-w-0 flex-col gap-2 rounded-lg border bg-muted/30 p-3',
        check?.status === 'match' && 'border-emerald-300 bg-emerald-50/60',
        check?.status === 'mismatch' && 'border-destructive/40 bg-destructive/5',
      )}
    >
      <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground uppercase">
        <span className="flex size-5 items-center justify-center rounded-full bg-primary text-[0.65rem] text-primary-foreground">
          {step}
        </span>
        <Icon className="size-3.5" aria-hidden />
        {title}
      </div>
      <div className="flex min-w-0 flex-col gap-0.5 text-sm">{children}</div>
      {display && check && (
        <div className={cn('flex items-start gap-1.5 text-xs', display.className)}>
          <display.icon className="mt-px size-3.5 shrink-0" aria-hidden />
          <span>
            <span className="font-medium">{display.label}.</span> {check.detail}
          </span>
        </div>
      )}
    </li>
  )
}

function DetailsCard({ cdxCommit }: { cdxCommit: CdxCommit }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Details</CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="flex flex-col gap-3 text-sm">
          <DetailRow label="Committed by">{cdxCommit.author_name}</DetailRow>
          <DetailRow label="Committed">{formatDateTime(cdxCommit.created_at)}</DetailRow>
          <DetailRow label="Folder">
            <Link to={`/browse?folder=${cdxCommit.box_folder_id}`} className="text-primary hover:underline">
              Open in browser
            </Link>
          </DetailRow>
          <DetailRow label="Box version">
            <code className="font-mono text-xs">{cdxCommit.box_file_version ?? '—'}</code>
          </DetailRow>
          {cdxCommit.anchored_at && (
            <DetailRow label="Anchored">{formatDateTime(cdxCommit.anchored_at)}</DetailRow>
          )}
          {cdxCommit.design_review_box_file_id && cdxCommit.design_review_sha256_hash && (
            <DetailRow label="Design review">
              <span className="flex min-w-0 flex-col gap-1">
                <a
                  href={fileDownloadUrl(cdxCommit.design_review_box_file_id)}
                  download
                  className="text-primary hover:underline"
                >
                  Download
                </a>
                <HashText hash={cdxCommit.design_review_sha256_hash} />
              </span>
            </DetailRow>
          )}
        </dl>
      </CardContent>
    </Card>
  )
}

function DetailRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="min-w-0">{children}</dd>
    </div>
  )
}

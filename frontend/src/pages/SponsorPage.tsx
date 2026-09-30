import {
  CheckCircle2,
  ExternalLink,
  FileStack,
  Fingerprint,
  Landmark,
  LogIn,
  Upload,
  Users,
} from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router'

import { usePublicSummary } from '@/api/queries'
import type { PublicCdxCommit, PublicSummary } from '@/api/types'
import { Logo } from '@/components/Logo'
import { StageProgress } from '@/components/StageProgress'
import { StatTile } from '@/components/StatTile'
import { EmptyState, ErrorState } from '@/components/StateViews'
import { buttonVariants } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { formatRelative, shortHash } from '@/lib/format'

/** Public, read-only summary for sponsors and visitors (no login). */
export function SponsorPage() {
  const summary = usePublicSummary()

  return (
    <div className="min-h-svh bg-muted/30">
      <header className="border-b bg-background">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <Logo />
          <Link to="/" className={buttonVariants({ variant: 'outline', size: 'sm' })}>
            <LogIn aria-hidden />
            Team login
          </Link>
        </div>
      </header>

      <main className="mx-auto flex max-w-5xl flex-col gap-10 px-4 py-10">
        <Hero />
        {summary.isPending && <Skeleton className="h-96 w-full" />}
        {summary.isError && <ErrorState error={summary.error} title="Couldn't load the summary" />}
        {summary.isSuccess && <SummaryBody summary={summary.data} />}
        <HowItWorks />
      </main>

      <footer className="border-t bg-background">
        <div className="mx-auto max-w-5xl px-4 py-6 text-sm text-muted-foreground">
          CDX is built by CalSol, UC Berkeley's Solar Vehicle Team, with support from Ripple's
          Center for Digital Assets.
        </div>
      </footer>
    </div>
  )
}

function Hero() {
  return (
    <section className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
      <div className="flex max-w-2xl flex-col gap-3">
        <span className="text-xs font-semibold tracking-wide text-primary uppercase">
          CalSol · UC Berkeley Solar Vehicle Team
        </span>
        <h1 className="font-heading text-3xl font-bold tracking-tight sm:text-4xl">
          Every engineering file, on the record.
        </h1>
        <p className="text-muted-foreground">
          CDX gives CalSol's subteams one shared view of each other's work, and writes a
          fingerprint of every committed file to the XRP Ledger — a permanent record that outlives
          server migrations, lost passwords, and graduating classes.
        </p>
      </div>
      <Card className="shrink-0 gap-1 border-[#FDB515]/60 bg-[#FDB515]/10 px-5 py-4 md:max-w-xs">
        <span className="text-xs font-medium text-muted-foreground">Supported by</span>
        <span className="font-heading font-semibold">Ripple's Center for Digital Assets (CDA)</span>
      </Card>
    </section>
  )
}

function SummaryBody({ summary }: { summary: PublicSummary }) {
  const activeSubsystems = summary.subsystems.filter((s) => s.commit_count > 0).length
  return (
    <>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile icon={FileStack} label="Files committed" value={summary.total_commits} />
        <StatTile
          icon={CheckCircle2}
          label="Anchored on the XRP Ledger"
          value={summary.anchored_commits}
        />
        <StatTile icon={Users} label="Contributors" value={summary.contributors} />
        <StatTile
          icon={Landmark}
          label="Subsystems with commits"
          value={`${activeSubsystems} / ${summary.subsystems.length}`}
        />
      </div>

      <div className="grid items-start gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Where each subsystem stands</CardTitle>
            <CardDescription>Design stage, as reported by each subteam.</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="flex flex-col gap-4">
              {summary.subsystems.map((s) => (
                <li key={s.slug} className="grid grid-cols-[7rem_minmax(0,1fr)] items-start gap-3">
                  <div className="flex flex-col">
                    <span className="text-sm font-medium">{s.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {s.commit_count} {s.commit_count === 1 ? 'commit' : 'commits'}
                    </span>
                  </div>
                  <StageProgress stage={s.stage} />
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Latest proofs on the ledger</CardTitle>
            <CardDescription>
              Each links to its public XRP Ledger transaction, where the file's SHA-256 is stored.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {summary.recent_anchored.length === 0 ? (
              <EmptyState icon={Landmark} title="No anchored files yet" />
            ) : (
              <ul className="divide-y">
                {summary.recent_anchored.map((c) => (
                  <ProofRow
                    key={`${c.xrpl_tx_hash}`}
                    cdxCommit={c}
                    subsystemName={summary.subsystems.find((s) => s.slug === c.subsystem)?.name}
                  />
                ))}
              </ul>
            )}
            {summary.recent_anchored.some((c) => c.xrpl_network === 'testnet') && (
              <p className="mt-3 text-xs text-muted-foreground">
                During development, CDX anchors to the XRPL Testnet.
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  )
}

function ProofRow({
  cdxCommit,
  subsystemName,
}: {
  cdxCommit: PublicCdxCommit
  subsystemName?: string
}) {
  return (
    <li className="flex items-center justify-between gap-3 py-2.5">
      <div className="flex min-w-0 flex-col">
        <span className="truncate text-sm font-medium">{cdxCommit.file_name}</span>
        <span className="text-xs text-muted-foreground">
          {[subsystemName, formatRelative(cdxCommit.created_at)].filter(Boolean).join(' · ')}
        </span>
      </div>
      {cdxCommit.xrpl_explorer_url && (
        <a
          href={cdxCommit.xrpl_explorer_url}
          target="_blank"
          rel="noreferrer"
          className="flex shrink-0 items-center gap-1 font-mono text-xs text-primary hover:underline"
          title={`SHA-256 ${cdxCommit.sha256_hash}`}
        >
          {shortHash(cdxCommit.sha256_hash)}
          <ExternalLink className="size-3" aria-label="(opens XRPL explorer)" />
        </a>
      )}
    </li>
  )
}

function HowItWorks() {
  return (
    <section className="flex flex-col gap-4">
      <h2 className="font-heading text-xl font-semibold">How it works</h2>
      <ol className="grid gap-3 md:grid-cols-3">
        <Step icon={Upload} title="1. Commit">
          An engineer uploads a file through CDX with a short message. It's stored in CalSol's
          existing Box, where the team already works.
        </Step>
        <Step icon={Fingerprint} title="2. Fingerprint">
          CDX computes the file's SHA-256 — a 64-character fingerprint that changes completely if a
          single byte of the file does.
        </Step>
        <Step icon={Landmark} title="3. Anchor">
          The fingerprint is written into a transaction on the public XRP Ledger. Anyone can
          re-hash the file later and compare, without trusting CalSol's servers.
        </Step>
      </ol>
    </section>
  )
}

function Step({
  icon: Icon,
  title,
  children,
}: {
  icon: typeof Upload
  title: string
  children: ReactNode
}) {
  return (
    <li>
      <Card className="h-full gap-2 px-5 py-4">
        <Icon className="size-5 text-primary" aria-hidden />
        <span className="font-medium">{title}</span>
        <p className="text-sm text-muted-foreground">{children}</p>
      </Card>
    </li>
  )
}

import { cn } from '@/lib/utils'

/** CDX wordmark: Berkeley blue + California gold, matching public/favicon.svg. */
export function Logo({ className }: { className?: string }) {
  return (
    <span className={cn('inline-flex items-center gap-2', className)}>
      <svg viewBox="0 0 32 32" className="size-7 shrink-0" aria-hidden>
        <rect width="32" height="32" rx="7" fill="#003262" />
        <path
          d="M9 20.5 16 8l7 12.5"
          fill="none"
          stroke="#FDB515"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx="16" cy="23" r="2.2" fill="#FDB515" />
      </svg>
      <span className="flex flex-col leading-none">
        <span className="font-heading text-base font-bold tracking-tight">CDX</span>
        <span className="text-[0.65rem] font-medium tracking-wide text-muted-foreground uppercase">
          CalSol Engineering
        </span>
      </span>
    </span>
  )
}

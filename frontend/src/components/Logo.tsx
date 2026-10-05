import { cn } from '@/lib/utils'

/** CDX wordmark: the sun from the CalSol logo (public/calsol-sun.png, also the favicon). */
export function Logo({ className }: { className?: string }) {
  return (
    <span className={cn('inline-flex items-center gap-2', className)}>
      <img src="/calsol-sun.png" alt="" className="size-8 shrink-0" aria-hidden />
      <span className="flex flex-col leading-none">
        <span className="font-heading text-base font-bold tracking-tight">CDX</span>
        <span className="text-[0.65rem] font-medium tracking-wide text-muted-foreground uppercase">
          CalSol
        </span>
      </span>
    </span>
  )
}

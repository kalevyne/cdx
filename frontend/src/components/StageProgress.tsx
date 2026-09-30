import type { SubsystemStage } from '@/api/types'
import { STAGE_LABELS, STAGES } from '@/lib/stages'
import { cn } from '@/lib/utils'

/** A segmented bar showing how far through the design process a subsystem is. */
export function StageProgress({
  stage,
  className,
}: {
  stage: SubsystemStage | null | undefined
  className?: string
}) {
  const reached = stage ? STAGES.indexOf(stage) : -1
  return (
    <div className={cn('flex flex-col gap-1.5', className)}>
      <div
        className="flex gap-1"
        role="meter"
        aria-label="Design stage"
        aria-valuemin={0}
        aria-valuemax={STAGES.length}
        aria-valuenow={reached + 1}
        aria-valuetext={stage ? STAGE_LABELS[stage] : 'Not set'}
      >
        {STAGES.map((s, index) => (
          <span
            key={s}
            className={cn(
              'h-1.5 flex-1 rounded-full',
              index <= reached
                ? stage === 'complete'
                  ? 'bg-emerald-500'
                  : 'bg-primary'
                : 'bg-muted',
            )}
          />
        ))}
      </div>
      <span className="text-xs text-muted-foreground">
        {stage ? STAGE_LABELS[stage] : 'Stage not set'}
      </span>
    </div>
  )
}

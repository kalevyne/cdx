import type { SubsystemStage } from '@/api/types'

// Display labels for the backend's SubsystemStage enum. Typed as a Record so
// the build fails if the backend adds a stage this map doesn't cover.
export const STAGE_LABELS: Record<SubsystemStage, string> = {
  concept: 'Concept',
  design: 'Design',
  review: 'Design review',
  manufacturing: 'Manufacturing',
  testing: 'Testing',
  complete: 'Complete',
}

/** Stages in process order (the order they're declared above). */
export const STAGES = Object.keys(STAGE_LABELS) as SubsystemStage[]

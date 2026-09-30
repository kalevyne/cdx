import { Pencil } from 'lucide-react'
import { type FormEvent, useState } from 'react'
import { Link } from 'react-router'

import { useUpdateSubsystem } from '@/api/queries'
import type { SubsystemStage, SubsystemSummary } from '@/api/types'
import { StageProgress } from '@/components/StageProgress'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input, Label, NativeSelect, Textarea } from '@/components/ui/input'
import { formatRelative } from '@/lib/format'
import { STAGE_LABELS, STAGES } from '@/lib/stages'

export function SubsystemCard({ subsystem }: { subsystem: SubsystemSummary }) {
  const [editing, setEditing] = useState(false)

  return (
    <Card className="gap-3">
      <CardHeader className="flex flex-row items-start justify-between gap-2">
        <div className="flex flex-col gap-0.5">
          <CardTitle>{subsystem.name}</CardTitle>
          <span className="text-xs text-muted-foreground">
            {subsystem.owner_name ? `Lead: ${subsystem.owner_name}` : 'No lead set'}
          </span>
        </div>
        {!editing && (
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => setEditing(true)}
            aria-label={`Edit ${subsystem.name} status`}
          >
            <Pencil />
          </Button>
        )}
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {editing ? (
          <EditSubsystemForm subsystem={subsystem} onDone={() => setEditing(false)} />
        ) : (
          <>
            <StageProgress stage={subsystem.stage} />
            {subsystem.status_note && (
              <p className="text-sm text-muted-foreground">{subsystem.status_note}</p>
            )}
            <p className="text-xs text-muted-foreground">
              {subsystem.commit_count} {subsystem.commit_count === 1 ? 'commit' : 'commits'}
              {subsystem.last_commit_at && ` · last ${formatRelative(subsystem.last_commit_at)}`}
            </p>
            {subsystem.recent_commits.length > 0 && (
              <ul className="flex flex-col gap-1 border-t pt-2">
                {subsystem.recent_commits.map((c) => (
                  <li key={c.id}>
                    <Link
                      to={`/commits/${c.id}`}
                      className="flex items-baseline justify-between gap-2 text-sm hover:underline"
                    >
                      <span className="truncate">{c.file_name}</span>
                      <span className="shrink-0 text-xs text-muted-foreground">
                        {formatRelative(c.created_at)}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}

function EditSubsystemForm({
  subsystem,
  onDone,
}: {
  subsystem: SubsystemSummary
  onDone: () => void
}) {
  const update = useUpdateSubsystem(subsystem.slug)
  const [owner, setOwner] = useState(subsystem.owner_name ?? '')
  const [stage, setStage] = useState<SubsystemStage | ''>(subsystem.stage ?? '')
  const [note, setNote] = useState(subsystem.status_note ?? '')
  const idPrefix = `subsystem-${subsystem.slug}`

  function save(event: FormEvent) {
    event.preventDefault()
    update.mutate(
      { owner_name: owner, stage: stage || null, status_note: note },
      { onSuccess: onDone },
    )
  }

  return (
    <form onSubmit={save} className="flex flex-col gap-3">
      <div className="flex flex-col gap-1.5">
        <Label htmlFor={`${idPrefix}-owner`}>Lead</Label>
        <Input
          id={`${idPrefix}-owner`}
          value={owner}
          onChange={(e) => setOwner(e.target.value)}
          placeholder="Who to ask about this subsystem"
        />
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor={`${idPrefix}-stage`}>Stage</Label>
        <NativeSelect
          id={`${idPrefix}-stage`}
          value={stage}
          onChange={(e) => setStage(e.target.value as SubsystemStage | '')}
        >
          <option value="">Not set</option>
          {STAGES.map((s) => (
            <option key={s} value={s}>
              {STAGE_LABELS[s]}
            </option>
          ))}
        </NativeSelect>
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor={`${idPrefix}-note`}>Status note</Label>
        <Textarea
          id={`${idPrefix}-note`}
          value={note}
          onChange={(e) => setNote(e.target.value)}
          rows={2}
          placeholder="e.g. Waiting on cell samples"
        />
      </div>
      {update.isError && <p className="text-sm text-destructive">{update.error.message}</p>}
      <div className="flex gap-2">
        <Button type="submit" size="sm" disabled={update.isPending}>
          {update.isPending ? 'Saving…' : 'Save'}
        </Button>
        <Button type="button" size="sm" variant="ghost" onClick={onDone}>
          Cancel
        </Button>
      </div>
    </form>
  )
}

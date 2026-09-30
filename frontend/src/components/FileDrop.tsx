import { FileUp, X } from 'lucide-react'
import { useId, useState } from 'react'

import { MAX_UPLOAD_BYTES } from '@/api/types'
import { Button } from '@/components/ui/button'
import { formatBytes } from '@/lib/format'
import { cn } from '@/lib/utils'

/** A file picker that also accepts drag-and-drop. Holds no state of its own
 * beyond the drag highlight — the chosen file lives in the parent form. */
export function FileDrop({
  file,
  onChange,
  prompt,
  id,
}: {
  file: File | null
  onChange: (file: File | null) => void
  prompt: string
  id?: string
}) {
  const fallbackId = useId()
  const inputId = id ?? fallbackId
  const [dragging, setDragging] = useState(false)

  if (file) {
    return (
      <div className="flex items-center justify-between gap-3 rounded-lg border bg-muted/40 px-3 py-2.5">
        <div className="flex min-w-0 items-center gap-2">
          <FileUp className="size-4 shrink-0 text-muted-foreground" aria-hidden />
          <span className="truncate text-sm font-medium">{file.name}</span>
          <span className="shrink-0 text-xs text-muted-foreground">{formatBytes(file.size)}</span>
        </div>
        <Button variant="ghost" size="icon-sm" onClick={() => onChange(null)} aria-label="Remove file">
          <X />
        </Button>
      </div>
    )
  }

  return (
    <label
      htmlFor={inputId}
      onDragOver={(event) => {
        event.preventDefault()
        setDragging(true)
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(event) => {
        event.preventDefault()
        setDragging(false)
        onChange(event.dataTransfer.files[0] ?? null)
      }}
      className={cn(
        'flex cursor-pointer flex-col items-center gap-1 rounded-lg border border-dashed px-4 py-6 text-center transition-colors hover:bg-muted/40',
        dragging && 'border-primary bg-primary/5',
      )}
    >
      <FileUp className="size-5 text-muted-foreground" aria-hidden />
      <span className="text-sm font-medium">{prompt}</span>
      <span className="text-xs text-muted-foreground">Drag a file here or click to browse (max {formatBytes(MAX_UPLOAD_BYTES)})</span>
      <input
        id={inputId}
        type="file"
        className="sr-only"
        onChange={(event) => onChange(event.target.files?.[0] ?? null)}
      />
    </label>
  )
}

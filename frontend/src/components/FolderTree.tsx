import { ChevronRight, Folder, FolderOpen } from 'lucide-react'
import { useState } from 'react'

import { useFolder } from '@/api/queries'
import type { BoxFolderRef } from '@/api/types'
import { ErrorState } from '@/components/StateViews'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

interface FolderTreeProps {
  selectedId?: string
  onSelect: (folder: BoxFolderRef) => void
}

/** Lazily-loaded tree of the Dashboard folder hierarchy (folders only). The
 * selected folder's ancestors start expanded, so deep links show where you are. */
export function FolderTree({ selectedId, onSelect }: FolderTreeProps) {
  const root = useFolder()
  const selected = useFolder(selectedId, { enabled: Boolean(selectedId) })
  const expandIds = new Set(selected.data?.path.map((folder) => folder.id))

  if (root.isPending) return <Skeleton className="h-8 w-full" />
  if (root.isError) return <ErrorState error={root.error} title="Couldn't load folders" />

  return (
    <ul role="tree" aria-label="Dashboard folders" className="text-sm">
      <FolderNode
        folder={{ id: root.data.id, name: root.data.name }}
        depth={0}
        expandIds={expandIds}
        selectedId={selectedId}
        onSelect={onSelect}
      />
    </ul>
  )
}

function FolderNode({
  folder,
  depth,
  expandIds,
  selectedId,
  onSelect,
}: FolderTreeProps & { folder: BoxFolderRef; depth: number; expandIds: Set<string> }) {
  // Until the user toggles a node, it's open if it's the root or on the selected path.
  const [toggledOpen, setToggledOpen] = useState<boolean>()
  const open = toggledOpen ?? (depth === 0 || expandIds.has(folder.id))
  // Children are fetched only once a node is expanded.
  const listing = useFolder(depth === 0 ? undefined : folder.id, { enabled: open })
  const subfolders = listing.data?.items.filter((item) => item.type === 'folder') ?? []
  const selected = folder.id === selectedId
  const FolderIcon = open ? FolderOpen : Folder

  return (
    <li role="treeitem" aria-expanded={open} aria-selected={selected}>
      <div
        className={cn(
          'flex items-center gap-0.5 rounded-md pr-2 hover:bg-muted',
          selected && 'bg-muted font-medium',
        )}
        style={{ paddingLeft: `${depth * 0.875}rem` }}
      >
        <button
          type="button"
          className="flex size-6 shrink-0 items-center justify-center rounded text-muted-foreground hover:text-foreground"
          onClick={() => setToggledOpen(!open)}
          aria-label={open ? `Collapse ${folder.name}` : `Expand ${folder.name}`}
        >
          <ChevronRight className={cn('size-3.5 transition-transform', open && 'rotate-90')} />
        </button>
        <button
          type="button"
          className="flex min-w-0 flex-1 items-center gap-1.5 py-1 text-left"
          onClick={() => {
            onSelect(folder)
            setToggledOpen(true)
          }}
        >
          <FolderIcon className="size-4 shrink-0 text-amber-500" aria-hidden />
          <span className="truncate">{folder.name}</span>
        </button>
      </div>
      {open && (
        <ul role="group">
          {listing.isPending && (
            <li style={{ paddingLeft: `${(depth + 1) * 0.875 + 1.5}rem` }} className="py-1">
              <Skeleton className="h-4 w-24" />
            </li>
          )}
          {listing.isSuccess && subfolders.length === 0 && (
            <li
              style={{ paddingLeft: `${(depth + 1) * 0.875 + 1.5}rem` }}
              className="py-1 text-xs text-muted-foreground"
            >
              No subfolders
            </li>
          )}
          {subfolders.map((child) => (
            <FolderNode
              key={child.id}
              folder={child}
              depth={depth + 1}
              expandIds={expandIds}
              selectedId={selectedId}
              onSelect={onSelect}
            />
          ))}
        </ul>
      )}
    </li>
  )
}

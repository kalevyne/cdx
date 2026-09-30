import { ChevronRight } from 'lucide-react'

import type { BoxFolderRef } from '@/api/types'
import { cn } from '@/lib/utils'

/** "CDX › Zephyr › Battery", optionally clickable. */
export function FolderBreadcrumb({
  path,
  onNavigate,
  className,
}: {
  path: BoxFolderRef[]
  onNavigate?: (folderId: string) => void
  className?: string
}) {
  return (
    <nav aria-label="Folder path" className={cn('min-w-0', className)}>
      <ol className="flex flex-wrap items-center gap-1 text-sm text-muted-foreground">
        {path.map((folder, index) => {
          const isLast = index === path.length - 1
          return (
            <li key={folder.id} className="flex items-center gap-1">
              {onNavigate && !isLast ? (
                <button
                  type="button"
                  className="hover:text-foreground hover:underline"
                  onClick={() => onNavigate(folder.id)}
                >
                  {folder.name}
                </button>
              ) : (
                <span className={cn(isLast && 'font-medium text-foreground')}>{folder.name}</span>
              )}
              {!isLast && <ChevronRight className="size-3.5" aria-hidden />}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}

import { Download, FileText, Folder, FolderOpen, Upload } from 'lucide-react'
import { Link, useSearchParams } from 'react-router'

import { fileDownloadUrl } from '@/api/client'
import { useFolder } from '@/api/queries'
import type { BoxItem } from '@/api/types'
import { PageHeader } from '@/components/AppShell'
import { FilePreviewDialog } from '@/components/FilePreviewDialog'
import { FolderBreadcrumb } from '@/components/FolderBreadcrumb'
import { FolderTree } from '@/components/FolderTree'
import { EmptyState, ErrorState, LoadingRows } from '@/components/StateViews'
import { buttonVariants } from '@/components/ui/button'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { formatBytes, formatRelative } from '@/lib/format'

export function BrowsePage() {
  const [params, setParams] = useSearchParams()
  const folderId = params.get('folder') ?? undefined
  const openFolder = (id: string) => setParams({ folder: id })
  // The previewed file lives in the URL, so a preview can be linked to.
  const previewFile = (id: string | null, { replace = false } = {}) =>
    setParams({ ...(folderId && { folder: folderId }), ...(id && { file: id }) }, { replace })

  return (
    <>
      <PageHeader
        title="Browse"
        description="Every subteam's files, straight from CalSol's Box. Read-only — changes go through commits."
      />
      <div className="grid items-start gap-6 md:grid-cols-[18rem_minmax(0,1fr)]">
        <Card className="py-3">
          <CardContent className="px-2">
            <FolderTree selectedId={folderId} onSelect={(folder) => openFolder(folder.id)} />
          </CardContent>
        </Card>
        <FolderContents
          folderId={folderId}
          onOpenFolder={openFolder}
          previewedFileId={params.get('file')}
          onPreviewFile={previewFile}
        />
      </div>
    </>
  )
}

function FolderContents({
  folderId,
  onOpenFolder,
  previewedFileId,
  onPreviewFile,
}: {
  folderId?: string
  onOpenFolder: (id: string) => void
  previewedFileId: string | null
  onPreviewFile: (id: string | null, options?: { replace?: boolean }) => void
}) {
  const listing = useFolder(folderId)

  if (listing.isPending) {
    return (
      <Card>
        <CardContent>
          <LoadingRows />
        </CardContent>
      </Card>
    )
  }
  if (listing.isError) return <ErrorState error={listing.error} title="Couldn't open this folder" />

  const folder = listing.data
  const items = [...folder.items].sort(
    (a, b) => Number(a.type === 'file') - Number(b.type === 'file') || a.name.localeCompare(b.name),
  )
  const files = items.filter((item) => item.type === 'file')
  const previewedIndex = files.findIndex((file) => file.id === previewedFileId)
  const previewed = files[previewedIndex]
  // Stepping between files replaces the URL, so Back closes the preview.
  const stepTo = (file?: BoxItem) => file && (() => onPreviewFile(file.id, { replace: true }))

  return (
    <Card>
      <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3">
        <FolderBreadcrumb
          path={[...folder.path, { id: folder.id, name: folder.name }]}
          onNavigate={onOpenFolder}
        />
        <Link to={`/commit?folder=${folder.id}`} className={buttonVariants({ size: 'sm' })}>
          <Upload aria-hidden />
          Commit a file here
        </Link>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <EmptyState
            icon={FolderOpen}
            title="This folder is empty"
            description="Commit the first file to start its history."
          />
        ) : (
          <ul className="divide-y rounded-lg border">
            {items.map((item) => (
              <ItemRow
                key={item.id}
                item={item}
                onOpen={() => (item.type === 'folder' ? onOpenFolder(item.id) : onPreviewFile(item.id))}
              />
            ))}
          </ul>
        )}
      </CardContent>
      <FilePreviewDialog
        file={
          previewed
            ? {
                id: previewed.id,
                name: previewed.name,
                size: previewed.size ?? null,
                modifiedAt: previewed.modified_at,
              }
            : null
        }
        onClose={() => onPreviewFile(null)}
        onPrevious={stepTo(files[previewedIndex - 1])}
        onNext={stepTo(files[previewedIndex + 1])}
      />
    </Card>
  )
}

/** A folder (click to open) or a file (click to preview, with a download button). */
function ItemRow({ item, onOpen }: { item: BoxItem; onOpen: () => void }) {
  const details = [
    item.size != null && item.type === 'file' ? formatBytes(item.size) : null,
    item.modified_at ? `updated ${formatRelative(item.modified_at)}` : null,
  ].filter(Boolean)

  return (
    <li className="flex items-center hover:bg-muted/50">
      <button
        type="button"
        className="flex min-w-0 flex-1 items-center gap-2 px-3 py-2.5 text-left text-sm"
        onClick={onOpen}
      >
        {item.type === 'folder' ? (
          <Folder className="size-4 shrink-0 text-amber-500" aria-hidden />
        ) : (
          <FileText className="size-4 shrink-0 text-muted-foreground" aria-hidden />
        )}
        <span className="flex min-w-0 flex-1 flex-col gap-0.5 sm:flex-row sm:items-center sm:gap-2">
          <span className="truncate font-medium">{item.name}</span>
          <span className="text-xs text-muted-foreground sm:ml-auto sm:shrink-0">
            {details.join(' · ')}
          </span>
        </span>
      </button>
      {item.type === 'file' && (
        <a
          href={fileDownloadUrl(item.id, { name: item.name })}
          download={item.name}
          className={buttonVariants({ variant: 'ghost', size: 'icon', className: 'mr-1 text-muted-foreground' })}
          aria-label={`Download ${item.name}`}
          title="Download"
        >
          <Download aria-hidden />
        </a>
      )}
    </li>
  )
}

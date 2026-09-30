import { Download, FileText, Folder, FolderOpen, Upload } from 'lucide-react'
import { Link, useSearchParams } from 'react-router'

import { fileDownloadUrl } from '@/api/client'
import { useFolder } from '@/api/queries'
import type { BoxItem } from '@/api/types'
import { PageHeader } from '@/components/AppShell'
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
        <FolderContents folderId={folderId} onOpenFolder={openFolder} />
      </div>
    </>
  )
}

function FolderContents({
  folderId,
  onOpenFolder,
}: {
  folderId?: string
  onOpenFolder: (id: string) => void
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
              <ItemRow key={item.id} item={item} onOpenFolder={onOpenFolder} />
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}

function ItemRow({ item, onOpenFolder }: { item: BoxItem; onOpenFolder: (id: string) => void }) {
  const details = [
    item.size != null && item.type === 'file' ? formatBytes(item.size) : null,
    item.modified_at ? `updated ${formatRelative(item.modified_at)}` : null,
  ].filter(Boolean)

  const label = (
    <>
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
    </>
  )

  return (
    <li>
      {item.type === 'folder' ? (
        <button
          type="button"
          className="flex w-full items-center gap-2 px-3 py-2.5 text-left text-sm hover:bg-muted/50"
          onClick={() => onOpenFolder(item.id)}
        >
          {label}
        </button>
      ) : (
        <a
          href={fileDownloadUrl(item.id)}
          download
          className="group flex items-center gap-2 px-3 py-2.5 text-sm hover:bg-muted/50"
        >
          {label}
          <Download
            className="size-4 shrink-0 text-muted-foreground opacity-0 group-hover:opacity-100"
            aria-label="Download"
          />
        </a>
      )}
    </li>
  )
}

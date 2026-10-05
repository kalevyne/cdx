import { Download, FileQuestion, FileWarning, type LucideIcon } from 'lucide-react'
import { lazy, Suspense, useCallback, useMemo } from 'react'

import { ApiError, fileDownloadUrl } from '@/api/client'
import { type PreviewSource, useFilePreview } from '@/api/queries'
import { EmptyState, ErrorState, LoadingRows } from '@/components/StateViews'
import { buttonVariants } from '@/components/ui/button'
import { formatBytes } from '@/lib/format'
import { decodeText, imageMimeType, maxPreviewBytes, type PreviewKind, previewKind } from '@/lib/preview'

// Markdown and CSV parsing are only loaded when a file of that kind is opened.
const MarkdownPreview = lazy(() => import('@/components/preview/MarkdownPreview'))
const TablePreview = lazy(() => import('@/components/preview/TablePreview'))

export interface PreviewFile extends PreviewSource {
  name: string
  size: number | null
}

/** Shows a Box file's content in the app, or says why it can't (unsupported
 * type, too large) and offers the download instead. Files that can't be shown
 * are never fetched. */
export function FilePreview({ file }: { file: PreviewFile }) {
  const kind = previewKind(file.name)
  if (!kind) {
    return (
      <NoPreview
        file={file}
        icon={FileQuestion}
        title="No preview for this type of file"
        description="Download it to open it in its own app."
      />
    )
  }
  if (file.size != null && file.size > maxPreviewBytes(kind)) return <TooLarge file={file} kind={kind} />
  return <LoadedPreview file={file} kind={kind} />
}

function LoadedPreview({ file, kind }: { file: PreviewFile; kind: PreviewKind }) {
  const preview = useFilePreview(file)

  if (preview.isPending) {
    return (
      <div className="p-6">
        <LoadingRows rows={6} />
      </div>
    )
  }
  if (preview.isError) {
    if (preview.error instanceof ApiError && preview.error.status === 413) {
      return <TooLarge file={file} kind={kind} />
    }
    return (
      <div className="p-6">
        <ErrorState error={preview.error} title="Couldn't load the preview" />
      </div>
    )
  }

  const bytes = preview.data
  if (kind === 'image') return <ImagePreview bytes={bytes} name={file.name} />
  if (kind === 'pdf') return <PdfPreview bytes={bytes} name={file.name} />
  return <TextPreview bytes={bytes} kind={kind} file={file} />
}

function ImagePreview({ bytes, name }: { bytes: ArrayBuffer; name: string }) {
  // As an <img>, an SVG can't run scripts or load anything external.
  const showBytes = useObjectUrl(bytes, imageMimeType(name))
  return (
    <div className="flex min-h-full items-center justify-center bg-muted/40 p-6">
      <img ref={showBytes} alt={name} className="max-h-full max-w-full rounded border bg-background" />
    </div>
  )
}

function PdfPreview({ bytes, name }: { bytes: ArrayBuffer; name: string }) {
  const showBytes = useObjectUrl(bytes, 'application/pdf')
  return <iframe ref={showBytes} title={name} className="block size-full" />
}

function TextPreview({
  bytes,
  kind,
  file,
}: {
  bytes: ArrayBuffer
  kind: PreviewKind
  file: PreviewFile
}) {
  const text = useMemo(() => decodeText(bytes), [bytes])

  if (text === null) {
    return (
      <NoPreview
        file={file}
        icon={FileQuestion}
        title="This file isn't text"
        description="Its name says it is, but its content is binary. Download it to open it."
      />
    )
  }
  if (!text.trim()) {
    return <p className="p-6 text-sm text-muted-foreground">This file is empty.</p>
  }
  if (kind === 'text') {
    return <pre className="min-w-max p-6 font-mono text-xs leading-relaxed [tab-size:4]">{text}</pre>
  }
  return (
    <Suspense
      fallback={
        <div className="p-6">
          <LoadingRows rows={6} />
        </div>
      }
    >
      {kind === 'markdown' ? <MarkdownPreview text={text} /> : <TablePreview text={text} />}
    </Suspense>
  )
}

function TooLarge({ file, kind }: { file: PreviewFile; kind: PreviewKind }) {
  const limit = formatBytes(maxPreviewBytes(kind))
  return (
    <NoPreview
      file={file}
      icon={FileWarning}
      title="This file is too large to preview"
      description={
        file.size != null
          ? `It's ${formatBytes(file.size)}; previews of this type of file stop at ${limit}. Download it to view it.`
          : `Previews of this type of file stop at ${limit}. Download it to view it.`
      }
    />
  )
}

function NoPreview({
  file,
  icon,
  title,
  description,
}: {
  file: PreviewFile
  icon: LucideIcon
  title: string
  description: string
}) {
  return (
    <div className="p-6">
      <EmptyState
        icon={icon}
        title={title}
        description={description}
        action={
          <a
            href={fileDownloadUrl(file.id, file)}
            download={file.name}
            className={buttonVariants({ variant: 'outline' })}
          >
            <Download aria-hidden />
            Download
          </a>
        }
      />
    </div>
  )
}

/** A ref that points an <img>/<iframe> at file bytes through a temporary
 * same-page URL, typed so the browser's own viewer (image, PDF) handles them.
 * The URL is released when the element goes away. */
function useObjectUrl(bytes: ArrayBuffer, type: string) {
  return useCallback(
    (element: HTMLImageElement | HTMLIFrameElement | null) => {
      if (!element) return
      const url = URL.createObjectURL(new Blob([bytes], { type }))
      element.src = url
      return () => URL.revokeObjectURL(url)
    },
    [bytes, type],
  )
}

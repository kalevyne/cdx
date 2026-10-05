import { ChevronLeft, ChevronRight, Download, X } from 'lucide-react'
import { useState } from 'react'

import { fileDownloadUrl } from '@/api/client'
import { FilePreview, type PreviewFile } from '@/components/FilePreview'
import { Button, buttonVariants } from '@/components/ui/button'
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogTitle } from '@/components/ui/dialog'
import { formatBytes } from '@/lib/format'

interface FilePreviewDialogProps {
  /** The file to show; null closes the dialog. */
  file: PreviewFile | null
  onClose: () => void
  /** Step to the neighbouring file, when the file is one of a list. */
  onPrevious?: () => void
  onNext?: () => void
}

export function FilePreviewDialog({ file, onClose, onPrevious, onNext }: FilePreviewDialogProps) {
  // Keep showing the last file while the dialog animates closed.
  const [shown, setShown] = useState(file)
  if (file && file !== shown) setShown(file)

  return (
    <Dialog open={file !== null} onOpenChange={(open) => !open && onClose()}>
      {shown && (
        <DialogContent
          showCloseButton={false}
          className="flex h-[min(52rem,calc(100dvh-2rem))] flex-col gap-0 overflow-hidden p-0 sm:max-w-5xl"
        >
          <div className="flex items-center gap-2 border-b px-4 py-3">
            <div className="flex min-w-0 flex-1 flex-col gap-1">
              <DialogTitle className="truncate leading-tight">{shown.name}</DialogTitle>
              <DialogDescription className="text-xs">
                {[
                  shown.size != null ? formatBytes(shown.size) : null,
                  shown.versionId ? 'The version recorded by this commit' : null,
                ]
                  .filter(Boolean)
                  .join(' · ') || 'File preview'}
              </DialogDescription>
            </div>
            {(onPrevious || onNext) && (
              <div className="flex">
                <Button variant="ghost" size="icon" onClick={onPrevious} disabled={!onPrevious} aria-label="Previous file">
                  <ChevronLeft />
                </Button>
                <Button variant="ghost" size="icon" onClick={onNext} disabled={!onNext} aria-label="Next file">
                  <ChevronRight />
                </Button>
              </div>
            )}
            <a
              href={fileDownloadUrl(shown.id, shown)}
              download={shown.name}
              className={buttonVariants({ variant: 'outline' })}
            >
              <Download aria-hidden />
              Download
            </a>
            <DialogClose render={<Button variant="ghost" size="icon" aria-label="Close preview" />}>
              <X />
            </DialogClose>
          </div>
          <div className="min-h-0 flex-1 overflow-auto">
            {/* Keyed so each file starts from a clean viewer, scrolled to the top. */}
            <FilePreview key={`${shown.id}:${shown.versionId ?? ''}`} file={shown} />
          </div>
        </DialogContent>
      )}
    </Dialog>
  )
}

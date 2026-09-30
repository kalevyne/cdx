import { AlertTriangle, CheckCircle2, Upload } from 'lucide-react'
import { type FormEvent, useState } from 'react'
import { Link, useSearchParams } from 'react-router'

import { useCdxCommit, useCreateCdxCommit, useFolder } from '@/api/queries'
import { type CdxCommit, MAX_UPLOAD_BYTES } from '@/api/types'
import { AnchorStatusBadge } from '@/components/AnchorStatusBadge'
import { PageHeader } from '@/components/AppShell'
import { FileDrop } from '@/components/FileDrop'
import { FolderBreadcrumb } from '@/components/FolderBreadcrumb'
import { FolderTree } from '@/components/FolderTree'
import { HashText } from '@/components/HashText'
import { LedgerLink } from '@/components/LedgerLink'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button, buttonVariants } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label, Textarea } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { formatBytes } from '@/lib/format'

export function CommitPage() {
  const [params, setParams] = useSearchParams()
  const folderId = params.get('folder') ?? undefined
  const createCommit = useCreateCdxCommit()
  const [file, setFile] = useState<File | null>(null)
  const [designReview, setDesignReview] = useState<File | null>(null)
  const [message, setMessage] = useState('')
  const [formError, setFormError] = useState<string | null>(null)

  function reset() {
    createCommit.reset()
    setFile(null)
    setDesignReview(null)
    setMessage('')
    setFormError(null)
  }

  function submit(event: FormEvent) {
    event.preventDefault()
    const problem = validate({ folderId, file, designReview, message })
    setFormError(problem)
    if (problem || !folderId || !file) return
    createCommit.mutate({ folderId, file, designReview, message })
  }

  if (createCommit.isSuccess) {
    return <CommitSuccess cdxCommit={createCommit.data} onCommitAnother={reset} />
  }

  const error = formError ?? createCommit.error?.message

  return (
    <>
      <PageHeader
        title="Commit a file"
        description="Upload your work to Box with a message. CDX fingerprints it (SHA-256) so the exact version can be proven later."
      />
      <div className="grid items-start gap-6 lg:grid-cols-[20rem_minmax(0,1fr)]">
        <Card>
          <CardHeader>
            <CardTitle>1. Choose a folder</CardTitle>
            <CardDescription>Usually your subsystem's CAD or documents folder.</CardDescription>
          </CardHeader>
          <CardContent className="px-2">
            <FolderTree selectedId={folderId} onSelect={(folder) => setParams({ folder: folder.id })} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>2. Describe the change</CardTitle>
            <SelectedFolder folderId={folderId} />
          </CardHeader>
          <CardContent>
            <form onSubmit={submit} className="flex flex-col gap-5">
              <div className="flex flex-col gap-2">
                <Label htmlFor="commit-file">File</Label>
                <FileDrop id="commit-file" file={file} onChange={setFile} prompt="Choose the file to commit" />
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="commit-message">Commit message</Label>
                <Textarea
                  id="commit-message"
                  value={message}
                  onChange={(event) => setMessage(event.target.value)}
                  placeholder="What changed and why? e.g. “Moved cell tabs 2 mm inboard after thermal review”"
                  rows={4}
                />
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="commit-design-review">
                  Design review <span className="font-normal text-muted-foreground">(optional)</span>
                </Label>
                <FileDrop
                  id="commit-design-review"
                  file={designReview}
                  onChange={setDesignReview}
                  prompt="Attach a design review document"
                />
              </div>

              {error && (
                <Alert variant="destructive">
                  <AlertTriangle aria-hidden />
                  <AlertTitle>Couldn't commit</AlertTitle>
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <Button type="submit" size="lg" disabled={createCommit.isPending} className="self-start">
                <Upload aria-hidden />
                {createCommit.isPending ? 'Uploading…' : 'Commit to Box'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </>
  )
}

function validate({
  folderId,
  file,
  designReview,
  message,
}: {
  folderId?: string
  file: File | null
  designReview: File | null
  message: string
}): string | null {
  if (!folderId) return 'Choose a folder to commit into.'
  if (!file) return 'Choose a file to commit.'
  if (!message.trim()) return 'Write a commit message so teammates know what changed.'
  const tooLarge = [file, designReview].find((f) => f && f.size > MAX_UPLOAD_BYTES)
  if (tooLarge) return `${tooLarge.name} is larger than ${formatBytes(MAX_UPLOAD_BYTES)}.`
  return null
}

function SelectedFolder({ folderId }: { folderId?: string }) {
  const folder = useFolder(folderId, { enabled: Boolean(folderId) })

  if (!folderId) return <CardDescription>No folder chosen yet.</CardDescription>
  if (folder.isPending) return <Skeleton className="h-5 w-48" />
  if (folder.isError) return <CardDescription>Couldn't load that folder.</CardDescription>
  return (
    <FolderBreadcrumb path={[...folder.data.path, { id: folder.data.id, name: folder.data.name }]} />
  )
}

function CommitSuccess({
  cdxCommit,
  onCommitAnother,
}: {
  cdxCommit: CdxCommit
  onCommitAnother: () => void
}) {
  // Live anchoring status: the commit is saved before it reaches the ledger.
  const live = useCdxCommit(cdxCommit.id).data ?? cdxCommit

  return (
    <Card className="mx-auto max-w-xl">
      <CardHeader className="items-center text-center">
        <CheckCircle2 className="size-10 text-emerald-600" aria-hidden />
        <CardTitle className="text-xl">Committed {live.file_name}</CardTitle>
        <CardDescription>
          It's in Box, and its fingerprint is on its way to the public XRP Ledger.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <span className="text-xs font-medium text-muted-foreground uppercase">SHA-256</span>
          <HashText hash={live.sha256_hash} />
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span className="text-muted-foreground">XRP Ledger:</span>
          <AnchorStatusBadge status={live.anchor_status} />
          <LedgerLink cdxCommit={live} />
        </div>
        <div className="flex flex-wrap gap-2">
          <Link to={`/commits/${live.id}`} className={buttonVariants()}>
            View proof
          </Link>
          <Button variant="outline" onClick={onCommitAnother}>
            Commit another file
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

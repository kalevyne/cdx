// The one place the frontend talks HTTP. All requests go to the same origin
// under /api (proxied to the backend in dev and in render.yaml), so the
// session cookie is always first-party.

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, { credentials: 'same-origin', ...init })
  if (!response.ok) {
    throw new ApiError(response.status, await errorMessage(response))
  }
  return (response.status === 204 ? undefined : await response.json()) as T
}

/** Full-page navigation to the backend's Box login redirect. */
export function startLogin(): void {
  window.location.assign('/api/auth/login')
}

/** Download URL for a Box file — a specific version when `versionId` is given. */
export function fileDownloadUrl(fileId: string, versionId?: string | null): string {
  const url = `/api/files/${encodeURIComponent(fileId)}/content`
  return versionId ? `${url}?version_id=${encodeURIComponent(versionId)}` : url
}

// FastAPI errors are {"detail": "..."} or, for validation errors,
// {"detail": [{"msg": "...", ...}]}.
async function errorMessage(response: Response): Promise<string> {
  try {
    const { detail } = await response.json()
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) return detail.map((d) => d.msg).join('; ')
  } catch {
    // Not JSON — fall through to the status text.
  }
  return response.statusText || `Request failed (${response.status})`
}

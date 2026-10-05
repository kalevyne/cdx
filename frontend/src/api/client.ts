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
  const response = await request(path, init)
  return (response.status === 204 ? undefined : await response.json()) as T
}

/** A response body as raw bytes — file content for the in-app preview. */
export async function apiFetchBytes(path: string, init?: RequestInit): Promise<ArrayBuffer> {
  return (await request(path, init)).arrayBuffer()
}

async function request(path: string, init?: RequestInit): Promise<Response> {
  const response = await fetch(path, { credentials: 'same-origin', ...init })
  if (!response.ok) {
    throw new ApiError(response.status, await errorMessage(response))
  }
  return response
}

const RETURN_TO_KEY = 'cdx:return-to'

/** Full-page navigation to the backend's Box login redirect. The current page
 * is remembered so a shared link (e.g. a commit's proof) survives logging in. */
export function startLogin(): void {
  const params = new URLSearchParams(window.location.search)
  params.delete('login_error') // don't carry a previous failure back after success
  const query = params.toString()
  try {
    sessionStorage.setItem(RETURN_TO_KEY, window.location.pathname + (query ? `?${query}` : ''))
  } catch {
    // Storage unavailable (private mode): the user just lands on the dashboard.
  }
  window.location.assign('/api/auth/login')
}

/** The page to return to after login, if one was saved; clears it. */
export function takeLoginReturnPath(): string | null {
  try {
    const path = sessionStorage.getItem(RETURN_TO_KEY)
    sessionStorage.removeItem(RETURN_TO_KEY)
    return path
  } catch {
    return null
  }
}

/** Download URL for a Box file — a specific version when `versionId` is given.
 * `name` goes on the end of the URL so the saved file gets its real name even
 * in browsers that name downloads after the URL. */
export function fileDownloadUrl(
  fileId: string,
  { name, versionId }: { name?: string; versionId?: string | null } = {},
): string {
  const url = `/api/files/${encodeURIComponent(fileId)}/content`
  return withVersion(name ? `${url}/${encodeURIComponent(name)}` : url, versionId)
}

/** URL of a Box file's bytes for the in-app preview (size-capped by the server). */
export function filePreviewUrl(fileId: string, versionId?: string | null): string {
  return withVersion(`/api/files/${encodeURIComponent(fileId)}/preview`, versionId)
}

function withVersion(url: string, versionId?: string | null): string {
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

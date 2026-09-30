// React Query hooks over the API. Components use these, never apiFetch directly,
// so caching, invalidation and query keys live in one file.
import {
  QueryCache,
  QueryClient,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'

import { ApiError, apiFetch } from './client'
import type {
  BoxFolderListing,
  CdxCommit,
  CdxCommitVerification,
  PublicSummary,
  ServerStatus,
  SessionUser,
  SubsystemSummary,
  SubsystemUpdate,
} from './types'

// How often to re-check a commit whose XRPL anchoring is still in flight.
const ANCHOR_POLL_MS = 3_000

export const queryKeys = {
  me: ['me'] as const,
  folder: (folderId?: string) => ['folder', folderId ?? 'root'] as const,
  cdxCommits: (filters: CdxCommitFilters = {}) => ['cdx-commits', filters] as const,
  cdxCommit: (id: number) => ['cdx-commit', id] as const,
  verification: (id: number) => ['cdx-commit', id, 'verification'] as const,
  subsystems: ['subsystems'] as const,
  publicSummary: ['public-summary'] as const,
  serverStatus: ['server-status'] as const,
}

export function createQueryClient(): QueryClient {
  const client: QueryClient = new QueryClient({
    queryCache: new QueryCache({
      // An expired session anywhere sends the app back to the login screen.
      onError: (error) => {
        if (error instanceof ApiError && error.status === 401) {
          client.setQueryData(queryKeys.me, null)
        }
      },
    }),
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        retry: (failureCount, error) =>
          !(error instanceof ApiError && error.status < 500) && failureCount < 2,
      },
    },
  })
  return client
}

/** The logged-in engineer, or null when nobody is logged in. */
export function useCurrentUser() {
  return useQuery({
    queryKey: queryKeys.me,
    queryFn: async () => {
      try {
        return await apiFetch<SessionUser>('/api/auth/me')
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) return null
        throw error
      }
    },
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => apiFetch<void>('/api/auth/logout', { method: 'POST' }),
    onSuccess: () => {
      queryClient.clear()
      queryClient.setQueryData(queryKeys.me, null)
    },
  })
}

/** A Box folder's contents; the Dashboard root when `folderId` is omitted. */
export function useFolder(folderId?: string, options: { enabled?: boolean } = {}) {
  return useQuery({
    queryKey: queryKeys.folder(folderId),
    queryFn: () =>
      apiFetch<BoxFolderListing>(
        folderId ? `/api/folders/${encodeURIComponent(folderId)}` : '/api/folders',
      ),
    ...options,
  })
}

export interface CdxCommitFilters {
  subsystem?: string
  limit?: number
}

export function useCdxCommits(filters: CdxCommitFilters = {}) {
  const pollInterval = useAnchorPolling()
  return useQuery({
    queryKey: queryKeys.cdxCommits(filters),
    queryFn: () => {
      const params = new URLSearchParams()
      if (filters.subsystem) params.set('subsystem', filters.subsystem)
      if (filters.limit) params.set('limit', String(filters.limit))
      return apiFetch<CdxCommit[]>(`/api/cdx-commits?${params}`)
    },
    refetchInterval: (query) =>
      pollInterval(Boolean(query.state.data?.some((c) => c.anchor_status === 'pending'))),
  })
}

/** Whether this server can anchor to XRPL (public, cached for the session). */
export function useServerStatus() {
  return useQuery({
    queryKey: queryKeys.serverStatus,
    queryFn: () => apiFetch<ServerStatus>('/api/status'),
    staleTime: Infinity,
  })
}

/** Poll interval for queries showing pending commits: poll only while
 * something is pending and the server can actually anchor it. */
function useAnchorPolling() {
  const anchoringEnabled = useServerStatus().data?.anchoring_enabled !== false
  return (anyPending: boolean) => (anyPending && anchoringEnabled ? ANCHOR_POLL_MS : false)
}

/** One CDX commit; polls while its anchoring is pending so the UI updates live. */
export function useCdxCommit(id: number) {
  const pollInterval = useAnchorPolling()
  return useQuery({
    queryKey: queryKeys.cdxCommit(id),
    queryFn: () => apiFetch<CdxCommit>(`/api/cdx-commits/${id}`),
    refetchInterval: (query) => pollInterval(query.state.data?.anchor_status === 'pending'),
  })
}

export function useRetryAnchoring(id: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => apiFetch<CdxCommit>(`/api/cdx-commits/${id}/anchor`, { method: 'POST' }),
    onSuccess: (cdxCommit) => {
      queryClient.setQueryData(queryKeys.cdxCommit(id), cdxCommit)
      queryClient.invalidateQueries({ queryKey: ['cdx-commits'] })
    },
  })
}

/** Re-check a commit against Box and the ledger. Runs only when `enabled`
 * (i.e. after the user asks), since it downloads the file. */
export function useVerification(id: number, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.verification(id),
    queryFn: () => apiFetch<CdxCommitVerification>(`/api/cdx-commits/${id}/verification`),
    enabled,
    staleTime: 0,
  })
}

export interface NewCdxCommit {
  folderId: string
  message: string
  file: File
  designReview?: File | null
}

export function useCreateCdxCommit() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ folderId, message, file, designReview }: NewCdxCommit) => {
      const body = new FormData()
      body.set('folder_id', folderId)
      body.set('message', message)
      body.set('file', file)
      if (designReview) body.set('design_review', designReview)
      return apiFetch<CdxCommit>('/api/cdx-commits', { method: 'POST', body })
    },
    onSuccess: (cdxCommit) => {
      queryClient.invalidateQueries({ queryKey: ['cdx-commits'] })
      queryClient.invalidateQueries({ queryKey: ['folder'] })
      queryClient.invalidateQueries({ queryKey: queryKeys.subsystems })
      queryClient.invalidateQueries({ queryKey: queryKeys.publicSummary })
      queryClient.setQueryData(queryKeys.cdxCommit(cdxCommit.id), cdxCommit)
    },
  })
}

/** Every subsystem's dashboard card, in the backend's canonical order. */
export function useSubsystems() {
  return useQuery({
    queryKey: queryKeys.subsystems,
    queryFn: () => apiFetch<SubsystemSummary[]>('/api/subsystems'),
  })
}

/** Display name for a subsystem slug ("battery" → "Battery"). */
export function useSubsystemName(slug: string | null | undefined): string | null {
  const { data } = useSubsystems()
  return data?.find((s) => s.slug === slug)?.name ?? null
}

export function useUpdateSubsystem(slug: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (update: SubsystemUpdate) =>
      apiFetch<SubsystemSummary>(`/api/subsystems/${encodeURIComponent(slug)}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(update),
      }),
    onSuccess: (updated) => {
      queryClient.setQueryData<SubsystemSummary[]>(queryKeys.subsystems, (cards) =>
        cards?.map((card) => (card.slug === updated.slug ? updated : card)),
      )
      queryClient.invalidateQueries({ queryKey: queryKeys.publicSummary })
    },
  })
}

/** The public sponsor summary — works without logging in. */
export function usePublicSummary() {
  return useQuery({
    queryKey: queryKeys.publicSummary,
    queryFn: () => apiFetch<PublicSummary>('/api/public/summary'),
  })
}

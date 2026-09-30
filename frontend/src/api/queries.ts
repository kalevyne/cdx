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
import type { BoxFolderListing, CdxCommit, SessionUser } from './types'

export const queryKeys = {
  me: ['me'] as const,
  folder: (folderId?: string) => ['folder', folderId ?? 'root'] as const,
  cdxCommits: (filters: CdxCommitFilters = {}) => ['cdx-commits', filters] as const,
  cdxCommit: (id: number) => ['cdx-commit', id] as const,
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
  return useQuery({
    queryKey: queryKeys.cdxCommits(filters),
    queryFn: () => {
      const params = new URLSearchParams()
      if (filters.subsystem) params.set('subsystem', filters.subsystem)
      if (filters.limit) params.set('limit', String(filters.limit))
      return apiFetch<CdxCommit[]>(`/api/cdx-commits?${params}`)
    },
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
      queryClient.setQueryData(queryKeys.cdxCommit(cdxCommit.id), cdxCommit)
    },
  })
}

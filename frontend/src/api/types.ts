// Friendly names for the backend's API types. The shapes themselves are
// generated from the backend (see schema.d.ts / `npm run gen:api`) — never
// redeclare them by hand here.
import type { components } from './schema'

type Schemas = components['schemas']

export type SessionUser = Schemas['SessionUser']
export type BoxItem = Schemas['BoxItem']
export type BoxFolderRef = Schemas['BoxFolderRef']
export type BoxFolderListing = Schemas['BoxFolderListing']
export type CdxCommit = Schemas['CdxCommitRead']

// Mirrors MAX_UPLOAD_BYTES in backend/app/services/cdx_commits.py (Box's
// single-upload limit), so oversized files are caught before uploading.
export const MAX_UPLOAD_BYTES = 50 * 1024 * 1024

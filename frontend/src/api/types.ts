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
export type AnchorStatus = Schemas['AnchorStatus']
export type CdxCommitVerification = Schemas['CdxCommitVerification']
export type VerificationCheck = Schemas['VerificationCheck']
export type SubsystemStage = Schemas['SubsystemStage']
export type SubsystemSummary = Schemas['SubsystemSummary']
export type SubsystemUpdate = Schemas['SubsystemUpdate']
export type SubsystemOverview = Schemas['SubsystemOverview']
export type PublicSummary = Schemas['PublicSummary']
export type PublicCdxCommit = Schemas['PublicCdxCommit']
export type ServerStatus = Schemas['ServerStatus']

// Mirrors MAX_UPLOAD_BYTES in backend/app/services/cdx_commits.py (Box's
// single-upload limit), so oversized files are caught before uploading.
export const MAX_UPLOAD_BYTES = 50 * 1024 * 1024

// Mirrors MAX_PREVIEW_BYTES in backend/app/services/file_downloads.py: the
// server refuses to relay anything bigger for a preview, so don't ask.
export const MAX_PREVIEW_BYTES = 20 * 1024 * 1024

// Which files the in-app preview can show, and how to read their bytes.
import { MAX_PREVIEW_BYTES } from '@/api/types'

export type PreviewKind = 'image' | 'pdf' | 'markdown' | 'table' | 'text'

const IMAGE_TYPES: Record<string, string> = {
  png: 'image/png',
  jpg: 'image/jpeg',
  jpeg: 'image/jpeg',
  gif: 'image/gif',
  webp: 'image/webp',
  avif: 'image/avif',
  bmp: 'image/bmp',
  svg: 'image/svg+xml',
}

// Shown as plain text. HTML is on this list on purpose: uploaded HTML is only
// ever displayed as source, never rendered.
const TEXT_EXTENSIONS = new Set(
  (
    'txt log json jsonl yaml yml toml ini cfg conf xml html htm css ' +
    'c h cpp hpp cc ino py m js jsx ts tsx rs go java kt sh bat ps1 sql tex bib ' +
    'gcode nc dbc ld s asm cmake mk gitignore'
  ).split(' '),
)

// Text is rendered into the page in one piece, which gets slow long before the
// server's cap; PDFs and images are handed to the browser's own viewers.
const MAX_TEXT_PREVIEW_BYTES = 2 * 1024 * 1024

function extension(fileName: string): string {
  const dot = fileName.lastIndexOf('.')
  return dot < 0 ? '' : fileName.slice(dot + 1).toLowerCase()
}

/** How to preview a file, judged by its name; null if it can't be previewed. */
export function previewKind(fileName: string): PreviewKind | null {
  const ext = extension(fileName)
  if (ext in IMAGE_TYPES) return 'image'
  if (ext === 'pdf') return 'pdf'
  if (ext === 'md' || ext === 'markdown') return 'markdown'
  if (ext === 'csv' || ext === 'tsv') return 'table'
  return TEXT_EXTENSIONS.has(ext) ? 'text' : null
}

/** The largest file of this kind the preview will load. */
export function maxPreviewBytes(kind: PreviewKind): number {
  return kind === 'image' || kind === 'pdf' ? MAX_PREVIEW_BYTES : MAX_TEXT_PREVIEW_BYTES
}

export function imageMimeType(fileName: string): string {
  return IMAGE_TYPES[extension(fileName)]
}

/** Decode a text file's bytes: UTF-8 unless it starts with a UTF-16 byte-order
 * mark (Excel's "Unicode Text" export). Null if it doesn't look like text. */
export function decodeText(bytes: ArrayBuffer): string | null {
  const [first, second] = new Uint8Array(bytes, 0, Math.min(2, bytes.byteLength))
  const encoding =
    first === 0xff && second === 0xfe ? 'utf-16le' : first === 0xfe && second === 0xff ? 'utf-16be' : 'utf-8'
  const text = new TextDecoder(encoding).decode(bytes)
  return text.includes('\0') ? null : text
}

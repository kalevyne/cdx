"""Relaying Box file content to the browser: downloads and in-app previews.

The bytes come from Box on every request (CDX stores no file content) and pass
through this server on the way to the browser, so three things keep a busy day
from hurting it:

* content is streamed in chunks, never held in memory whole;
* at most `MAX_CONCURRENT_DOWNLOADS` are relayed at once — the rest are turned
  away immediately rather than piling up on the worker threads every other
  route shares;
* a browser that already has the content (matching ETag) gets a 304 after one
  Box metadata call, with no download at all.

Previews additionally refuse files over `MAX_PREVIEW_BYTES`.
"""

import threading
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from functools import lru_cache

from app.config import get_settings
from app.schemas.box import BoxFileMetadata
from app.services.box_client import BoxService

# Hard cap on what the preview endpoint will relay. Uploads are limited to
# 50 MB today (cdx_commits.MAX_UPLOAD_BYTES), but that limit goes away with
# chunked uploads; this one stays, so "click a file to look at it" can never
# mean pulling a multi-gigabyte CAD file through the server. 20 MB covers the
# formats the frontend can actually render (PDFs, images, text, CSV).
MAX_PREVIEW_BYTES = 20 * 1024 * 1024


class PreviewTooLargeError(Exception):
    pass


class DownloadsBusyError(Exception):
    pass


class DownloadSlots:
    """Counts the downloads currently being relayed from Box."""

    def __init__(self, limit: int) -> None:
        self._semaphore = threading.BoundedSemaphore(limit)

    def acquire(self) -> None:
        if not self._semaphore.acquire(blocking=False):
            raise DownloadsBusyError(
                "The server is busy with other downloads; try again in a moment"
            )

    def release(self) -> None:
        self._semaphore.release()


@lru_cache
def get_download_slots() -> DownloadSlots:
    return DownloadSlots(get_settings().max_concurrent_downloads)


class DownloadBody:
    """A file's content as an iterator of chunks, holding one download slot
    until it is exhausted, fails, or is dropped (e.g. the browser went away)."""

    def __init__(
        self, chunks: Iterator[bytes], release: Callable[[], None], max_bytes: int | None
    ) -> None:
        self._chunks = chunks
        self._release = release
        self._max_bytes = max_bytes
        self._sent = 0
        self._closed = False

    def __iter__(self) -> "DownloadBody":
        return self

    def __next__(self) -> bytes:
        try:
            chunk = next(self._chunks)
            self._sent += len(chunk)
            # Only reachable for a pinned older version that is bigger than the
            # current one `open_download` checked; cuts the response short.
            if self._max_bytes is not None and self._sent > self._max_bytes:
                raise PreviewTooLargeError("File is too large to preview")
        except BaseException:
            self.close()
            raise
        return chunk

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self._release()

    # Safety net: a response that never gets iterated must not leak its slot.
    __del__ = close


@dataclass(frozen=True)
class FileDownload:
    metadata: BoxFileMetadata
    # Identifies this exact content, for browser cache revalidation.
    etag: str | None
    # None when the browser's cached copy (`cached_etags`) is still current.
    body: DownloadBody | None


def open_download(
    box: BoxService,
    slots: DownloadSlots,
    file_id: str,
    version_id: str | None = None,
    *,
    max_bytes: int | None = None,
    cached_etags: frozenset[str] = frozenset(),
) -> FileDownload:
    """Start relaying a file's current content, or a specific earlier version.
    `max_bytes` refuses larger files with PreviewTooLargeError."""
    metadata = box.get_file_metadata(file_id)
    etag = _etag(metadata, version_id)
    if etag in cached_etags:
        return FileDownload(metadata, etag, body=None)

    # Box reports the current version's size; an older version's isn't known
    # until its bytes arrive, so DownloadBody enforces the cap for those.
    is_current = version_id is None or version_id == metadata.version_id
    if max_bytes is not None and is_current and metadata.size > max_bytes:
        raise PreviewTooLargeError(
            f"{metadata.name} is larger than {max_bytes // (1024 * 1024)} MB; "
            "download it to view it"
        )

    slots.acquire()
    try:
        chunks = box.open_file_content(metadata, version_id)
    except BaseException:
        slots.release()
        raise
    return FileDownload(metadata, etag, DownloadBody(chunks, slots.release, max_bytes))


def _etag(metadata: BoxFileMetadata, version_id: str | None) -> str | None:
    # A Box version ID never points at different bytes, so it identifies the content.
    version = version_id or metadata.version_id
    return f'"{version}"' if version else None

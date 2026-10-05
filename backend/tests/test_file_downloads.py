import gc
from unittest.mock import MagicMock

import pytest

from app.schemas.box import BoxFileMetadata
from app.services.file_downloads import (
    DownloadsBusyError,
    DownloadSlots,
    PreviewTooLargeError,
    open_download,
)


def _box(chunks: list[bytes], **metadata) -> MagicMock:
    fields = {"id": "9", "name": "pack.step", "size": 10, "version_id": "v2"}
    box = MagicMock()
    box.get_file_metadata.return_value = BoxFileMetadata(**{**fields, **metadata})
    box.open_file_content.side_effect = lambda file, version_id=None: iter(chunks)
    return box


def _slot_is_free(slots: DownloadSlots) -> bool:
    try:
        slots.acquire()
    except DownloadsBusyError:
        return False
    slots.release()
    return True


def test_download_holds_a_slot_until_the_content_is_read():
    slots = DownloadSlots(limit=1)

    download = open_download(_box([b"ab", b"cd"]), slots, "9")

    assert not _slot_is_free(slots)
    assert b"".join(download.body) == b"abcd"
    assert _slot_is_free(slots)


def test_abandoned_download_gives_its_slot_back():
    slots = DownloadSlots(limit=1)

    download = open_download(_box([b"ab", b"cd"]), slots, "9")
    next(download.body)  # the browser disconnects after the first chunk
    del download
    gc.collect()

    assert _slot_is_free(slots)


def test_download_that_fails_midway_gives_its_slot_back():
    def broken_stream():
        yield b"ab"
        raise ConnectionError("Box hung up")

    slots = DownloadSlots(limit=1)
    box = _box([])
    box.open_file_content.side_effect = lambda file, version_id=None: broken_stream()

    download = open_download(box, slots, "9")
    with pytest.raises(ConnectionError):
        list(download.body)

    assert _slot_is_free(slots)


def test_cached_copy_takes_no_slot_and_no_download():
    slots = DownloadSlots(limit=1)
    box = _box([b"abcd"])
    etag = open_download(box, slots, "9").etag
    box.open_file_content.reset_mock()  # that download was dropped unread, freeing its slot

    download = open_download(box, slots, "9", cached_etags=frozenset({etag}))

    assert download.body is None
    box.open_file_content.assert_not_called()
    assert _slot_is_free(slots)


def test_etag_follows_the_requested_version():
    slots = DownloadSlots(limit=4)
    box = _box([b"abcd"])

    assert open_download(box, slots, "9").etag == '"v2"'
    assert open_download(box, slots, "9", "v1").etag == '"v1"'


def test_oversized_older_version_is_cut_off():
    # Box only reports the current version's size (10 bytes here), so an older,
    # bigger version is caught while its bytes arrive.
    slots = DownloadSlots(limit=1)
    box = _box([b"x" * 8, b"x" * 8, b"x" * 8])

    download = open_download(box, slots, "9", "v1", max_bytes=12)
    with pytest.raises(PreviewTooLargeError):
        list(download.body)

    assert _slot_is_free(slots)

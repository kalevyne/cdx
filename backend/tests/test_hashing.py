import hashlib
from io import BytesIO

from app.services.hashing import sha256_hex_chunks, sha256_hex_file


def test_chunked_hash_matches_whole_content_hash():
    assert sha256_hex_chunks([b"pack-", b"", b"bytes"]) == hashlib.sha256(b"pack-bytes").hexdigest()


def test_file_hash_reads_from_the_start_and_rewinds(monkeypatch):
    monkeypatch.setattr("app.services.hashing._HASH_CHUNK_BYTES", 3)
    file = BytesIO(b"pack-bytes")
    file.seek(4)

    assert sha256_hex_file(file) == hashlib.sha256(b"pack-bytes").hexdigest()
    assert file.tell() == 0

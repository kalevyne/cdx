"""The hashing pipeline: every CDX commit is identified by the SHA-256 of the
exact bytes uploaded. That hex digest is what gets anchored to XRPL, so anyone
holding the file can recompute it and compare against the public ledger.

Committed files can be gigabytes, so hashes are computed over a stream of
pieces rather than the whole file in memory."""

import hashlib
from collections.abc import Iterable
from typing import BinaryIO

# Read size when hashing a file object.
_HASH_CHUNK_BYTES = 1024 * 1024


def sha256_hex(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_hex_chunks(chunks: Iterable[bytes]) -> str:
    digest = hashlib.sha256()
    for chunk in chunks:
        digest.update(chunk)
    return digest.hexdigest()


def sha256_hex_file(file: BinaryIO) -> str:
    """Hash a seekable file object from the start, leaving it rewound."""
    file.seek(0)
    digest = sha256_hex_chunks(iter(lambda: file.read(_HASH_CHUNK_BYTES), b""))
    file.seek(0)
    return digest

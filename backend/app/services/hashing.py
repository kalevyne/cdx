"""The hashing pipeline: every CDX commit is identified by the SHA-256 of the
exact bytes uploaded. That hex digest is what gets anchored to XRPL, so anyone
holding the file can recompute it and compare against the public ledger."""

import hashlib


def sha256_hex(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

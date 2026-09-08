"""Conservative guards for ZIP-based learning materials."""

from __future__ import annotations

import re
import zipfile
from pathlib import PurePosixPath

from extractor.exceptions import ExtractionError

MAX_ARCHIVE_MEMBERS = 10_000
MAX_MEMBER_UNCOMPRESSED_BYTES = 128 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED_BYTES = 2 * 1024 * 1024 * 1024
MAX_COMPRESSION_RATIO = 1_000
MIN_RATIO_CHECK_BYTES = 1024 * 1024
SUPPORTED_COMPRESSION_TYPES = {
    zipfile.ZIP_STORED,
    zipfile.ZIP_DEFLATED,
    zipfile.ZIP_BZIP2,
    zipfile.ZIP_LZMA,
}


class ArchiveSafetyError(ExtractionError):
    """Raised when an archive exceeds conservative safety limits."""


def validate_archive(
    archive: zipfile.ZipFile,
    *,
    max_members: int = MAX_ARCHIVE_MEMBERS,
    max_member_size: int = MAX_MEMBER_UNCOMPRESSED_BYTES,
    max_total_size: int = MAX_TOTAL_UNCOMPRESSED_BYTES,
    max_compression_ratio: int = MAX_COMPRESSION_RATIO,
) -> None:
    """Reject traversal, encryption and decompression-bomb patterns before reads."""
    members = archive.infolist()
    if len(members) > max_members:
        raise ArchiveSafetyError(
            f"Archive contains too many entries ({len(members)} > {max_members})."
        )

    total_size = 0
    for info in members:
        name = info.filename.replace("\\", "/")
        path = PurePosixPath(name)
        if (
            path.is_absolute()
            or name.startswith("//")
            or re.match(r"^[A-Za-z]:", name)
            or ".." in path.parts
        ):
            raise ArchiveSafetyError(f"Archive contains an unsafe path: {info.filename}")
        if info.flag_bits & 0x1:
            raise ArchiveSafetyError(f"Encrypted archive entry is not supported: {info.filename}")
        if info.compress_type not in SUPPORTED_COMPRESSION_TYPES:
            raise ArchiveSafetyError(
                f"Archive entry uses an unsupported compression method: {info.filename}"
            )
        if info.file_size > max_member_size:
            raise ArchiveSafetyError(
                f"Archive entry is too large: {info.filename} ({info.file_size} bytes)."
            )
        total_size += info.file_size
        if total_size > max_total_size:
            raise ArchiveSafetyError(
                f"Archive expands beyond the allowed total size ({max_total_size} bytes)."
            )
        if info.file_size >= MIN_RATIO_CHECK_BYTES:
            ratio = info.file_size / max(info.compress_size, 1)
            if ratio > max_compression_ratio:
                raise ArchiveSafetyError(
                    f"Archive entry has an unsafe compression ratio: {info.filename} ({ratio:.0f}:1)."
                )


def read_member(archive: zipfile.ZipFile, name: str) -> bytes:
    """Read one previously validated member with a second size check."""
    info = archive.getinfo(name)
    if info.file_size > MAX_MEMBER_UNCOMPRESSED_BYTES:
        raise ArchiveSafetyError(
            f"Archive entry is too large: {name} ({info.file_size} bytes)."
        )
    try:
        return archive.read(info)
    except (NotImplementedError, RuntimeError) as exc:
        raise ArchiveSafetyError(f"Could not safely read archive entry: {name}") from exc

#!/usr/bin/env python3
"""Fail CI if an ARM64 APK contains native ELF PT_LOAD segments incompatible with 16 KiB pages."""

import argparse
import struct
import sys
import zipfile
from pathlib import Path

PAGE = 16384
ELF_MAGIC = b"\x7fELF"
AARCH64 = 183


def check_elf(data: bytes, name: str) -> list[str]:
    """Return actionable diagnostics for a native arm64 ELF library."""
    errors = []
    if len(data) < 64 or data[:4] != ELF_MAGIC:
        return [f"{name}: missing/truncated ELF header"]
    if data[4] != 2 or data[5] != 1:
        return [f"{name}: expected little-endian ELF64"]
    machine = struct.unpack_from("<H", data, 18)[0]
    if machine != AARCH64:
        errors.append(f"{name}: expected AArch64 machine=183, found {machine}")
    phoff = struct.unpack_from("<Q", data, 32)[0]
    phentsize = struct.unpack_from("<H", data, 54)[0]
    phnum = struct.unpack_from("<H", data, 56)[0]
    if phnum == 0 or phnum == 0xFFFF or phentsize < 56 or phoff > len(data) or phnum > (len(data) - phoff) // phentsize:
        return errors + [f"{name}: missing/invalid program header table"]
    loads = 0
    for i in range(phnum):
        off = phoff + i * phentsize
        p_type = struct.unpack_from("<I", data, off)[0]
        if p_type != 1:
            continue
        loads += 1
        p_offset, p_vaddr = struct.unpack_from("<QQ", data, off + 8)
        p_align = struct.unpack_from("<Q", data, off + 48)[0]
        if p_align < PAGE or p_align % PAGE != 0 or (p_vaddr - p_offset) % PAGE != 0:
            errors.append(
                f"{name}: PT_LOAD[{i}] offset=0x{p_offset:x} "
                f"vaddr=0x{p_vaddr:x} align=0x{p_align:x} (requires 0x4000)"
            )
    if not loads:
        errors.append(f"{name}: no PT_LOAD segments")
    return errors


def check_apk(apk: Path) -> tuple[int, list[str]]:
    errors = []
    count = 0
    with zipfile.ZipFile(apk) as archive:
        for info in archive.infolist():
            if not info.filename.startswith("lib/arm64-v8a/") or not info.filename.endswith(".so"):
                continue
            count += 1
            errors.extend(check_elf(archive.read(info), info.filename))
    if not count:
        errors.append("APK contains no lib/arm64-v8a/*.so libraries")
    return count, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path, help="ARM64 debug APK to inspect")
    args = parser.parse_args()
    try:
        count, errors = check_apk(args.apk)
    except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
        print(f"APK inspection failed: {exc}", file=sys.stderr)
        return 2
    for err in errors:
        print("FAIL:", err, file=sys.stderr)
    print(f"Checked {count} ARM64 native libraries: {len(errors)} issue(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

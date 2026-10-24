#!/usr/bin/env python3
"""Reject exported debug diagnostic Activities in an assembled APK.

Reads binary AndroidManifest.xml directly; no Android SDK, credentials,
device, or third-party Python packages required.
"""
import argparse
import struct
import sys
import zipfile

XML = 0x0003
STRING_POOL = 0x0001
START_ELEMENT = 0x0102
TYPE_STRING = 0x03
TYPE_INT_BOOLEAN = 0x12
NO_INDEX = 0xFFFFFFFF
TARGETS = {
    "leakcanary.internal.activity.LeakActivity",
    "androidx.compose.ui.tooling.PreviewActivity",
    "leakcanary.internal.activity.LeakLauncherActivity",
    "androidx.activity.ComponentActivity",
}


def u16(buf, pos):
    return struct.unpack_from("<H", buf, pos)[0]


def u32(buf, pos):
    return struct.unpack_from("<I", buf, pos)[0]


def utf8_len(buf, pos):
    n = buf[pos]
    if n & 0x80:
        return ((n & 0x7F) << 8) | buf[pos + 1], pos + 2
    return n, pos + 1


def utf16_len(buf, pos):
    n = u16(buf, pos)
    if n & 0x8000:
        return ((n & 0x7FFF) << 16) | u16(buf, pos + 2), pos + 4
    return n, pos + 2


def read_strings(buf, pos, size):
    count = u32(buf, pos + 8)
    flags = u32(buf, pos + 16)
    strings_start = u32(buf, pos + 20)
    header_size = u16(buf, pos + 2)
    if count > 100_000 or strings_start >= size or header_size < 28:
        raise ValueError("invalid string pool")
    out = []
    for i in range(count):
        offset = u32(buf, pos + header_size + i * 4)
        p = pos + strings_start + offset
        if flags & 0x100:
            _, p = utf8_len(buf, p)
            length, p = utf8_len(buf, p)
            out.append(buf[p:p + length].decode("utf-8"))
        else:
            length, p = utf16_len(buf, p)
            out.append(buf[p:p + length * 2].decode("utf-16le"))
    return out


def activities_from_apk(path):
    with zipfile.ZipFile(path) as apk:
        buf = apk.read("AndroidManifest.xml")
    if len(buf) < 8 or u16(buf, 0) != XML or u32(buf, 4) != len(buf):
        raise ValueError("invalid binary Android manifest")
    strings = []
    components = {}
    pos = u16(buf, 2)
    while pos < len(buf):
        if pos + 8 > len(buf):
            raise ValueError("truncated chunk header")
        typ, header_size, size = struct.unpack_from("<HHI", buf, pos)
        if size < header_size or header_size < 8 or pos + size > len(buf):
            raise ValueError("invalid chunk length")
        if typ == STRING_POOL:
            strings = read_strings(buf, pos, size)
        elif typ == START_ELEMENT:
            element_index = u32(buf, pos + 20)
            if element_index == NO_INDEX or element_index >= len(strings):
                raise ValueError("invalid XML element index")
            if strings[element_index] in ("activity", "activity-alias"):
                attr_start, attr_size, attr_count = struct.unpack_from("<HHH", buf, pos + 24)
                if attr_size < 20 or attr_count > 1000:
                    raise ValueError("invalid XML attributes")
                attrs = {}
                for i in range(attr_count):
                    a = pos + 16 + attr_start + i * attr_size
                    if a + 20 > pos + size:
                        raise ValueError("truncated XML attribute")
                    name_index, raw = u32(buf, a + 4), u32(buf, a + 8)
                    if name_index >= len(strings):
                        raise ValueError("invalid XML attribute index")
                    value_type = buf[a + 15]
                    value_data = u32(buf, a + 16)
                    if raw != NO_INDEX:
                        value = strings[raw]
                    elif value_type == TYPE_STRING:
                        value = strings[value_data]
                    elif value_type == TYPE_INT_BOOLEAN:
                        value = value_data != 0
                    else:
                        value = (value_type, value_data)
                    attrs[strings[name_index]] = value
                if "name" in attrs:
                    components[attrs["name"]] = attrs.get("exported")
        pos += size
    return components


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", help="Built ARM64 debug APK")
    args = parser.parse_args()
    try:
        activities = activities_from_apk(args.apk)
        found = {name: activities.get(name, "MISSING") for name in sorted(TARGETS)}
        for name, exported in found.items():
            print(f"{name}: exported={exported}")
        bad = [name for name, exported in found.items() if exported is not False]
        if bad:
            print("FAIL: debug diagnostic activities are exported or missing", file=sys.stderr)
            return 1
        print("PASS: debug diagnostic activities are not exported")
        return 0
    except (OSError, ValueError, zipfile.BadZipFile, struct.error, IndexError, UnicodeDecodeError) as exc:
        print(f"FAIL: cannot inspect APK manifest: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

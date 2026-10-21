#!/usr/bin/env python3
"""Check Muse pt-BR resources without Android SDK or third-party packages.

Run from repository root: python3 ci/script/check_ptbr_resources.py
This is a source-level check, not a substitute for Android resource compilation.
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "app/src/main/res"
ANDROID_NAME = "{http://schemas.android.com/apk/res/android}name"
FORMAT = re.compile(r"%(?:\d+\$)?[-#+ 0,(]*\d*(?:\.\d+)?[a-zA-Z%]")


def strings(path: Path) -> dict[str, str]:
    tree = ET.parse(path)
    items = [node for node in tree.getroot() if node.tag == "string"]
    keys = [node.get("name") for node in items]
    duplicates = sorted(key for key, count in Counter(keys).items() if count > 1)
    if duplicates:
        raise ValueError(f"{path}: duplicate string keys: {duplicates}")
    return {node.get("name"): "".join(node.itertext()) for node in items}


def placeholders(value: str) -> Counter[str]:
    # Ignore escaped percent signs; preserve format indices and conversion types.
    return Counter(token for token in FORMAT.findall(value) if token != "%%")


def main() -> int:
    en = strings(RES / "values-en/strings.xml")
    pt = strings(RES / "values-pt-rBR/strings.xml")
    locales = ET.parse(RES / "xml/locales_config.xml").getroot()
    tags = [element.get(ANDROID_NAME) for element in locales]
    problems = []
    if "pt-BR" not in tags:
        problems.append("Android locale config must declare pt-BR (BCP 47)")
    if len(tags) != len(set(tags)):
        problems.append("Duplicate locale declarations")
    missing = sorted(en.keys() - pt.keys())
    if missing:
        problems.append(f"{len(missing)} missing pt-BR keys relative to English: {missing}")
    for key in sorted(en.keys() & pt.keys()):
        if placeholders(en[key]) != placeholders(pt[key]):
            problems.append(
                f"Format mismatch for {key}: EN={dict(placeholders(en[key]))} "
                f"PT={dict(placeholders(pt[key]))}"
            )
    print(f"English strings: {len(en)} | pt-BR strings: {len(pt)}")
    print(f"Locale declaration: {tags}")
    if problems:
        for problem in problems:
            print("FAIL:", problem, file=sys.stderr)
        return 1
    print("PASS: XML parse, locale declaration, keys, duplicates, and format placeholders")
    print("NOTE: Run Android build and inspect other strings*.xml files before shipping.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

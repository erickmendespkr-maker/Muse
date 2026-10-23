#!/usr/bin/env python3
"""Audit all Muse pt-BR Android string resources (Python standard library only).

Run: python3 ci/script/check_ptbr_resources.py
No Gradle, Android SDK, network access or credentials required.
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


def placeholders(value: str) -> Counter[str]:
    return Counter(token for token in FORMAT.findall(value) if token != "%%")


def read_strings(folder: Path) -> tuple[dict[str, str], list[str]]:
    all_strings: dict[str, str] = {}
    errors: list[str] = []
    # Automation labels live in automation*.xml, outside strings*.xml.
    # Include both families so missing pt-BR strings cannot silently pass CI.
    paths = sorted(set(folder.glob("strings*.xml")) | set(folder.glob("automation*.xml")))
    if not paths:
        return {}, [f"No strings*.xml or automation*.xml files in {folder}"]
    for path in paths:
        try:
            tree = ET.parse(path)
        except ET.ParseError as exc:
            errors.append(f"Invalid XML in {path}: {exc}")
            continue
        for node in tree.getroot():
            if node.tag != "string":
                continue
            key = node.get("name")
            if not key:
                errors.append(f"Unnamed string in {path}")
                continue
            if key in all_strings:
                errors.append(f"Duplicate key {key} in {path}")
            all_strings[key] = "".join(node.itertext())
    return all_strings, errors


def main() -> int:
    base, base_errors = read_strings(RES / "values")
    en, en_errors = read_strings(RES / "values-en")
    pt, pt_errors = read_strings(RES / "values-pt-rBR")
    problems = base_errors + en_errors + pt_errors
    try:
        locales = ET.parse(RES / "xml/locales_config.xml").getroot()
        tags = [node.get(ANDROID_NAME) for node in locales]
    except (ET.ParseError, OSError) as exc:
        tags = []
        problems.append(f"Invalid locale config: {exc}")
    if "pt-BR" not in tags:
        problems.append("Missing BCP-47 pt-BR declaration in locales_config.xml")
    if len(tags) != len(set(tags)):
        problems.append("Duplicate locale declarations")

    # English is the translation baseline for pt-BR; default resources also
    # contain strings that may be missing from English. Report both sets.
    for label, baseline in (("English", en), ("default", base)):
        missing = sorted(baseline.keys() - pt.keys())
        if missing:
            problems.append(f"pt-BR missing {len(missing)} {label} keys: {', '.join(missing)}")
    for key in sorted((set(en) | set(base)) & set(pt)):
        source = en.get(key, base.get(key, ""))
        if placeholders(source) != placeholders(pt[key]):
            problems.append(
                f"Format mismatch for {key}: source={dict(placeholders(source))} "
                f"pt-BR={dict(placeholders(pt[key]))}"
            )

    print(f"Resource strings: default={len(base)}, English={len(en)}, pt-BR={len(pt)}")
    print(f"Declared locales: {', '.join(tag for tag in tags if tag)}")
    if problems:
        for problem in problems:
            print("FAIL:", problem, file=sys.stderr)
        return 1
    print("PASS: XML, locale tags, all strings*.xml keys, duplicates, and placeholders")
    print("NOTE: This does not replace Gradle resource compilation or on-device UI testing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

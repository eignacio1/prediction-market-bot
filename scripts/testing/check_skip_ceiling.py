#!/usr/bin/env python3
"""
GG-179/T-464 — loud-skip guard for CI.

A bare `pytest tests/ -q` reports a skip count in its summary line, but
nothing gates on it: "0 failed" is green regardless of how many tests
silently never ran. That was the entire defect GG-179 documents (22 of 28
skips were CI-environment artifacts, not legitimate skips, and nothing
noticed for months).

This script parses a JUnit XML report pytest produces and fails the build
if the skip count exceeds the stated ceiling, or prints every skipped
test's name+reason so a new skip is visible in the CI log rather than
buried in a summary line. It does NOT fail merely because skips increased
below the ceiling isn't breached — see --ceiling.

Usage:
    pytest tests/ -q -rs --junit-xml=pytest-results.xml
    python3 scripts/testing/check_skip_ceiling.py pytest-results.xml --ceiling 18
"""
import argparse
import sys
import xml.etree.ElementTree as ET


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("junit_xml_path")
    parser.add_argument(
        "--ceiling",
        type=int,
        required=True,
        help="Max acceptable skip count. CI fails if the real count exceeds this.",
    )
    args = parser.parse_args()

    tree = ET.parse(args.junit_xml_path)
    root = tree.getroot()
    suites = [root] if root.tag == "testsuite" else root.findall("testsuite")

    skipped_cases = []
    for suite in suites:
        for case in suite.findall("testcase"):
            skip_el = case.find("skipped")
            if skip_el is not None:
                classname = case.get("classname", "")
                name = case.get("name", "")
                reason = skip_el.get("message", "") or (skip_el.text or "").strip()
                skipped_cases.append(f"{classname}::{name} — {reason}")

    count = len(skipped_cases)
    print(f"[check_skip_ceiling] {count} skipped test(s) (ceiling={args.ceiling}):")
    for line in skipped_cases:
        print(f"  SKIP: {line}")

    if count > args.ceiling:
        print(
            f"\n[check_skip_ceiling] FAIL: {count} skips exceeds ceiling of "
            f"{args.ceiling}. A test that used to run is now silently skipping "
            f"in CI — investigate the skip reasons printed above (GG-179)."
        )
        return 1

    print(f"\n[check_skip_ceiling] OK: {count} <= ceiling {args.ceiling}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

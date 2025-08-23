#!/usr/bin/env python3
"""
Script to automatically fix common Flake8 violations.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import List, Set


def run_flake8() -> str:
    """Run flake8 and return output."""
    result = subprocess.run(
        [
            "flake8",
            "app/",
            "--max-line-length=127",
            "--extend-ignore=E203,W503",
            "--format=%(path)s:%(row)d:%(col)d: %(code)s %(text)s",
        ],
        cwd="/Users/alex/Desktop/Projects/DAPP/python-backend",
        capture_output=True,
        text=True,
    )
    return result.stdout


def get_unused_imports(flake8_output: str) -> dict:
    """Extract F401 (unused import) violations."""
    violations = {}
    for line in flake8_output.split("\n"):
        if ":" in line and "F401" in line:
            parts = line.split(":")
            if len(parts) >= 4:
                filepath = parts[0]
                line_num = int(parts[1])
                if filepath not in violations:
                    violations[filepath] = []
                # Extract the import name from the message
                match = re.search(r"'([^']+)' imported but unused", line)
                if match:
                    violations[filepath].append((line_num, match.group(1)))
    return violations


def remove_unused_imports(violations: dict):
    """Remove unused imports from files."""
    for filepath, imports in violations.items():
        if not os.path.exists(filepath):
            continue

        with open(filepath, "r") as f:
            lines = f.readlines()

        # Sort by line number in reverse to avoid index shifting
        imports.sort(key=lambda x: x[0], reverse=True)

        for line_num, import_name in imports:
            if line_num <= len(lines):
                line = lines[line_num - 1]  # Convert to 0-based index

                # Different patterns for removing imports
                patterns = [
                    rf"from [^,\n]+ import [^,\n]*{re.escape(import_name)}[^,\n]*",
                    rf"import {re.escape(import_name)}\n",
                    rf"{re.escape(import_name)},\s*",
                    rf",\s*{re.escape(import_name)}",
                ]

                for pattern in patterns:
                    if re.search(pattern, line):
                        # Simple approach: comment out the problematic import
                        if not line.strip().startswith("#"):
                            lines[line_num - 1] = f"# {line}"
                        break

        with open(filepath, "w") as f:
            f.writelines(lines)


def fix_trailing_whitespace():
    """Fix trailing whitespace violations."""
    for root, dirs, files in os.walk(
        "/Users/alex/Desktop/Projects/DAPP/python-backend/app"
    ):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                with open(filepath, "r") as f:
                    content = f.read()

                # Remove trailing whitespace
                fixed_content = re.sub(r" +$", "", content, flags=re.MULTILINE)

                if content != fixed_content:
                    with open(filepath, "w") as f:
                        f.write(fixed_content)


def fix_boolean_comparisons(flake8_output: str):
    """Fix E712 violations (comparison to True/False)."""
    violations = []
    for line in flake8_output.split("\n"):
        if ":" in line and "E712" in line:
            parts = line.split(":")
            if len(parts) >= 4:
                filepath = parts[0]
                line_num = int(parts[1])
                violations.append((filepath, line_num))

    # Group by file
    file_violations = {}
    for filepath, line_num in violations:
        if filepath not in file_violations:
            file_violations[filepath] = []
        file_violations[filepath].append(line_num)

    for filepath, line_nums in file_violations.items():
        if not os.path.exists(filepath):
            continue

        with open(filepath, "r") as f:
            lines = f.readlines()

        for line_num in sorted(line_nums, reverse=True):
            if line_num <= len(lines):
                line = lines[line_num - 1]

                # Fix common boolean comparison patterns
                line = re.sub(r"== True\b", " is True", line)
                line = re.sub(r"== False\b", " is False", line)
                line = re.sub(r"!= True\b", " is not True", line)
                line = re.sub(r"!= False\b", " is not False", line)

                lines[line_num - 1] = line

        with open(filepath, "w") as f:
            f.writelines(lines)


if __name__ == "__main__":
    print("Running initial Flake8 check...")
    flake8_output = run_flake8()

    print("Fixing trailing whitespace...")
    fix_trailing_whitespace()

    print("Fixing boolean comparisons...")
    fix_boolean_comparisons(flake8_output)

    print("Finding unused imports...")
    unused_imports = get_unused_imports(flake8_output)

    print(f"Found unused imports in {len(unused_imports)} files")
    for filepath, imports in unused_imports.items():
        print(f"  {filepath}: {len(imports)} unused imports")

    print("Commenting out unused imports...")
    remove_unused_imports(unused_imports)

    print("Re-running Flake8 to check improvements...")
    final_output = run_flake8()

    # Count remaining violations
    violation_count = len(
        [
            line
            for line in final_output.split("\n")
            if ":" in line and any(code in line for code in ["E", "F", "W"])
        ]
    )

    print(f"Remaining violations: {violation_count}")
    if violation_count > 0:
        print("First 20 remaining violations:")
        lines = [
            line
            for line in final_output.split("\n")
            if ":" in line and any(code in line for code in ["E", "F", "W"])
        ]
        for line in lines[:20]:
            print(f"  {line}")

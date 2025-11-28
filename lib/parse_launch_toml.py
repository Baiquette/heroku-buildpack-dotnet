#!/usr/bin/env python3
"""
Parse CNB launch.toml files for buildpack scripts.

Supports two output formats:
- --yaml: YAML for bin/release
- --process <type>: Command for a single process type (e.g., as used in `bin/test`)

No external dependencies required - compatible with Python 3.7+
"""

import sys
import shlex
import re
from pathlib import Path


def parse_processes(toml_path):
    """Parse launch.toml and return process type -> command mapping.

    Uses simple regex parsing to avoid dependency on tomli/tomllib.
    This is sufficient for the specific structure of launch.toml files.
    """
    try:
        with open(toml_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (FileNotFoundError, IOError):
        return {}

    processes = {}

    # Find all [[processes]] blocks
    # Pattern matches: [[processes]] followed by type and command fields
    process_blocks = re.split(r'\[\[processes\]\]', content)[1:]

    for block in process_blocks:
        # Extract type field: type = "web" or type = 'web'
        type_match = re.search(r'type\s*=\s*["\']([^"\']+)["\']', block)
        if not type_match:
            continue

        proc_type = type_match.group(1)

        # Extract command array: command = ["bash", "-c", "dotnet MyApp.dll"]
        command_match = re.search(r'command\s*=\s*\[(.*?)\]', block, re.DOTALL)
        if not command_match:
            continue

        # Parse command array elements
        command_str = command_match.group(1)
        # Find all quoted strings in the array
        command_parts = re.findall(r'["\']([^"\']*)["\']', command_str)

        if not command_parts:
            continue

        # Extract script content from bash -c commands, otherwise join with escaping
        if len(command_parts) >= 3 and command_parts[:2] == ["bash", "-c"]:
            processes[proc_type] = command_parts[2]
        else:
            processes[proc_type] = shlex.join(command_parts)

    return processes


def main():
    if len(sys.argv) not in [3, 4]:
        print(
            "Usage: parse_launch_toml.py <launch.toml> [--yaml|--process <type>]",
            file=sys.stderr,
        )
        sys.exit(1)

    toml_path, mode = sys.argv[1], sys.argv[2]

    if not Path(toml_path).exists():
        sys.exit(1)

    processes = parse_processes(toml_path)

    if mode == "--yaml":
        if processes:
            print("---\ndefault_process_types:")
            for proc_type, command in processes.items():
                print(f"  {proc_type}: {command}")

    elif mode == "--process" and len(sys.argv) == 4:
        command = processes.get(sys.argv[3])
        if command:
            print(command)
        else:
            sys.exit(1)

    else:
        print(
            "Usage: parse_launch_toml.py <launch.toml> [--yaml|--process <type>]",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()

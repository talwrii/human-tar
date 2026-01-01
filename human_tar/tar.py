#!/usr/bin/env python3
"""Pack git-tracked files into human-tar format."""
import argparse
import os
import subprocess
import sys


def main():
    """Output git-tracked files in human-tar format (grep . style)."""
    parser = argparse.ArgumentParser(description="Pack git-tracked files into human-tar format")
    parser.add_argument("--bytes", action="store_true", help="Show byte count per file instead of content")
    args = parser.parse_args()

    try:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True,
            text=True,
            check=True
        )
        files = [f for f in result.stdout.strip().split("\n") if f]

        if not files:
            print("No git-tracked files found.", file=sys.stderr)
            sys.exit(1)

        if args.bytes:
            for f in files:
                try:
                    size = os.path.getsize(f)
                    print(f"{f}:{size}")
                except OSError:
                    print(f"{f}:0")
            return

        proc = subprocess.run(
            ["grep", ".", "--"] + files,
            capture_output=True,
            text=True
        )

        print(proc.stdout, end="")

        if proc.stderr:
            print(proc.stderr, file=sys.stderr, end="")

    except subprocess.CalledProcessError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: Required command not found: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
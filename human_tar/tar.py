#!/usr/bin/env python3
"""Pack git-tracked files into human-tar format."""
import argparse
import fnmatch
import os
import subprocess
import sys

EXCLUDE_FILE = ".human-tar-exclude"


def load_excludes():
    """Load exclusion patterns from .human-tar-exclude."""
    if not os.path.exists(EXCLUDE_FILE):
        return []
    with open(EXCLUDE_FILE, "r") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def save_exclude(pattern):
    """Add a pattern to .human-tar-exclude."""
    excludes = load_excludes()
    if pattern not in excludes:
        with open(EXCLUDE_FILE, "a") as f:
            f.write(pattern + "\n")
        print(f"Added: {pattern}", file=sys.stderr)
    else:
        print(f"Already excluded: {pattern}", file=sys.stderr)


def is_excluded(filepath, excludes):
    """Check if a filepath matches any exclusion pattern."""
    for pattern in excludes:
        if fnmatch.fnmatch(filepath, pattern) or filepath == pattern:
            return True
    return False


def get_files():
    """Get git-tracked files, filtered by excludes."""
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

    excludes = load_excludes()
    filtered = []
    for f in files:
        if is_excluded(f, excludes):
            print(f"HUMAN-TAR:excluding {f}", file=sys.stderr)
        else:
            filtered.append(f)

    return filtered


def main():
    """Output git-tracked files in human-tar format (grep . style)."""
    parser = argparse.ArgumentParser(description="Pack git-tracked files into human-tar format")
    parser.add_argument("command", nargs="?", help="Subcommand: bytes, exclude")
    parser.add_argument("pattern", nargs="?", help="Pattern to exclude")
    args = parser.parse_args()

    if args.command == "exclude":
        if not args.pattern:
            print("Usage: human-tar exclude <pattern>", file=sys.stderr)
            sys.exit(1)
        save_exclude(args.pattern)
        return

    try:
        filtered_files = get_files()

        if not filtered_files:
            print("All files excluded.", file=sys.stderr)
            sys.exit(0)

        if args.command == "bytes":
            sizes = []
            for f in filtered_files:
                try:
                    size = os.path.getsize(f)
                except OSError:
                    size = 0
                sizes.append((f, size))
            
            sizes.sort(key=lambda x: x[1])
            total = sum(s for _, s in sizes)
            
            cumulative = 0
            for f, size in sizes:
                cumulative += size
                pct = (size / total * 100) if total > 0 else 0
                cum_pct = (cumulative / total * 100) if total > 0 else 0
                print(f"{f}:{size}:{pct:.1f}%:{cum_pct:.1f}%")
            print(f"TOTAL:{total}:100%:100%")
            return

        if args.command is not None:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            sys.exit(1)

        proc = subprocess.run(
            ["grep", ".", "--"] + filtered_files,
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
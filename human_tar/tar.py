#!/usr/bin/env python3
"""Pack git-tracked files into human-tar format."""

import argparse
import fnmatch
import os
import subprocess
import sys

EXCLUDE_FILE = ".human-tar-exclude"
DITTO = ""


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
        # Exact match
        if filepath == pattern:
            return True
        # Directory prefix match (e.g., "tests" excludes "tests/foo.py")
        if filepath.startswith(pattern + "/") or filepath.startswith(pattern + os.sep):
            return True
        # Glob pattern match
        if fnmatch.fnmatch(filepath, pattern):
            return True
    return False


def get_changed_files():
    """Get files that are modified or staged."""
    # Get both staged and unstaged changes compared to HEAD
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        capture_output=True,
        text=True,
        check=True
    )
    files = [f for f in result.stdout.strip().split("\n") if f]
    
    # Also get untracked files that are staged (new files)
    staged_result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        check=True
    )
    staged_files = [f for f in staged_result.stdout.strip().split("\n") if f]
    
    # Combine and deduplicate
    all_files = list(set(files + staged_files))
    return all_files


def get_files(changed_only=False):
    """Get git-tracked files, filtered by excludes."""
    if changed_only:
        files = get_changed_files()
        if not files:
            print("No changed files.", file=sys.stderr)
            sys.exit(0)
    else:
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


def is_empty_file(filepath):
    """Check if a file is empty."""
    try:
        return os.path.getsize(filepath) == 0
    except OSError:
        return False


def compress_output(text):
    """Replace repeated filenames with ditto mark."""
    lines = text.split("\n")
    result = []
    last_filename = None
    
    for line in lines:
        if not line:
            result.append(line)
            continue
        
        # Skip HUMAN-TAR: lines
        if line.startswith("HUMAN-TAR:"):
            result.append(line)
            continue
        
        if ":" in line:
            filename, content = line.split(":", 1)
            if filename == last_filename:
                result.append(f"{DITTO}:{content}")
            else:
                result.append(line)
                last_filename = filename
        else:
            result.append(line)
    
    return "\n".join(result)


def output_manifest(files):
    """Output the manifest block."""
    print("HUMAN-TAR:manifest")
    for f in sorted(files):
        if not os.path.exists(f):
            print(f"HUMAN-TAR:manifest:{f} (deleted)")
        elif is_empty_file(f):
            print(f"HUMAN-TAR:manifest:{f} (empty)")
        else:
            print(f"HUMAN-TAR:manifest:{f}")
    print("HUMAN-TAR:end-manifest")


def main():
    """Output git-tracked files in human-tar format (grep . style)."""
    parser = argparse.ArgumentParser(description="Pack git-tracked files into human-tar format")
    parser.add_argument("command", nargs="?", help="Subcommand: bytes [filter], exclude <pattern>")
    parser.add_argument("pattern", nargs="?", help="Pattern for exclude, or filter for bytes")
    parser.add_argument("-c", "--compress", action="store_true",
                        help="Compress output by omitting repeated filenames")
    parser.add_argument("-d", "--depth", type=int, default=None,
                        help="For bytes: aggregate by directory depth")
    parser.add_argument("-m", "--changed", action="store_true",
                        help="Only include modified and staged files")
    args = parser.parse_args()

    if args.command == "exclude":
        if not args.pattern:
            print("Usage: human-tar exclude <pattern>", file=sys.stderr)
            sys.exit(1)
        save_exclude(args.pattern)
        return

    try:
        filtered_files = get_files(changed_only=args.changed)
        if not filtered_files:
            print("All files excluded.", file=sys.stderr)
            sys.exit(0)

        if args.command == "bytes":
            # Calculate total size of all files first
            all_sizes = []
            for f in filtered_files:
                try:
                    size = os.path.getsize(f)
                except OSError:
                    size = 0
                all_sizes.append((f, size))
            
            grand_total = sum(s for _, s in all_sizes)
            
            # Filter by pattern if provided
            if args.pattern:
                filter_pattern = args.pattern
                sizes = [(f, s) for f, s in all_sizes 
                         if f.startswith(filter_pattern) or fnmatch.fnmatch(f, filter_pattern)]
                if not sizes:
                    print(f"No files matching '{filter_pattern}'", file=sys.stderr)
                    sys.exit(1)
            else:
                sizes = all_sizes
            
            # Aggregate by depth if specified
            if args.depth is not None:
                from collections import defaultdict
                aggregated = defaultdict(int)
                for f, s in sizes:
                    parts = f.split("/")
                    if len(parts) <= args.depth:
                        key = f  # File is shallower than depth, use full path
                    else:
                        key = "/".join(parts[:args.depth]) + "/"
                    aggregated[key] += s
                sizes = list(aggregated.items())
            
            sizes.sort(key=lambda x: x[1])
            filtered_total = sum(s for _, s in sizes)
            
            cumulative = 0
            for f, size in sizes:
                cumulative += size
                pct = (size / filtered_total * 100) if filtered_total > 0 else 0
                cum_pct = (cumulative / filtered_total * 100) if filtered_total > 0 else 0
                print(f"{f}:{size}:{pct:.1f}%:{cum_pct:.1f}%")
            
            # Show filtered total with percentage of grand total
            if args.pattern:
                grand_pct = (filtered_total / grand_total * 100) if grand_total > 0 else 0
                print(f"FILTERED:{filtered_total}:100%:{grand_pct:.1f}% of {grand_total}")
            else:
                print(f"TOTAL:{filtered_total}:100%:100%")
            return

        if args.command is not None:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            sys.exit(1)

        # Separate empty and non-empty files
        empty_files = []
        non_empty_files = []
        for f in filtered_files:
            if not os.path.exists(f):
                continue  # Skip deleted files
            if is_empty_file(f):
                empty_files.append(f)
            else:
                non_empty_files.append(f)

        # Output manifest
        output_manifest(filtered_files)

        # Output compressed header if needed
        if args.compress:
            print("HUMAN-TAR:compressed - lines starting with : continue the previous filename")

        # Output non-empty files using grep
        if non_empty_files:
            proc = subprocess.run(
                ["grep", ".", "--"] + non_empty_files,
                capture_output=True,
                text=True
            )
            
            output = proc.stdout
            if args.compress:
                output = compress_output(output)
            
            print(output, end="")
            if proc.stderr:
                print(proc.stderr, file=sys.stderr, end="")

        # Output empty file markers
        for f in sorted(empty_files):
            print(f"HUMAN-TAR:empty:{f}")

    except subprocess.CalledProcessError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: Required command not found: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
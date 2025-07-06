#!/usr/bin/env python3
import os
import sys
import argparse

def parse_grep_line(line):
    """Parse a grep line into filename and content."""
    try:
        # Split on the first ':' only
        filename, content = line.split(":", 1)
        return filename.strip(), content.strip()
    except ValueError:
        print(f"Warning: Skipping malformed line: {line.strip()}", file=sys.stderr)
        return None, None

def get_filenames_and_lines(input_source, output_dir):
    """Collect all unique filenames and store lines from the input."""
    filenames = set()
    lines = []
    for line in input_source:
        lines.append(line)
        filename, _ = parse_grep_line(line)
        if filename:
            full_path = os.path.join(output_dir, filename)
            filenames.add(full_path)
    return filenames, lines

def check_files_exist(filenames):
    """Check if any files in the set exist, return the first conflict or None."""
    for filename in filenames:
        if os.path.exists(filename):
            return filename
    return None

def write_to_file(filename, content, output_dir):
    """Write content to the specified file, creating directories as needed."""
    full_path = os.path.join(output_dir, filename)
    os.makedirs(os.path.dirname(full_path) or ".", exist_ok=True)
    try:
        with open(full_path, "a", encoding="utf-8") as f:
            f.write(content + "\n")
    except OSError as e:
        print(f"Error writing to {full_path}: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Unpack grep . -r output into original file structure."
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        type=str,
        default="-",
        help="Input file containing grep output (default: stdin)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=".",
        help="Output directory for unpacked files (default: current directory)",
    )
    args = parser.parse_args()

    # Set input source
    input_source = sys.stdin if args.input_file == "-" else open(args.input_file, "r", encoding="utf-8")

    # Collect filenames and store lines in memory
    with input_source:
        filenames, lines = get_filenames_and_lines(input_source, args.output_dir)

    # Check if any files exist
    conflicting_file = check_files_exist(filenames)
    if conflicting_file:
        print(f"Error: File {conflicting_file} already exists in output directory.", file=sys.stderr)
        sys.exit(1)

    # Process stored lines and write files
    for line in lines:
        filename, content = parse_grep_line(line)
        if filename and content:
            write_to_file(filename, content, args.output_dir)

if __name__ == "__main__":
    main()

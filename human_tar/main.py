#!/usr/bin/env python3

import os
import sys
import argparse

DITTO = ""


def parse_grep_line(line, last_filename=None):
    """Parse a grep line into filename and content, handling ditto marks."""
    try:
        # Split on the first ':' only
        filename, content = line.split(":", 1)
        filename = filename.strip()
        
        # Handle ditto mark - use previous filename
        if filename == DITTO:
            if last_filename is None:
                print(f"Warning: Empty filename with no previous filename: {line.strip()}", file=sys.stderr)
                return None, None, None
            filename = last_filename
        
        return filename, content, filename  # Return current filename as new "last"
    except ValueError:
        print(f"Warning: Skipping malformed line: {line.strip()}", file=sys.stderr)
        return None, None, last_filename


def get_filenames_and_lines(input_source, output_dir):
    """Collect all unique filenames and store lines from the input."""
    filenames = set()
    lines = []
    empty_files = []
    last_filename = None
    in_manifest = False
    
    for line in input_source:
        line = line.rstrip('\n\r')
        
        # Handle manifest block
        if line == "HUMAN-TAR:manifest":
            in_manifest = True
            continue
        if line == "HUMAN-TAR:end-manifest":
            in_manifest = False
            continue
        if in_manifest:
            # Skip manifest lines (we'll get files from actual content)
            continue
        
        # Skip metadata lines
        if line.startswith("HUMAN-TAR:compressed"):
            continue
        if line.startswith("HUMAN-TAR:excluding"):
            continue
        
        # Handle empty file markers
        if line.startswith("HUMAN-TAR:empty:"):
            empty_file = line[len("HUMAN-TAR:empty:"):]
            empty_files.append(empty_file)
            full_path = os.path.join(output_dir, empty_file)
            filenames.add(full_path)
            continue
        
        # Skip other HUMAN-TAR metadata
        if line.startswith("HUMAN-TAR:"):
            continue
        
        # Skip empty lines
        if not line:
            continue
        
        lines.append(line)
        filename, _, last_filename = parse_grep_line(line, last_filename)
        if filename:
            full_path = os.path.join(output_dir, filename)
            filenames.add(full_path)
    
    return filenames, lines, empty_files


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


def create_empty_file(filename, output_dir):
    """Create an empty file, creating directories as needed."""
    full_path = os.path.join(output_dir, filename)
    os.makedirs(os.path.dirname(full_path) or ".", exist_ok=True)
    try:
        with open(full_path, "w", encoding="utf-8") as f:
            pass  # Create empty file
    except OSError as e:
        print(f"Error creating empty file {full_path}: {e}", file=sys.stderr)
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
        filenames, lines, empty_files = get_filenames_and_lines(input_source, args.output_dir)

    # Check if any files exist
    conflicting_file = check_files_exist(filenames)
    if conflicting_file:
        print(f"Error: File {conflicting_file} already exists in output directory.", file=sys.stderr)
        sys.exit(1)

    # Process stored lines and write files
    last_filename = None
    for line in lines:
        filename, content, last_filename = parse_grep_line(line, last_filename)
        if filename and content is not None:
            write_to_file(filename, content, args.output_dir)

    # Create empty files
    for empty_file in empty_files:
        create_empty_file(empty_file, args.output_dir)


if __name__ == "__main__":
    main()
# human-tar
**@readwithai** - [X](https://x.com/readwithai) - [blog](https://readwithai.substack.com/) - [machine-aided reading](https://www.reddit.com/r/machineAidedReading/) - [📖](https://readwithai.substack.com/p/what-is-reading-broadly-defined
)[⚡️](https://readwithai.substack.com/s/technical-miscellany)[🖋️](https://readwithai.substack.com/p/note-taking-with-obsidian-much-of)

A human-readable tar format for text files. Easy for AIs to write and read.

## Motivation
I've been doing a little vibe-coding with online LLMs and found myself occasionally producing a number of files to share. While some online LLMs can produce tar files, this process is often buggy and slow compared to producing output like this (using prompts)

## Alternatives and prior Work
This format is based on the output of `grep . -r .` - which can be used to produce output to give to an LLM (with the appropriate ignore flags)

You could use cursor/windsurf or another AI tool to circumvent the need for this sort of tool. There are various tools to wrap up a codebase ready to be sent into an AI, but not necessarily the other way.

## Installation
Install `human-tar` from PyPI using [pipx](https://github.com/pypa/pipx)

```bash
pipx install human-tar
```

## Usage
`human-tar` will give you the output for the current *git repo* in this format.
`human-tar bytes` tells you how many bytes each file is taking up.
`human-tar exclude '*.json'` excludes all json iles
`human-tar exclude files` excludes a files.


`human-untar` unpacks the output in the form of `grep . -r` into the original file structure. It reads input from a file or stdin and writes files to the current directory by default.

### Examples
As a demonstraction, this command produces human-tar input using grep and feeds this into `human-tar`.

   ```bash
   grep . -r /path/to/dir | human-untar
   ```

You can also provide a path on the current directory or from the clipboard using xclip on linux or pblaste on mac

```bash
human-untar file.txt
human-untar <(xclip -o -selection CLIPBOARD)
```

For testing purposes, you might want to output into a different directory using the -o option

```bash
human-tar file.text -o file
```

### Input Format
The input should be in the format of `grep . -r` output, e.g.:
```
src/main.c:int main() {
src/main.c:    printf("Hello, world!\n");
src/utils/helper.c:void help() {
```
This will create (in the current directory by default):
```
./
├── src/
│   ├── main.c
│   └── utils/
│       └── helper.c
```

### Options
- `-o, --output-dir`: Specify the output directory (default: current directory).
- Example: `human-tar -o my_output_dir grep_output.txt`


## About me
I am **@readwithai**. I create tools for reading, research and agency sometimes using the markdown editor [Obsidian](https://readwithai.substack.com/p/what-exactly-is-obsidian).

I also create a [stream of tools](https://readwithai.substack.com/p/my-productivity-tools) like this that are related to carrying out my work. As users of tool are likely interesting in AI you might like to read my blog about tools for reading with ai.

I write about lots of things - including tools like this - on [X](https://x.com/readwithai).
My [blog](https://readwithai.substack.com/) is more about reading and research and agency.

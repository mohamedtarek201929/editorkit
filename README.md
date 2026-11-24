# editorkit

Small, dependency-free Python tools for video editors who work with SRT caption files.

Built from everyday editing needs: fixing caption timing after a cut, keeping lines readable,
catching captions that are too fast to read, joining parts, and drafting chapter timestamps
for a YouTube description.

Requires Python 3.9+. No third-party packages.

## Commands

    python -m editorkit shift captions.srt -2.5 -o fixed.srt   # move all cues 2.5 s earlier
    python -m editorkit rewrap captions.srt -w 38 -o wrapped.srt
    python -m editorkit check captions.srt                     # overlaps, long lines, characters/second
    python -m editorkit merge part1.srt part2.srt -o full.srt
    python -m editorkit chapters captions.srt                  # draft chapters from pauses

`chapters` output is a draft. Rename the chapters yourself before publishing.

## Tests

    python -m unittest discover -s tests

## Status

Early (0.1.0). Issues and pull requests welcome: ideas include ASS/VTT input, frame-rate aware
shifting, and Arabic/RTL line-wrapping checks.

## License

MIT

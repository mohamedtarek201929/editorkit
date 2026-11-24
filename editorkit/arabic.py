"""Checks and fixes for Arabic captions.

Arabic subtitles often arrive from tools that use Latin punctuation, which shows up on the wrong
side or with the wrong shape in right-to-left text. These helpers find and fix the common cases.
They only touch cues whose text contains Arabic letters.
"""
from __future__ import annotations
import re
from .srt import Cue

_ARABIC = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")
_LATIN_Q = re.compile(r"\?")
_LATIN_COMMA = re.compile(r"(?<=[\u0600-\u06FF]),")
_LATIN_SEMI = re.compile(r"(?<=[\u0600-\u06FF]);")
# A wrapped line that starts with punctuation shows that mark on the wrong edge in RTL text.
_LINE_START_PUNCT = re.compile(r"^[\s]*[،؛؟.!,;:?)\]»]")
_EASTERN = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def is_arabic(text: str) -> bool:
    return bool(_ARABIC.search(text))


def check(cues: list[Cue]) -> list[str]:
    issues = []
    for i, c in enumerate(cues, 1):
        if not is_arabic(c.text):
            continue
        if _LATIN_Q.search(c.text):
            issues.append(f"cue {i}: Latin '?' in Arabic text (use '؟')")
        if _LATIN_COMMA.search(c.text):
            issues.append(f"cue {i}: Latin ',' after Arabic text (use '،')")
        if _LATIN_SEMI.search(c.text):
            issues.append(f"cue {i}: Latin ';' after Arabic text (use '؛')")
        for n, line in enumerate(c.text.split("\n")[1:], 2):
            if _LINE_START_PUNCT.match(line):
                issues.append(f"cue {i}: line {n} starts with punctuation, move it to the previous line")
    return issues


def fix(cues: list[Cue]) -> list[Cue]:
    """Replace Latin punctuation with Arabic punctuation and pull stray leading punctuation up to
    the end of the previous line. Latin-only cues are returned unchanged."""
    out = []
    for c in cues:
        if not is_arabic(c.text):
            out.append(c)
            continue
        t = _LATIN_Q.sub("؟", c.text)
        t = _LATIN_COMMA.sub("،", t)
        t = _LATIN_SEMI.sub("؛", t)
        lines = t.split("\n")
        for n in range(1, len(lines)):
            m = re.match(r"^\s*([،؛؟.!:)\]»]+)\s*", lines[n])
            if m:
                lines[n - 1] = lines[n - 1].rstrip() + m.group(1)
                lines[n] = lines[n][m.end():]
        t = "\n".join(l for l in lines if l.strip() != "")
        out.append(Cue(c.start, c.end, t))
    return out

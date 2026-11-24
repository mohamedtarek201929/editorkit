"""Parse, write and transform SRT subtitle files."""
from __future__ import annotations
import re
import textwrap
from dataclasses import dataclass

_TS = re.compile(r"(\d+):(\d{2}):(\d{2})[,.](\d{1,3})")
_ARROW = re.compile(r"\s*-->\s*")


@dataclass
class Cue:
    start: int  # milliseconds
    end: int
    text: str


def parse_ts(s: str) -> int:
    m = _TS.fullmatch(s.strip())
    if not m:
        raise ValueError(f"bad timestamp: {s!r}")
    h, mi, se, ms = m.groups()
    return ((int(h) * 60 + int(mi)) * 60 + int(se)) * 1000 + int(ms.ljust(3, "0"))


def fmt_ts(ms: int, sep: str = ",") -> str:
    ms = max(0, int(ms))
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def parse(text: str) -> list[Cue]:
    cues: list[Cue] = []
    text = text.replace("\r\n", "\n").lstrip("\ufeff")
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [l for l in block.split("\n")]
        if not lines:
            continue
        idx = next((i for i, l in enumerate(lines) if "-->" in l), None)
        if idx is None:
            continue
        a, b = _ARROW.split(lines[idx].strip(), maxsplit=1)
        b = b.split()[0]
        cues.append(Cue(parse_ts(a), parse_ts(b), "\n".join(lines[idx + 1:]).strip()))
    return cues


def dump(cues: list[Cue]) -> str:
    out = []
    for i, c in enumerate(cues, 1):
        out.append(f"{i}\n{fmt_ts(c.start)} --> {fmt_ts(c.end)}\n{c.text}\n")
    return "\n".join(out)


def shift(cues: list[Cue], offset_ms: int) -> list[Cue]:
    """Move every cue by offset_ms (negative allowed). Cues that end before 0 are dropped."""
    res = []
    for c in cues:
        if c.end + offset_ms <= 0:
            continue
        res.append(Cue(max(0, c.start + offset_ms), c.end + offset_ms, c.text))
    return res


def rewrap(cues: list[Cue], width: int = 42, max_lines: int = 2) -> list[Cue]:
    """Re-wrap text to `width` characters per line. Raises no error if text needs more than max_lines;
    use `check` to find those."""
    res = []
    for c in cues:
        flat = " ".join(c.text.split())
        res.append(Cue(c.start, c.end, "\n".join(textwrap.wrap(flat, width)) or ""))
    return res


def check(cues: list[Cue], width: int = 42, max_lines: int = 2, max_cps: float = 20.0) -> list[str]:
    """Return human-readable problems: overlaps, too many lines, long lines, reading speed."""
    issues = []
    for i, c in enumerate(cues, 1):
        if c.end <= c.start:
            issues.append(f"cue {i}: end is not after start")
        lines = c.text.split("\n")
        if len(lines) > max_lines:
            issues.append(f"cue {i}: {len(lines)} lines (max {max_lines})")
        if any(len(l) > width for l in lines):
            issues.append(f"cue {i}: line longer than {width} characters")
        dur = (c.end - c.start) / 1000
        if dur > 0:
            cps = len(c.text.replace("\n", "")) / dur
            if cps > max_cps:
                issues.append(f"cue {i}: {cps:.1f} characters/second (max {max_cps:g})")
        if i < len(cues) and c.end > cues[i].start:
            issues.append(f"cue {i}: overlaps cue {i + 1}")
    return issues


def merge(a: list[Cue], b: list[Cue], offset_b_ms: int = 0) -> list[Cue]:
    """Append b after a, with b shifted by offset_b_ms plus the end time of a."""
    base = (a[-1].end if a else 0) + offset_b_ms
    return a + shift(b, base)


def chapters(cues: list[Cue], gap_s: float = 4.0, min_len_s: float = 30.0) -> list[tuple[int, str]]:
    """Rough chapter list for a YouTube description: a new chapter starts after a pause of
    gap_s seconds or more, at least min_len_s after the previous chapter. Label is the first
    words spoken. These are drafts for an editor to rename, not finished chapters."""
    out: list[tuple[int, str]] = []
    if not cues:
        return out
    out.append((0, _label(cues[0].text)))
    for prev, cur in zip(cues, cues[1:]):
        if (cur.start - prev.end) / 1000 >= gap_s and (cur.start - out[-1][0]) / 1000 >= min_len_s:
            out.append((cur.start, _label(cur.text)))
    return out


def _label(text: str, words: int = 6) -> str:
    w = " ".join(text.split()).split(" ")
    s = " ".join(w[:words]).strip(" ,.-")
    return s + ("..." if len(w) > words else "")


def fmt_chapter_ts(ms: int) -> str:
    s = ms // 1000
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"

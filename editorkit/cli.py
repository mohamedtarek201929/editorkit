import argparse
import sys
from . import srt, arabic


def _read(p):
    with open(p, encoding="utf-8-sig") as f:
        return srt.parse(f.read())


def _write(cues, p):
    data = srt.dump(cues)
    if p in (None, "-"):
        sys.stdout.write(data)
    else:
        with open(p, "w", encoding="utf-8") as f:
            f.write(data)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="editorkit", description="SRT helpers for video editors")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("shift", help="shift all cues by seconds (can be negative)")
    s.add_argument("input"); s.add_argument("seconds", type=float); s.add_argument("-o", "--output")

    s = sub.add_parser("rewrap", help="re-wrap cue text to a line width")
    s.add_argument("input"); s.add_argument("-w", "--width", type=int, default=42); s.add_argument("-o", "--output")

    s = sub.add_parser("check", help="report overlaps, long lines and fast reading speed")
    s.add_argument("input"); s.add_argument("-w", "--width", type=int, default=42)
    s.add_argument("--max-lines", type=int, default=2); s.add_argument("--max-cps", type=float, default=20.0)

    s = sub.add_parser("arabic", help="check Arabic captions for Latin punctuation and stray line-start marks")
    s.add_argument("input"); s.add_argument("--fix", action="store_true", help="write fixed captions"); s.add_argument("-o", "--output")

    s = sub.add_parser("merge", help="append second file after the first")
    s.add_argument("first"); s.add_argument("second"); s.add_argument("-o", "--output")

    s = sub.add_parser("chapters", help="draft chapter timestamps from pauses")
    s.add_argument("input"); s.add_argument("--gap", type=float, default=4.0); s.add_argument("--min-len", type=float, default=30.0)

    a = ap.parse_args(argv)
    if a.cmd == "shift":
        _write(srt.shift(_read(a.input), round(a.seconds * 1000)), a.output)
    elif a.cmd == "rewrap":
        _write(srt.rewrap(_read(a.input), a.width), a.output)
    elif a.cmd == "check":
        issues = srt.check(_read(a.input), a.width, a.max_lines, a.max_cps)
        print("\n".join(issues) if issues else "no problems found")
        return 1 if issues else 0
    elif a.cmd == "arabic":
        cues = _read(a.input)
        if a.fix:
            _write(arabic.fix(cues), a.output)
        else:
            issues = arabic.check(cues)
            print("\n".join(issues) if issues else "no problems found")
            return 1 if issues else 0
    elif a.cmd == "merge":
        _write(srt.merge(_read(a.first), _read(a.second)), a.output)
    elif a.cmd == "chapters":
        for ms, label in srt.chapters(_read(a.input), a.gap, a.min_len):
            print(f"{srt.fmt_chapter_ts(ms)} {label}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

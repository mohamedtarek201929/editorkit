import unittest
from editorkit import srt

SAMPLE = """1
00:00:01,000 --> 00:00:03,000
Hello there

2
00:00:10,000 --> 00:00:12,500
Second line
here
"""


class T(unittest.TestCase):
    def test_roundtrip(self):
        c = srt.parse(SAMPLE)
        self.assertEqual(len(c), 2)
        self.assertEqual(c[1].text, "Second line\nhere")
        self.assertEqual(srt.parse(srt.dump(c)), c)

    def test_ts(self):
        self.assertEqual(srt.parse_ts("01:02:03,004"), 3723004)
        self.assertEqual(srt.fmt_ts(3723004), "01:02:03,004")
        self.assertEqual(srt.parse_ts("00:00:01.5"), 1500)

    def test_shift(self):
        c = srt.shift(srt.parse(SAMPLE), -2000)
        self.assertEqual(len(c), 2)
        self.assertEqual(c[0].start, 0)
        self.assertEqual(len(srt.shift(srt.parse(SAMPLE), -4000)), 1)

    def test_check(self):
        c = srt.parse(SAMPLE)
        self.assertEqual(srt.check(c), [])
        c[0].end = 11000
        self.assertTrue(any("overlaps" in i for i in srt.check(c)))

    def test_rewrap(self):
        c = srt.rewrap(srt.parse(SAMPLE), 8)
        self.assertEqual(c[1].text, "Second\nline\nhere")

    def test_merge(self):
        a = srt.parse(SAMPLE)
        m = srt.merge(a, a)
        self.assertEqual(len(m), 4)
        self.assertEqual(m[2].start, a[-1].end + a[0].start)

    def test_chapters(self):
        c = srt.parse(SAMPLE)
        ch = srt.chapters(c, gap_s=5, min_len_s=5)
        self.assertEqual([x[0] for x in ch], [0, 10000])
        self.assertEqual(srt.fmt_chapter_ts(3723000), "1:02:03")


class Edge(unittest.TestCase):
    def test_bom_crlf_and_missing_index(self):
        raw = "\ufeff00:00:01,000 --> 00:00:02,000\r\nHi\r\n\r\n2\r\n00:00:03,000 --> 00:00:04,000 X1:0\r\nBye\r\n"
        c = srt.parse(raw)
        self.assertEqual([x.text for x in c], ["Hi", "Bye"])
        self.assertEqual(c[1].end, 4000)

    def test_empty_and_garbage(self):
        self.assertEqual(srt.parse(""), [])
        self.assertEqual(srt.parse("just text\n\nmore"), [])
        with self.assertRaises(ValueError):
            srt.parse_ts("nope")

    def test_arabic_text_kept(self):
        c = srt.parse("1\n00:00:00,000 --> 00:00:02,000\nأهلا بيكم في الفيديو\n")
        self.assertEqual(srt.parse(srt.dump(c))[0].text, "أهلا بيكم في الفيديو")

    def test_chapters_empty(self):
        self.assertEqual(srt.chapters([]), [])


if __name__ == "__main__":
    unittest.main()

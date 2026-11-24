import unittest
from editorkit import arabic, srt

RAW = """1
00:00:01,000 --> 00:00:03,000
هل تعرف الطريق?

2
00:00:04,000 --> 00:00:06,000
أولا, ثم ثانيا
، وبعد ذلك

3
00:00:07,000 --> 00:00:08,000
Is this right?
"""


class T(unittest.TestCase):
    def test_check_finds_problems(self):
        issues = arabic.check(srt.parse(RAW))
        self.assertTrue(any("cue 1" in i and "?" in i for i in issues))
        self.assertTrue(any("cue 2" in i and "','" in i for i in issues))
        self.assertTrue(any("cue 2" in i and "starts with punctuation" in i for i in issues))

    def test_latin_cue_untouched(self):
        issues = arabic.check(srt.parse(RAW))
        self.assertFalse(any("cue 3" in i for i in issues))
        fixed = arabic.fix(srt.parse(RAW))
        self.assertEqual(fixed[2].text, "Is this right?")

    def test_fix(self):
        fixed = arabic.fix(srt.parse(RAW))
        self.assertEqual(fixed[0].text, "هل تعرف الطريق؟")
        self.assertEqual(fixed[1].text, "أولا، ثم ثانيا،\nوبعد ذلك")
        self.assertEqual(arabic.check(fixed), [])

    def test_fix_is_idempotent(self):
        once = arabic.fix(srt.parse(RAW))
        self.assertEqual(arabic.fix(once), once)


if __name__ == "__main__":
    unittest.main()
